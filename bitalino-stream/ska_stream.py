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
    python ska_stream.py --port XX:XX:XX:XX:XX:XX --channel 1      # Linux/macOS, Bluetooth MAC, ECG on A2
    python ska_stream.py --port COM3 --channel 1                   # Windows, Bluetooth serial port
    python ska_stream.py --simulate --seconds 60                   # synthetic ECG, no device
    python ska_stream.py --port XX:XX:XX:XX:XX:XX --channel 1 --dry-run   # print rows, no QuestDB

The BITalino has no USB data link: it streams by Bluetooth only.

Safety: BITalino is a research kit, not a medical device. Never wear the electrodes while
the BITalino is charging.
"""
import argparse
import functools
import re
import select
import socket
import sys
import time

import numpy as np

FS = 1000                 # Hz — 1 sample = 1 ms
ADC_MAX = 1023            # 10-bit analog channels A1–A4
FRAME = 3                 # bytes per sample with one analog channel
LINK_TIMEOUT = 5.0        # s without any byte = the link is lost


@functools.lru_cache(maxsize=None)
def crc4(b0, b1, b2):
    """CRC-4 of a frame, its own CRC nibble (low nibble of the last byte) set to 0."""
    x = 0
    for byte in (b0, b1, b2 & 0xF0):
        for bit in range(7, -1, -1):
            x <<= 1
            if x & 0x10:
                x ^= 0x03
            x ^= (byte >> bit) & 1
    return x & 0x0F


def frame_ok(buf, p):
    return crc4(buf[p], buf[p + 1], buf[p + 2]) == buf[p + 2] & 0x0F


def next_seq(buf, p, q):
    """The frame at q carries the sequence number that follows the one at p."""
    return buf[q + 2] >> 4 == ((buf[p + 2] >> 4) + 1) % 16


class BITalinoLink:
    """One analog channel of a BITalino (r)evolution, read and decoded here.

    The bitalino package reads one byte per call and aborts the whole run on the first
    frame whose CRC fails. This reader receives the bytes in blocks and checks each
    3-byte frame itself. A frame is taken when its CRC is valid and its sequence number
    follows the previous one; otherwise (a lost or damaged frame) the reader moves on byte
    by byte and locks again on two consecutive valid frames with consecutive sequence
    numbers. Samples lost that way show up as a gap in the sequence number, like samples
    lost in transmission.

    Frame (one channel):  byte 0 = A[5:0] + 2 bits,  byte 1 = I1 I2 O1 O2 + A[9:6],
                          byte 2 = sequence number (high nibble) + CRC-4 (low nibble)
    """

    def __init__(self, port, channel):
        if re.fullmatch(r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", port):
            import bluetooth                          # installed with the bitalino package
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.sock.connect((port, 1))
            self.serial = None
        else:
            import serial                             # Windows: the Bluetooth COM port
            self.serial = serial.Serial(port, 115200, timeout=0.1)
            self.sock = None
        self.channel, self.buf, self.bad_bytes, self.last = channel, bytearray(), 0, None
        self.send(0xFF)                               # go to idle from any mode
        self.drain(0.5)                               # drop what a previous run left streaming
        self.version = self.ask_version()

    def send(self, cmd):
        time.sleep(0.1)
        (self.serial.write if self.serial else self.sock.send)(bytes([cmd]))

    def recv(self, wait):
        """The bytes available within `wait` seconds (b'' if none)."""
        if self.serial:
            return self.serial.read(max(1, self.serial.in_waiting))
        ready, _, _ = select.select([self.sock], [], [], wait)
        return self.sock.recv(4096) if ready else b""

    def drain(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            self.recv(0.1)

    def ask_version(self):
        self.send(0x07)
        text, end = b"", time.time() + 3
        while time.time() < end and not (b"BITalino" in text and text.endswith(b"\n")):
            text += self.recv(0.1)
        if b"BITalino" not in text:
            raise SystemExit(f"no answer from the BITalino (got {text[:20]!r})")
        return text[text.index(b"BITalino"):].strip().decode("ascii", "replace")

    def start(self):
        self.send((3 << 6) | 0x03)                    # sampling rate 1000 Hz
        self.send(0x01 | 1 << (2 + self.channel))     # live mode, this analog channel

    def read(self, n):
        """n samples: (sequence numbers, ADC values)."""
        seq, adc, last = [], [], time.time()
        while len(adc) < n:
            chunk = self.recv(0.2)
            if chunk:
                self.buf += chunk
                last = time.time()
            elif time.time() - last > LINK_TIMEOUT:
                raise ConnectionError(f"no data from the BITalino for {LINK_TIMEOUT:g} s")
            p, b = 0, self.buf
            while len(adc) < n and p + 2 * FRAME <= len(b):
                follows = self.last is not None and b[p + 2] >> 4 == (self.last + 1) % 16
                if frame_ok(b, p) and (follows or (frame_ok(b, p + FRAME)
                                                   and next_seq(b, p, p + FRAME))):
                    self.last = b[p + 2] >> 4
                    seq.append(self.last)
                    adc.append(((b[p + 1] & 0x0F) << 6) | (b[p] >> 2))
                    p += FRAME
                else:
                    p += 1
                    self.bad_bytes += 1
            del self.buf[:p]
        return np.array(seq), np.array(adc)

    def close(self):
        try:
            self.send(0x00)                           # stop the acquisition
        finally:
            (self.serial or self.sock).close()


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
    src.add_argument("--port", help="Bluetooth MAC address (Linux, macOS) or Bluetooth serial port (Windows, COM3)")
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
        device = BITalinoLink(a.port, a.channel)
        print(f"connected: {device.version}", file=sys.stderr)
        device.start()
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
                seq, adc = device.read(n)
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
    except ConnectionError as e:
        print(f"stopped: {e}", file=sys.stderr)
    finally:
        if device:
            device.close()
        out.close()
        bad = f", {device.bad_bytes} bytes skipped on CRC errors" if device else ""
        print(f"done: run {run}, {i:,} samples received, {dropped} lost "
              f"(clock spans {i + dropped:,} ms){bad}", file=sys.stderr)


if __name__ == "__main__":
    main()
