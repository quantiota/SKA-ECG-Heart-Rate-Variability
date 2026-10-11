"""
One beat = one turn of a circle whose circumference is the beat's duration.

Reads the phasor table written by complex-events/ (one row per wave: k, event, peak,
onset, offset, amplitude, RR) and draws, for each beat:

    left   the beat's circle, radius r = RR / 2π (arc length = time, 1 ms = 1 ms of arc),
           the five waves on their base arcs (onset → offset), the peaks
           (filled = positive wave, ring = negative wave), and the previous 12 circles
    right  the curvature κ = 1/r beat by beat; since arc length is time, it equals the
           angular frequency ω = 2π / RR (rad/s)

Angles are measured from the P peak, clockwise from the top: θ = t / r = κ t.

Real time (default): each beat is shown for its own RR, so the GIF plays at the heart's
pace (GIF frame times are rounded to 10 ms). With --fps, every beat gets the same time.

Usage
    python ska_ecg_circle_gif.py complex_events_0060.csv
    python ska_ecg_circle_gif.py complex_events_0060.csv --beats 200 --out circle_0060.gif
    python ska_ecg_circle_gif.py complex_events_0060.csv --fps 8          # fixed speed
Requires: numpy, pandas, matplotlib, pillow
"""
import argparse
import io

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

EV = "PQRST"
COL = dict(zip(EV, ["#3987e5", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
BG, INK, INK2, GRID = "#121317", "#f2f2f0", "#a9a8a2", "#2c2d33"


def load_beats(csv, n):
    d = pd.read_csv(csv)
    beats = []
    for k, g in d.groupby("k"):
        if len(beats) >= n:
            break
        g = g.set_index("event")
        if not set(EV) <= set(g.index):
            continue                                        # skip incomplete beats
        p0, RR = g.loc["P", "peak"], float(g.RR.iloc[0])
        ev = {e: (g.loc[e, "peak"] - p0, g.loc[e, "onset"] - p0,
                  g.loc[e, "offset"] - p0, g.loc[e, "amplitude"]) for e in EV}
        beats.append(dict(k=int(k), RR=RR, r=RR / (2 * np.pi), ev=ev))
    return beats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="complex_events_<record>.csv")
    ap.add_argument("--record", default="0060")
    ap.add_argument("--beats", type=int, default=200)
    ap.add_argument("--fps", type=float, default=None, help="fixed speed; default = real time")
    ap.add_argument("--trail", type=int, default=12, help="previous circles shown")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or f"ska_ecg_{a.record}_circle{'' if a.fps else '_realtime'}.gif"

    beats = load_beats(a.csv, a.beats)
    N = len(beats)
    kap = np.array([2 * np.pi / b["RR"] * 1000 for b in beats])          # rad/s
    RMAX = max(b["r"] for b in beats) * 1.18

    fig = plt.figure(figsize=(12.8, 7.2), facecolor=BG)
    ax = fig.add_axes([0.03, 0.04, 0.52, 0.82]); ax.set_facecolor(BG)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-RMAX, RMAX); ax.set_ylim(-RMAX, RMAX)
    bx = fig.add_axes([0.62, 0.16, 0.35, 0.55]); bx.set_facecolor(BG)
    for s in bx.spines.values():
        s.set_color(GRID)
    bx.tick_params(colors=INK2, labelsize=9); bx.grid(color=GRID, lw=.6)
    bx.set_xlim(0, N); bx.set_ylim(kap.min() * 0.98, kap.max() * 1.02)
    bx.set_xlabel("beat k", color=INK2); bx.set_ylabel("κ = 1/r = ω = 2π / RR  (rad/s)", color=INK2)
    line, = bx.plot([], [], color=INK, lw=1.2)
    dot, = bx.plot([], [], "o", color="#e87ba4", ms=7)

    pace = "fixed speed" if a.fps else "real time: each beat is shown for its own RR"
    fig.text(0.03, 0.94, "One beat = one turn of a circle whose circumference is the beat's duration",
             color=INK, fontsize=16, fontweight="bold")
    fig.text(0.03, 0.905, f"Record {a.record} · PhysioNet Autonomic Aging · {pace} · "
             "RR = 2πr, arc length = time, θ = κt from the P peak", color=INK2, fontsize=10.5)
    for i, e in enumerate(EV):
        fig.text(0.62 + 0.07 * i, 0.80, f"● {e}", color=COL[e], fontsize=13)
    fig.text(0.62, 0.765, "filled = positive wave · ring = negative wave (usually Q and S)", color=INK2, fontsize=9.5)

    th = lambda t, r: np.pi / 2 - t / r                     # P at the top, clockwise
    full = np.linspace(0, 2 * np.pi, 400)
    artists = []

    def draw(i):
        for x in artists:
            x.remove()
        artists.clear()
        b, r = beats[i], beats[i]["r"]
        for j in range(max(0, i - a.trail), i):                          # earlier beats
            rj = beats[j]["r"]; alpha = 0.04 + 0.02 * (j - i + a.trail) / a.trail
            artists.append(ax.plot(rj * np.cos(full), rj * np.sin(full), color=(1, 1, 1, alpha), lw=1)[0])
        artists.append(ax.plot(r * np.cos(full), r * np.sin(full), color="#5a5b63", lw=1.5)[0])
        for e, (pk, on, off, amp) in b["ev"].items():
            tt = th(np.linspace(on, off, 60), r)
            artists.append(ax.plot(r * np.cos(tt), r * np.sin(tt), color=COL[e], lw=7, solid_capstyle="butt")[0])
            x, y = r * np.cos(th(pk, r)), r * np.sin(th(pk, r))
            artists.append(ax.scatter([x], [y], s=110, color=COL[e] if amp > 0 else BG,
                                      edgecolor=COL[e], lw=2.2, zorder=5))
            artists.append(ax.text(1.13 * x, 1.13 * y, e, color=COL[e], fontsize=12,
                                   fontweight="bold", ha="center", va="center"))
        artists.append(ax.text(0, 22, f"beat {b['k'] + 1}", color=INK, fontsize=15, ha="center", fontweight="bold"))
        artists.append(ax.text(0, -2, f"RR = {b['RR']:.0f} ms   r = {r:.1f} ms", color=INK2, fontsize=11, ha="center"))
        artists.append(ax.text(0, -24, f"κ = 1/r = 2π/RR = {kap[i]:.2f} rad/s", color=INK2, fontsize=11, ha="center"))
        line.set_data(np.arange(i + 1), kap[:i + 1]); dot.set_data([i], [kap[i]])

    frames = []
    for i in range(N):
        draw(i)
        buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=100, facecolor=BG); buf.seek(0)
        frames.append(Image.open(buf).convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT))
        if i % 50 == 0:
            print(f"beat {i}/{N}", flush=True)

    if a.fps:
        dur = [int(round(1000 / a.fps))] * N
    else:
        dur = [int(round(b["RR"], -1)) for b in beats]                   # real time
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=dur, loop=0, optimize=True)
    print(f"saved {out}  ({N} beats, {sum(dur) / 1000:.1f} s)")


if __name__ == "__main__":
    main()
