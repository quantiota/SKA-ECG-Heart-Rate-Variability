"""
ECG raw waveform → five events per beat → phasors → candidate learner inputs.

For each beat (cycle index k) the five events P, Q, R, S, T are located on the raw signal,
each with its base arc (onset → offset). One beat is one turn of a circle whose circumference
is the beat period:  RR = 2πr  →  r = RR / 2π  (arc length = time, 1 sample = 1 ms).

    c_j  = (1/r) Σ_{t ∈ arc_j} x(t) · e^{i t / r}      event phasor j, t = ms since the P peak
    C_k  = Σ_j c_j                                      beat phasor k
    ċ_n  = c_n − c_{n−1}                                derivative on the event index n = 5k + j

(c and C, not z and Z: in SKA, z is the learner's knowledge and ż its flow.)

The arc edges of the broad waves, P and T, are found on a copy of the signal with the mains
line (50 Hz) notched out: on the raw trace the ripple riding on a broad, flat wave creates
sign crossings every 20 ms, and the edge stops at one of them. The sharp waves Q, R, S keep
their edges on the raw trace, where the notch would ring and smear them. The phasor itself
is always summed on the raw signal. A wave that does not reach its expected sign on the
signal used for its edges (P, R, T above the baseline; Q, S below) is absent: its arc is
empty and c_j = 0 (column `present` = False). An arc never starts before the end of the previous
wave's arc nor ends after the next wave's peak, so the five arcs of a beat never overlap.
The baseline of a beat is the straight line joining the flat stretch before its P to the flat
stretch before the next P, so it follows the drift across the beat.

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
from scipy.ndimage import median_filter
from scipy.signal import butter, filtfilt, find_peaks, iirnotch

EVENTS = "PQRST"
SIGN = dict(P=1, Q=-1, R=1, S=-1, T=1)          # expected sign of each wave
BROAD = "PT"                                    # waves whose edges are found on the notched copy


def same_sign_arc(xb, peak, lo, hi):
    """Base arc of a wave: the run of samples around its peak with the peak's sign."""
    s = np.sign(xb[peak]); a = b = peak
    while a > lo and np.sign(xb[a - 1]) == s:
        a -= 1
    while b < hi - 1 and np.sign(xb[b + 1]) == s:
        b += 1
    return a, b + 1


def edge_signal(x, fs=1000, mains=50.0):
    """Copy of x with the mains line notched out, used only to find the edges of P and T."""
    b, a = iirnotch(mains, 30.0, fs)
    return filtfilt(b, a, x)


def wave_arc(xeb, name, peak, lo, hi):
    """Arc of a wave on a baseline-removed signal; (peak, peak) if the wave is absent."""
    if np.sign(xeb[peak]) != SIGN[name]:
        return peak, peak
    return same_sign_arc(xeb, peak, lo, hi)


def r_peaks(x, fs=1000, mains=50.0):
    """R peak sample indices of the raw signal x (mV).

    Found on a cleaned copy (mains notch -> 5-20 Hz QRS band -> squared slope -> 150 ms
    moving energy -> peaks above 40 % of the local maximum, at least 300 ms apart), then
    located on the raw signal: the highest sample within +/-60 ms, after removing the local
    baseline. A fixed threshold on the raw trace would also take tall T waves for R.
    """
    y = edge_signal(x, fs, mains)
    b, a = butter(3, [5.0, 20.0], btype="band", fs=fs)
    y = filtfilt(b, a, y)
    energy = np.convolve(np.gradient(y) ** 2, np.ones(int(0.15 * fs)) / (0.15 * fs), "same")

    win = int(5 * fs)                                   # local maximum over 5 s windows
    local_max = np.maximum.reduceat(energy, np.arange(0, len(energy), win))
    threshold = 0.4 * np.repeat(local_max, win)[:len(energy)]
    pk, _ = find_peaks(energy, height=threshold, distance=int(0.3 * fs))

    xb = x - median_filter(x, size=int(0.2 * fs) | 1)   # remove the local baseline
    h = int(0.06 * fs)
    return np.array([p - h + np.argmax(xb[max(p - h, 0):p + h]) for p in pk
                     if p - h >= 0 and p + h <= len(x)])


def detect(x, fs=1000):
    """Locate P, Q, R, S, T peaks per beat (windows in ms around R) and a baseline per beat."""
    ms = fs / 1000
    R = r_peaks(x, fs)
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


def baseline_line(beats, k, idx, fs=1000):
    """Baseline of beat k at sample indices idx: the straight line from this beat's flat
    stretch before P to the next beat's (both measured 300-220 ms before R, as in detect())."""
    (ev, b0), (ev2, b1) = beats[k], beats[k + 1]
    t0, t1 = ev["R"] - int(260 * fs / 1000), ev2["R"] - int(260 * fs / 1000)
    return b0 + (b1 - b0) * (idx - t0) / (t1 - t0)


def complex_events(x, beats, fs=1000, mains=50.0):
    xe = edge_signal(x, fs, mains)                           # P, T edges only; the sum stays raw
    rows = []
    for k in range(len(beats) - 1):
        ev = beats[k][0]
        RR = beats[k + 1][0]["P"] - ev["P"]                  # P peak → next P peak, ms
        r = RR / (2 * np.pi)
        off = max(ev["P"] - int(400 * fs / 1000), 0)         # the beat's window, baseline removed
        stop = min(beats[k + 1][0]["P"] + 1, len(x))
        L = baseline_line(beats, k, np.arange(off, stop), fs)
        xb, xeb = x[off:stop] - L, xe[off:stop] - L
        nxt = [ev[n] for n in EVENTS[1:]] + [beats[k + 1][0]["P"]]   # peak of the next wave
        end = ev["P"] - int(150 * fs / 1000)                         # end of the previous arc
        for j, name in enumerate(EVENTS):
            pk = ev[name]
            lo, hi = max(pk - 150, end), min(pk + 250, nxt[j])       # an arc stays between its neighbours
            a, b = wave_arc(xeb if name in BROAD else xb, name, pk - off, lo - off, hi - off)
            a, b = a + off, b + off
            end = max(end, b)
            t = np.arange(a, b)
            c = np.sum(xb[t - off] * np.exp(1j * (t - ev["P"]) / r)) / r   # 0 for an absent wave
            rows.append(dict(event_index=5 * k + j, k=k, event=name, peak=pk, onset=a, offset=b,
                             arc=b - a, amplitude=xb[pk - off], present=b > a, RR=RR, r=r,
                             c_cos=c.real, c_sin=c.imag))
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
    d = complex_events(x, detect(x, a.fs), a.fs)
    d.to_csv(a.out, index=False)
    print(f"{d.k.nunique()} beats, {len(d)} events → {a.out}")


if __name__ == "__main__":
    main()
