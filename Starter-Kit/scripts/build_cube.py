#!/usr/bin/env python3
"""3D cube (HTML, Three.js, WebXR) for one record and one scale, read from data/ecg_ska_results.csv.gz.

Axes: z = ‖Z‖ (knowledge), ż = dz/dt (1/s), P = exp(−|ΔH/H|).
Colour = the five transitions of the heartbeat. Open the HTML file in a browser.

Usage
    python scripts/build_cube.py 0060 25              # → vr/ska_ecg_0060_scale25_vr.html
    python scripts/build_cube.py 0060 selected
Requires: numpy, pandas
"""
import json
import pathlib
import sys

from ska_data import NAMES, COLORS, load_run

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "vr"


def main():
    rec, scale_arg = sys.argv[1].zfill(4), sys.argv[2]
    d, scale, age = load_run(rec, scale_arg)
    D = dict(z=d.knowledge.round(2).tolist(), zd=d.zdot.round(3).tolist(), p=d.P.round(4).tolist(),
             t=[NAMES.index(t) for t in d.tr], names=NAMES, colors=COLORS,
             zmax=float(d.knowledge.max()), zdmax=float(d.zdot.max()))
    desc = (f"Record {rec}, PhysioNet Autonomic Aging (woman {age}, lead ECG1, 1000 Hz), "
            f"{d.k.nunique()} beats = {len(d):,} steps of SKA real-time learning. "
            f"Input: Re ċ (cosine), scale {scale:g}. Horizontal axes: z = ‖Z‖ and ż = dz/dt (1/s); "
            "vertical axis: P = exp(−|ΔH/H|). 5 colours = the five transitions of the heartbeat.")
    s = (HERE / "ska_ecg_vr_template.html").read_text(encoding="utf-8")
    s = s.replace("__DATA__", json.dumps(D, separators=(",", ":"), ensure_ascii=False))
    s = s.replace("__DESCRIPTION__", desc)
    OUT.mkdir(exist_ok=True)
    out = OUT / f"ska_ecg_{rec}_scale{scale:g}_vr.html"
    out.write_text(s, encoding="utf-8")
    print(f"saved {out}  ({len(d):,} steps)")


if __name__ == "__main__":
    main()
