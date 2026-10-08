"""Validate collected ECG data in QuestDB."""
import psycopg2

from config import QDB_CONFIG, ECG_CONFIG
from ecg_chain import ECGRecord, read_records

TABLE = "ecg_steps"


def validate_ecg_data():
    """Run validation queries on collected ECG sample data."""
    try:
        conn = psycopg2.connect(**QDB_CONFIG)
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES;")
            if TABLE not in [t[0] for t in cur.fetchall()]:
                print(f"❌ {TABLE} table not found")
                return

            cur.execute(f"SELECT COUNT(*) FROM {TABLE};")
            total = cur.fetchone()[0]
            print(f"📊 Total samples collected: {total:,}")

            cur.execute(f"""SELECT record_id, age_band, COUNT(*) AS n,
                                   MIN(sample_index), MAX(sample_index),
                                   count_distinct(sample_index), MAX(record_length)
                            FROM {TABLE} GROUP BY record_id, age_band
                            ORDER BY MIN(step_index);""")
            per_record = cur.fetchall()
            print(f"\n📍 Samples per record ({len(per_record)} records):")
            gaps = dups = 0
            for rec, band, n, lo, hi, nd, rl in per_record:
                g, d = (hi - lo + 1) - nd, n - nd
                gaps += g
                dups += d
                pct = 100.0 * n / rl if rl else 0.0
                print(f"   {rec}  {band:6s} {n:>9,} samples  index {lo:,}–{hi:,}  "
                      f"{pct:5.1f}% of window"
                      f"{'' if g == 0 and d == 0 else f'   gaps {g}, duplicates {d}'}")

            cur.execute(f"""SELECT record_id, MIN(value), MAX(value), AVG(value), STDDEV(value)
                            FROM {TABLE} GROUP BY record_id ORDER BY record_id;""")
            print("\n📈 Value statistics (mV):")
            for rec, lo, hi, avg, sd in cur.fetchall():
                sd = sd if sd is not None else float('nan')
                print(f"   {rec}: {lo:+.3f} to {hi:+.3f}  (avg {avg:+.4f}, std {sd:.4f})")

            cur.execute(f"""SELECT record_id, step_index, sample_index, value, timestamp
                            FROM {TABLE} ORDER BY timestamp DESC LIMIT 5;""")
            print("\n🕐 Recent samples:")
            for rec, si, k, val, ts in cur.fetchall():
                print(f"   {rec} step {si:,} sample {k:,} {val:+.4f} mV at {ts}")

            # ---- stream coverage: every step_index exactly once ------------
            cur.execute(f"""SELECT count(), count_distinct(step_index),
                                   min(step_index), max(step_index),
                                   min(timestamp), max(timestamp)
                            FROM {TABLE};""")
            n, n_distinct, lo, hi, t0, t1 = cur.fetchone()
            span_ms = (t1 - t0).total_seconds() * 1000
            print("\n🫀 Stream coverage:")
            print(f"   rows {n:,}   distinct step_index {n_distinct:,}   range {lo:,}–{hi:,}")
            print(f"   repeated steps:   {n - n_distinct:,}")
            print(f"   gaps within range: {(hi - lo + 1) - n_distinct:,}")
            print(f"   timestamps span {span_ms:,.0f} ms for {n - 1:,} intervals "
                  f"({'1 ms grid' if abs(span_ms - (n - 1)) < 1 else 'NOT on the 1 ms grid'})")

            # ---- round trip: database against the record files -------------
            print("\n⚖️  Collected vs record files (count, sum of adc, mV range):")
            mismatches = 0
            for rec, band, cnt, *_ in per_record:
                r = ECGRecord(ECG_CONFIG["data_dir"], rec, ECG_CONFIG["channel"],
                              ECG_CONFIG["window_s"])
                cur.execute(f"""SELECT sum(adc), min(value), max(value) FROM {TABLE}
                                WHERE record_id = %s;""", (rec,))
                sadc, vmin, vmax = cur.fetchone()
                adc, v = r.adc[:cnt], r.value()[:cnt]
                ok = (int(sadc) == int(adc.sum()) and abs(vmin - v.min()) < 1e-5
                      and abs(vmax - v.max()) < 1e-5)
                mismatches += not ok
                print(f"   {rec}  {cnt:>9,}  adc sum {int(sadc):>14,} vs {int(adc.sum()):>14,}"
                      f"  {'✅' if ok else '<-- MISMATCH'}")
            print(f"   {'✅ all records match' if mismatches == 0 else f'❌ {mismatches} mismatched'}")

            listed = read_records(ECG_CONFIG["records"])
            collected = {r[0] for r in per_record}
            missing = [r for r in listed if r not in collected]
            print(f"\n📋 Records: {len(collected)} of {len(listed)} listed in records.txt"
                  f"{'' if not missing else f' — not yet collected: {missing}'}")

            print("\n🔍 Data quality:")
            checks = {}
            for col in ("value", "adc", "record_id", "step_index", "sample_index"):
                cur.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE {col} IS NULL;")
                checks[f"NULL {col}"] = cur.fetchone()[0]
            checks["duplicate step_index"] = n - n_distinct
            checks["step gaps"] = (hi - lo + 1) - n_distinct
            checks["sample_index gaps within a record"] = gaps
            checks["duplicate sample_index within a record"] = dups
            checks["records not matching their file"] = mismatches

            for k, v in checks.items():
                print(f"   {k}: {v:,}")

            if all(v == 0 for v in checks.values()):
                print("✅ Data quality PASSED")
            else:
                print("⚠️  Data quality issues detected")

        conn.close()

    except Exception as e:
        print(f"❌ Data validation failed: {e}")


if __name__ == "__main__":
    validate_ecg_data()
