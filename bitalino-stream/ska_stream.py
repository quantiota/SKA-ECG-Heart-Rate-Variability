"""
BITalino ECG → QuestDB real-time stream (input side of SKA-HRV).

Reads the raw ECG waveform from a BITalino (r)evolution board at 1000 Hz and writes
one row per sample to QuestDB over ILP (TCP 9009). The SKA real-time learner consumes
the table as it fills; this script does no signal processing and no learning.

Each row
    run            tag identifying this acquisition (default: its UTC start time)
    sample_index   0, 1, 2, …        the internal clock (1 sample = 1 ms)
    adc            raw 10-bit value   0 … 1023
    level          adc / 1023         input level in [0, 1]
    seq            BITalino sequence number (0 … 15), to detect dropped packets
    timestamp      t0 + sample_index × 1 ms  (constant step)

The clock survives dropped packets: samples lost in transmission are detected from the
sequence number and skipped in sample_index, so the samples after a loss keep their true
position and RR intervals are not shortened. Losses of up to 15 consecutive samples are
counted exactly (15 shows up as a repeated sequence number). The 4-bit sequence number
cannot tell larger losses apart: they are counted modulo 16.

Usage
    python ska_stream.py --port /dev/ttyUSB0                 # Linux, USB
    python ska_stream.py --port COM3                         # Windows, USB
    python ska_stream.py --simulate --seconds 60             # synthetic ECG, no device
    python ska_stream.py --port /dev/ttyUSB0 --dry-run       # print rows, no QuestDB

Safety: BITalino is a research kit, not a medical device. When electrodes are on the body,
run the computer on battery (unplugged from mains).
"""
import argparse
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

    def write(self, rows, run):
        payload = "".join(
            f"{self.table},source={src},run={run} "
            f"sample_index={i}i,adc={a}i,level={a / ADC_MAX:.6f},seq={s}i {ts}\n"
            for src, i, a, s, ts in rows)
        if self.dry_run:
            sys.stdout.write(payload)
        else:
            self.sock.sendall(payload.encode())

    def close(self):
        if self.sock:
            self.sock.close()


class SyntheticECG:
    """Synthetic 10-bit ECG (P, QRS, T as Gaussians) with real beat-to-beat variability.

    Each RR interval is the mean period modulated by respiratory sinus arrhythmia (a slow
    sinusoid) plus beat-to-beat noise. With the defaults the SDNN is about 30 ms over five
    minutes -- breathing alone gives about 24 ms, the beat noise the rest -- the order of a
    resting adult, so that an HRV pipeline has variability to find.
    """
    WAVES = [(0.10, 0.025, 0.15), (0.24, 0.008, -0.10), (0.25, 0.010, 1.00),
             (0.26, 0.008, -0.20), (0.45, 0.040, 0.30)]           # (centre, width, amplitude)

    def __init__(self, rng, bpm=70.0, rsa=0.04, resp_hz=0.25, jitter=0.02):
        self.rng, self.mean_rr = rng, 60.0 / bpm
        self.rsa, self.resp_hz, self.jitter = rsa, resp_hz, jitter
        self.onsets = [0.0]                                      # beat start times, seconds

    def _extend(self, t_end):
        while self.onsets[-1] <= t_end:
            t = self.onsets[-1]
            rr = self.mean_rr * (1 + self.rsa * np.sin(2 * np.pi * self.resp_hz * t)
                                 + self.jitter * self.rng.standard_normal())
            self.onsets.append(t + rr)

    def read(self, n, start):
        t = (start + np.arange(n)) / FS
        self._extend(t[-1])
        on = np.asarray(self.onsets)
        k = np.searchsorted(on, t, side="right") - 1             # beat each sample falls in
        phase = (t - on[k]) / (on[k + 1] - on[k])
        x = sum(a * np.exp(-((phase - c) / w) ** 2) for c, w, a in self.WAVES)
        x = 0.45 + 0.35 * x + 0.01 * self.rng.standard_normal(n)
        return np.clip(np.round(x * ADC_MAX), 0, ADC_MAX).astype(int)


def main():
    ap = argparse.ArgumentParser(description="BITalino ECG → QuestDB stream for SKA-HRV")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--port", help="serial port (/dev/ttyUSB0, COM3) or MAC address")
    src.add_argument("--simulate", action="store_true", help="synthetic ECG, no device")
    ap.add_argument("--channel", type=int, default=0, help="analog channel index (0 = A1)")
    ap.add_argument("--seconds", type=float, default=0, help="stop after N seconds (0 = run until Ctrl-C)")
    ap.add_argument("--block", type=int, default=100, help="samples per read")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--ilp-port", type=int, default=9009)
    ap.add_argument("--table", default="ecg_stream")
    ap.add_argument("--dry-run", action="store_true", help="print ILP rows instead of sending")
    ap.add_argument("--run", default=None,
                    help="tag for this acquisition (default: UTC start time, e.g. 20261007T121500)")
    a = ap.parse_args()

    device, rng = None, np.random.default_rng(0)
    sim = None if a.port else SyntheticECG(rng)
    if a.port:
        from bitalino import BITalino          # pip install bitalino
        device = BITalino(a.port)
        device.start(FS, [a.channel])
    source = "simulate" if a.simulate else "bitalino"

    out = ILPWriter(a.host, a.ilp_port, a.table, a.dry_run)
    t0 = time.time_ns()
    run = a.run or time.strftime("%Y%m%dT%H%M%S", time.gmtime(t0 / 1e9))
    i, last_seq, dropped = 0, None, 0           # i counts samples received
    limit = int(a.seconds * FS) if a.seconds else None
    try:
        while limit is None or i < limit:
            n = a.block if limit is None else min(a.block, limit - i)
            if device:
                data = device.read(n)
                adc, seq = data[:, ANALOG_COL].astype(int), data[:, 0].astype(int)
                prev = seq[0] - 1 if last_seq is None else last_seq
                # samples lost before each one: a step of 1 is no loss, and a REPEATED
                # sequence number (step 0) means exactly 15 lost -- it cannot occur otherwise
                gaps = (np.diff(np.r_[prev, seq]) - 1) % 16
                last_seq = seq[-1]
            else:
                adc = sim.read(n, i + dropped)
                seq = (np.arange(i, i + n) % 16)
                gaps = np.zeros(n, dtype=int)
                time.sleep(n / FS)                 # pace like the real device
            idx = i + dropped + np.arange(n) + np.cumsum(gaps)   # true position on the 1 ms clock
            dropped += int(gaps.sum())
            ts = t0 + idx * 1_000_000                           # constant 1 ms step, in ns
            out.write(zip([source] * n, idx, adc, seq, ts), run)
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
        print(f"done: run {run}, {i:,} samples received, {dropped} lost "
              f"(clock spans {i + dropped:,} ms)", file=sys.stderr)


if __name__ == "__main__":
    main()
