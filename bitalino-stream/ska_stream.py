"""
BITalino ECG → SKA real-time learner, on the fly, with QuestDB storage.

Reads the raw ECG waveform from a BITalino (r)evolution board at 1000 Hz. Every sample is
handed to the SKA learner the moment it arrives, and the sample together with the learner's
state is written to QuestDB over ILP (TCP 9009). QuestDB only stores; it is not in the
learning path.

    BITalino ──► ska_stream.py ──► SKA learner (in process, sample by sample)
                       │
                       └──────────► QuestDB (raw sample + learner state, one row per sample)

The SKA real-time engine is proprietary and not part of this repository. It is plugged in
with --learner module:Class. The class must provide

    step(level: float) -> dict[str, float]

called once per sample with the input level in [0, 1]; the returned fields (for example
knowledge, entropy, P) are written to the same QuestDB row. Without --learner, only the raw
stream is stored.

Each row
    sample_index   0, 1, 2, …        the internal clock (1 sample = 1 ms)
    adc            raw 10-bit value   0 … 1023
    level          adc / 1023         input level in [0, 1]
    seq            BITalino sequence number (0 … 15), to detect dropped packets
    <learner>      fields returned by the learner's step()
    timestamp      t0 + sample_index × 1 ms  (constant step)

Usage
    python ska_stream.py --port /dev/ttyUSB0 --learner ska_engine:SKALearner
    python ska_stream.py --port /dev/ttyUSB0                  # raw stream only
    python ska_stream.py --simulate --seconds 60 --dry-run    # synthetic ECG, print rows

Safety: BITalino is a research kit, not a medical device. When electrodes are on the body,
run the computer on battery (unplugged from mains).
"""
import argparse
import importlib
import math
import socket
import sys
import time

import numpy as np

FS = 1000                 # Hz — 1 sample = 1 ms
ADC_MAX = 1023            # 10-bit analog channels A1–A4
ANALOG_COL = 5            # BITalino.read(): cols 0 seq, 1–4 digital, 5+ analog


class ILPWriter:
    """Minimal QuestDB InfluxDB-line-protocol writer over TCP."""

    def __init__(self, host, port, table, dry_run=False):
        self.table, self.dry_run = table, dry_run
        self.sock = None if dry_run else socket.create_connection((host, port))

    def write(self, lines):
        payload = "".join(lines)
        if self.dry_run:
            sys.stdout.write(payload)
        else:
            self.sock.sendall(payload.encode())

    def line(self, source, i, adc, seq, ts, state):
        fields = [f"sample_index={i}i", f"adc={adc}i", f"level={adc / ADC_MAX:.6f}", f"seq={seq}i"]
        fields += [f"{k}={float(v):.10g}" for k, v in state.items()
                   if v is not None and math.isfinite(float(v))]
        return f"{self.table},source={source} {','.join(fields)} {ts}\n"

    def close(self):
        if self.sock:
            self.sock.close()


def load_learner(spec):
    """'module:Class' → instance. The module must be importable (on PYTHONPATH)."""
    module, _, cls = spec.partition(":")
    return getattr(importlib.import_module(module), cls or "SKALearner")()


def synthetic_ecg(n, start, rng, bpm=70.0):
    """Synthetic 10-bit ECG (P, QRS, T as Gaussians) with beat-to-beat jitter, for testing."""
    t = (start + np.arange(n)) / FS
    period = 60.0 / bpm
    phase = (t % period) / period
    waves = [(0.10, 0.025, 0.15), (0.24, 0.008, -0.10), (0.25, 0.010, 1.00),
             (0.26, 0.008, -0.20), (0.45, 0.040, 0.30)]          # (centre, width, amplitude)
    x = sum(a * np.exp(-((phase - c) / w) ** 2) for c, w, a in waves)
    x = 0.45 + 0.35 * x + 0.01 * rng.standard_normal(n)
    return np.clip(np.round(x * ADC_MAX), 0, ADC_MAX).astype(int)


def main():
    ap = argparse.ArgumentParser(description="BITalino ECG → SKA learner on the fly + QuestDB storage")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--port", help="serial port (/dev/ttyUSB0, COM3) or MAC address")
    src.add_argument("--simulate", action="store_true", help="synthetic ECG, no device")
    ap.add_argument("--learner", help="SKA learner as module:Class, with step(level) -> dict")
    ap.add_argument("--channel", type=int, default=0, help="analog channel index (0 = A1)")
    ap.add_argument("--seconds", type=float, default=0, help="stop after N seconds (0 = run until Ctrl-C)")
    ap.add_argument("--block", type=int, default=100, help="samples per device read")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--ilp-port", type=int, default=9009)
    ap.add_argument("--table", default="ecg_stream")
    ap.add_argument("--dry-run", action="store_true", help="print ILP rows instead of sending")
    a = ap.parse_args()

    learner = load_learner(a.learner) if a.learner else None
    device, rng = None, np.random.default_rng(0)
    if a.port:
        from bitalino import BITalino          # pip install bitalino
        device = BITalino(a.port)
        device.start(FS, [a.channel])
    source = "simulate" if a.simulate else "bitalino"

    out = ILPWriter(a.host, a.ilp_port, a.table, a.dry_run)
    t0 = time.time_ns()
    i, last_seq, dropped = 0, None, 0
    limit = int(a.seconds * FS) if a.seconds else None
    try:
        while limit is None or i < limit:
            n = a.block if limit is None else min(a.block, limit - i)
            if device:
                data = device.read(n)
                adc, seq = data[:, ANALOG_COL].astype(int), data[:, 0].astype(int)
                if last_seq is not None:
                    gaps = (np.diff(np.r_[last_seq, seq]) % 16) - 1
                    dropped += int(gaps.clip(min=0).sum())
                last_seq = seq[-1]
            else:
                adc = synthetic_ecg(n, i, rng)
                seq = np.arange(i, i + n) % 16
                time.sleep(n / FS)                 # pace like the real device
            lines = []
            for j in range(n):                     # learn sample by sample, in order
                state = learner.step(adc[j] / ADC_MAX) if learner else {}
                lines.append(out.line(source, i + j, int(adc[j]), int(seq[j]),
                                      t0 + (i + j) * 1_000_000, state))
            out.write(lines)                       # store after learning, never in its path
            i += n
            if i % (10 * FS) < n:
                print(f"[{source}] {i:,} samples ({i / FS:.0f} s), dropped packets: {dropped}",
                      file=sys.stderr, flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        if device:
            device.stop()
            device.close()
        out.close()
        print(f"done: {i:,} samples, dropped packets: {dropped}", file=sys.stderr)


if __name__ == "__main__":
    main()
