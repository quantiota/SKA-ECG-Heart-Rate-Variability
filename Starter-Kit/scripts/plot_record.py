#!/usr/bin/env python3
"""Figures for one record and one scale, read from data/ecg_ska_results.csv.gz.

    figures/ska_<record>_scale<s>.png      entropy H and P = exp(-|ΔH/H|) on the step index
    figures/bands3d_<record>_scale<s>.png  the steps in the learner's space (z, ż, P)

Colour = the transition between two successive waves (P→Q, Q→R, R→S, S→T, T→P).

Usage
    python scripts/plot_record.py 0060 25
    python scripts/plot_record.py 0060 selected     # the scale selected for that record
Requires: numpy, pandas, matplotlib
"""
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ska_data import NAMES, COLORS, load_run

OUT = pathlib.Path(__file__).resolve().parent.parent / "figures"


def main():
    rec, scale_arg = sys.argv[1].zfill(4), sys.argv[2]
    d, scale, age = load_run(rec, scale_arg)
    OUT.mkdir(exist_ok=True)
    title = f"Record {rec} (woman {age}), input Re ċ, scale {scale:g}"

    fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for name, color in zip(NAMES, COLORS):
        m = d.tr == name
        ax[0].scatter(d.event_index[m], d.entropy[m], s=2, color=color, label=name)
        ax[1].scatter(d.event_index[m], d.P[m], s=2, color=color)
    ax[0].set_ylabel("entropy H")
    ax[1].set_ylabel("P = exp(−|ΔH/H|)")
    ax[1].set_xlabel("step")
    ax[0].legend(markerscale=5, ncol=5, loc="upper right", fontsize=8)
    ax[0].set_title(title)
    f1 = OUT / f"ska_{rec}_scale{scale:g}.png"
    fig.savefig(f1, dpi=140, bbox_inches="tight"); plt.close(fig)

    fig = plt.figure(figsize=(9, 8))
    ax = fig.add_subplot(projection="3d")
    for name, color in zip(NAMES, COLORS):
        m = d.tr == name
        ax.scatter(d.knowledge[m], d.zdot[m], d.P[m], s=3, color=color, label=name, edgecolors="none")
    ax.set_xlabel("z = ‖Z‖"); ax.set_ylabel("ż (1/s)"); ax.set_zlabel("P")
    ax.legend(markerscale=4, fontsize=8)
    ax.set_title(title)
    f2 = OUT / f"bands3d_{rec}_scale{scale:g}.png"
    fig.savefig(f2, dpi=140, bbox_inches="tight"); plt.close(fig)
    print(f"saved {f1}\nsaved {f2}")


if __name__ == "__main__":
    main()
