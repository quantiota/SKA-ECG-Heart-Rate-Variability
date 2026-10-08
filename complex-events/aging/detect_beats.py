"""Beat detection that survives real recordings.

ska_complex_events.detect() finds R as any raw sample above 0.5 mV. On the Autonomic
Aging recordings that breaks two ways: baseline drift lifts whole stretches above
0.5 mV (false beats), and some leads have a small R (missed or doubled beats).

Here each beat is FOUND on a cleaned copy and MEASURED on the raw signal:

    find      50 Hz notch -> 5-20 Hz band (the QRS band) -> squared slope ->
              150 ms moving energy -> peaks above 40 % of the local maximum,
              at least 300 ms apart
    locate R  the highest raw sample within +/-60 ms of each energy peak,
              after removing the local baseline (200 ms moving median)

The cleaned copy is used only to say WHERE the beats are. Every value that follows --
event peaks, baselines, base arcs, z -- is taken from the raw signal, exactly as in
ska_complex_events.detect(), whose windows are reused unchanged.
"""
import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import butter, filtfilt, find_peaks, iirnotch


def r_peaks(x, fs=1000):
    """R peak sample indices of the raw signal x (mV)."""
    b, a = iirnotch(50.0, 30.0, fs)
    y = filtfilt(b, a, x)
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


def detect_robust(x, fs=1000):
    """Same output as ska_complex_events.detect(): [(events, baseline), ...] per beat."""
    ms = fs / 1000
    R = r_peaks(x, fs)
    beats = []
    for i in range(1, len(R) - 1):
        r, rr_next = R[i], R[i + 1] - R[i]
        base = np.median(x[r - int(300 * ms): r - int(220 * ms)])
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
