"""
ECG raw waveform → five events per beat → phasors → candidate learner inputs.

For each beat (cycle index k) the five events P, Q, R, S, T are located on the raw signal,
each with its base arc (onset → offset). One beat is one turn of a circle whose circumference
is the beat period:  RR = 2πr  →  r = RR / 2π  (arc length = time, 1 sample = 1 ms).

    c_j  = (1/r) Σ_{t ∈ arc_j} x(t) · e^{i t / r}      event phasor j, t = ms since the P peak
    C_k  = Σ_j c_j                                      beat phasor k
    ċ_n  = c_n − c_{n−1}                                derivative on the event index n = 5k + j

(c and C, not z and Z: in SKA, z is the learner's knowledge and ż its flow.)

Candidate inputs for the SKA learner (one value per event):
    cos  = Re ċ_n        sin  = Im ċ_n

Usage
    python ska_complex_events.py ecg.csv                      # column ECG, mV, 1000 Hz
    python ska_complex_events.py ecg.csv --column ECG --fs 1000 --out events.csv
Requires: numpy, pandas, scipy
"""
import argparse

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

EVENTS = "PQRST"


def same_sign_arc(xb, peak, lo, hi):
    """Base arc of a wave: the run of samples around its peak with the peak's sign."""
    s = np.sign(xb[peak]); a = b = peak
    while a > lo and np.sign(xb[a - 1]) == s:
        a -= 1
    while b < hi - 1 and np.sign(xb[b + 1]) == s:
        b += 1
    return a, b + 1


def detect(x, fs=1000, r_height=0.5):
    """Locate P, Q, R, S, T peaks per beat (windows in ms around R) and a baseline per beat."""
    ms = fs / 1000
    R, _ = find_peaks(x, height=r_height, distance=int(300 * ms))
    beats = []
    for i in range(1, len(R) - 1):
        r, rr_next = R[i], R[i + 1] - R[i]
        base = np.median(x[r - int(300 * ms): r - int(220 * ms)])     # flat stretch before P
        xb = x - base
        w = lambda a, b: slice(r + int(a * ms), r + int(b * ms))
        t0, t1 = r + int(120 * ms), r + int(0.6 * rr_next)
        ev = {"P": w(-280, -80).start + np.argmax(xb[w(-280, -80)]),
              "Q": w(-60, 0).start + np.argmin(xb[w(-60, 0)]),
              "R": r,
              "S": r + np.argmin(xb[w(0, 60)]),
              "T": t0 + np.argmax(xb[t0:t1])}
        beats.append((ev, base))
    return beats


def complex_events(x, beats):
    rows = []
    for k in range(len(beats) - 1):
        ev, base = beats[k]
        RR = beats[k + 1][0]["P"] - ev["P"]                  # P peak → next P peak, ms
        r = RR / (2 * np.pi)
        xb = x - base
        for j, name in enumerate(EVENTS):
            pk = ev[name]
            a, b = same_sign_arc(xb, pk, pk - 150, pk + 250)
            t = np.arange(a, b)
            c = np.sum(xb[t] * np.exp(1j * (t - ev["P"]) / r)) / r
            rows.append(dict(event_index=5 * k + j, k=k, event=name, peak=pk, onset=a, offset=b,
                             arc=b - a, amplitude=xb[pk], RR=RR, r=r, c_cos=c.real, c_sin=c.imag))
    d = pd.DataFrame(rows)
    c = d.c_cos + 1j * d.c_sin
    cd = c.diff()                                            # ċ on the event index
    d["cdot_cos"], d["cdot_sin"] = np.real(cd.values), np.imag(cd.values)
    d.loc[0, ["cdot_cos", "cdot_sin"]] = np.nan                # no previous event
    d["transition"] = d.event.shift().fillna("") + "→" + d.event
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv"); ap.add_argument("--column", default="ECG")
    ap.add_argument("--fs", type=int, default=1000); ap.add_argument("--out", default="complex_events.csv")
    a = ap.parse_args()
    x = pd.read_csv(a.csv)[a.column].values
    d = complex_events(x, detect(x, a.fs))
    d.to_csv(a.out, index=False)
    print(f"{d.k.nunique()} beats, {len(d)} events → {a.out}")


if __name__ == "__main__":
    main()
