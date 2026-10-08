"""Simulated real-time ECG stream into QuestDB — raw parameters only.

The records were sampled at 1000 Hz, so the stream runs at the same rate.
Samples are emitted in packets paced against the wall clock, and each row is
stamped on a FIXED GRID anchored at the run's start time:

    timestamp(k) = t_start + k / rate_hz

These are ASSIGNED timestamps, not observations. delta_t downstream will
therefore return exactly 1/rate_hz with no jitter — at the native rate that is
the true clock of the recording, 1 ms, but it must not be mistaken for a
measurement of the replay.

Records are streamed one after another, in the order of records.txt, each over
the same window of the same lead.

No returns, no entropy, no learning. Raw values only.
"""
import argparse
import logging
import os
import signal
import socket
import time
import traceback

import psycopg2
import psycopg2.pool

from config import QDB_CONFIG, ILP_CONFIG, ECG_CONFIG, LOG_CONFIG

from ecg_chain import ECGChain, read_records

os.makedirs('logs', exist_ok=True)
logging.basicConfig(level=getattr(logging, LOG_CONFIG['level']),
                    format=LOG_CONFIG['format'],
                    filename=LOG_CONFIG['file'], filemode='a')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(LOG_CONFIG['format']))
logging.getLogger('').addHandler(console)

connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **QDB_CONFIG)

TABLE = "ecg_steps"

CREATE_SQL = f"""
CREATE TABLE {TABLE} (
    record_id SYMBOL,
    age_band SYMBOL,
    channel SYMBOL,
    step_index LONG,
    sample_index LONG,
    adc LONG,
    value DOUBLE,
    rate_hz DOUBLE,
    record_length LONG,
    total_steps LONG,
    timestamp TIMESTAMP
) TIMESTAMP(timestamp) PARTITION BY DAY;
"""


def ilp_escape(v: str) -> str:
    """Escape an ILP tag value: spaces, commas and equals must be backslashed."""
    return str(v).replace("\\", "\\\\").replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def ilp_connect():
    """Open the ILP ingestion socket (port 9009). ~600k rows/s vs ~3.5k on pg-wire."""
    return socket.create_connection((ILP_CONFIG["host"], ILP_CONFIG["port"]), timeout=30)


def create_questdb_table(recreate=False):
    """Create the table. Refuses to drop a non-empty one unless recreate=True:
    an unconditional DROP here will silently destroy a collection that another
    process is still writing."""
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            existing = 0
            try:
                cur.execute(f"SELECT count() FROM {TABLE};")
                existing = cur.fetchone()[0]
            except Exception:
                conn.rollback()                 # table does not exist yet
            if existing and not recreate:
                raise SystemExit(
                    f"{TABLE} already holds {existing:,} rows. Pass --recreate to "
                    f"drop it, or use a different table. Refusing to destroy data.")
            if existing:
                logging.warning(f"--recreate: dropping {existing:,} existing rows")
            cur.execute(f"DROP TABLE IF EXISTS {TABLE};")
            cur.execute(CREATE_SQL)
            conn.commit()
            logging.info(f"Clean {TABLE} table created")
    except SystemExit:
        raise
    except Exception as e:
        logging.error(f"Error creating QuestDB table: {e}")
        logging.error(traceback.format_exc())
    finally:
        connection_pool.putconn(conn)


def send_packet(sock, lines):
    """Ship one packet over ILP. Raises on failure — a dropped packet is a gap
    in the stream, and TCP ILP does not report rejected rows, so continuing
    would silently corrupt the collection."""
    try:
        sock.sendall("".join(lines).encode())
    except Exception as e:
        logging.error(f"Error sending ECG packet over ILP: {e}")
        logging.error(traceback.format_exc())
        raise


def run_chain_stream(data_dir, records, channel, window_s, rate_hz, packet_steps,
                     max_steps):
    """Emit the records in packets, paced against the wall clock, over ILP."""
    chain = ECGChain(data_dir, records, channel, window_s, max_steps=max_steps)
    record_length, total_steps = chain.record_length, chain.total_steps

    n_emit = total_steps if max_steps is None else min(max_steps, total_steps)
    dt = 1.0 / rate_hz
    logging.info(f"Streaming {len(records)} records | lead {channel} | "
                 f"{window_s} s each | {total_steps:,} samples | {rate_hz:,.0f} Hz | "
                 f"packets of {packet_steps:,}")
    logging.info(f"Emitting {n_emit:,} samples -> projected duration "
                 f"{n_emit / rate_hz / 60:.2f} min")

    ch = ilp_escape(channel)
    sock = ilp_connect()
    t_start = time.time()
    t0_ns = int(t_start * 1e9)

    lines, count, packets, current = [], 0, 0, None
    try:
        for e in chain.events():
            if e['record_id'] != current:
                current = e['record_id']
                logging.info(f"Record {current} (age {e['age_band']})")
            # ASSIGNED timestamp on a fixed grid, computed from the exact
            # fraction so a non-integer rate does not accumulate drift.
            ts_ns = t0_ns + round(count * 1e9 / rate_hz)
            lines.append(
                f"{TABLE},record_id={e['record_id']},age_band={ilp_escape(e['age_band'])},"
                f"channel={ch} "
                f"step_index={e['step']}i,sample_index={e['sample_index']}i,"
                f"adc={e['adc']}i,value={e['value']:.6f},"
                f"rate_hz={rate_hz},record_length={record_length}i,"
                f"total_steps={total_steps}i {ts_ns}\n")
            count += 1

            if len(lines) >= packet_steps:
                lag = (t_start + count * dt) - time.time()
                if lag > 0:
                    time.sleep(lag)
                send_packet(sock, lines)
                lines = []
                packets += 1
                if packets % 60 == 0:
                    el = time.time() - t_start
                    logging.info(f"Collected {count:,} raw ECG samples  "
                                 f"({count/el:,.0f} samples/s, {el:.0f}s elapsed)")
    finally:
        # never drop the tail, including on Ctrl-C
        if lines:
            try:
                send_packet(sock, lines)
                logging.info(f"Flushed final partial packet ({len(lines)} samples)")
            except Exception:
                logging.error("Final packet could not be flushed")
        sock.close()

    elapsed = time.time() - t_start
    logging.info(f"Done: {count:,} samples in {elapsed:.1f}s ({count/elapsed:,.0f} samples/s)")
    return count


def shutdown(signum, frame):
    """Raise, so the stream's finally-block flushes the partial packet."""
    logging.info(f"Received shutdown signal: {signum}")
    raise KeyboardInterrupt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rate", type=float, default=ECG_CONFIG["rate_hz"],
                   help="emission rate in Hz (1000 = the native rate)")
    p.add_argument("--packet", type=int, default=ECG_CONFIG["packet_steps"])
    p.add_argument("--max-steps", type=int, default=ECG_CONFIG["max_steps"])
    p.add_argument("--recreate", action="store_true",
                   help="drop an existing non-empty table before collecting")
    a = p.parse_args()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    create_questdb_table(recreate=a.recreate)
    records = read_records(ECG_CONFIG["records"])
    logging.info("Starting CLEAN ECG data stream processor...")
    logging.info(f"Source: {ECG_CONFIG['dataset']}, {len(records)} records")
    logging.info("✅ Raw data collection only")
    logging.info("✅ No SKA computations")
    logging.info("✅ Assigned timestamps on a fixed grid (not measured)")
    logging.info(f"✅ ILP ingestion on {ILP_CONFIG['host']}:{ILP_CONFIG['port']}")

    try:
        run_chain_stream(ECG_CONFIG["data_dir"], records, ECG_CONFIG["channel"],
                         ECG_CONFIG["window_s"], a.rate, a.packet, a.max_steps)
    except KeyboardInterrupt:
        logging.info("Interrupted — partial packet flushed")
    connection_pool.closeall()
