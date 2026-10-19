"""
Entropic characteristic time of the heart: tau_H = eta × K (arXiv:2504.03214, §2.2, T = η × K).

    eta  = 0.001 (1 ms)
    K    = the number of SKA steps (waves) until the entropy is 90 % saturated:
           for each transition, the first step after the entropy minimum where |H| ≤ 10 % of |H_min|;
           the heart is saturated when its slowest transition is.

Each record is read at its selected scale (the figure results/<record>/figures/ska_<record>_cdot_cos_scale<S>_selected.png;
no scale in the name = scale 5), or at scale 25 when no scale was selected. Input cdot_cos.

Usage
    python tau_h.py results results/tau_H.csv
Requires: numpy, pandas
"""
import pathlib
import re
import sys

import numpy as np
import pandas as pd

ETA = 0.001
SATURATION = 0.9
TRANSITIONS = ["P-Q", "Q-R", "R-S", "S-T", "T-P"]


def selected_scale(folder):
    for f in (folder / "figures").glob("ska_*_cdot_cos*_selected.png"):
        m = re.search(r"_scale(\d+)_selected", f.name)
        return float(m.group(1)) if m else 5.0
    return None


def main():
    results, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    rows = []
    for folder in sorted(p for p in results.iterdir() if p.is_dir() and p.name.isdigit()):
        rec = folder.name
        sel = selected_scale(folder)
        scale = sel if sel is not None else 25.0
        d = pd.read_csv(folder / f"ska_{rec}_runs.csv", usecols=["input", "scale", "transition", "event_index", "entropy"])
        d = d[(d.input == "cdot_cos") & (d.scale == scale)].dropna(subset=["entropy"]).sort_values("event_index")
        if d.empty:
            raise SystemExit(f"{rec}: no rows for input=cdot_cos scale={scale:g}")
        row = dict(record=rec, selected="yes" if sel is not None else "no", scale=scale)
        for tr, g in d.groupby("transition"):
            H, k = g.entropy.values, g.event_index.values
            i0 = H.argmin()
            hit = np.flatnonzero(np.abs(H[i0:]) <= (1 - SATURATION) * abs(H[i0]))
            row[f"tau_{tr}"] = ETA * k[i0 + hit[0]] if len(hit) else np.nan
        taus = [row[f"tau_{t}"] for t in TRANSITIONS]
        row["tau_H"] = max(taus)
        row["slowest"] = TRANSITIONS[int(np.nanargmax(taus))]
        row["waves"] = int(d.event_index.max())
        rows.append(row)
    o = pd.DataFrame(rows)
    o.to_csv(out, index=False, float_format="%.3f")
    print(o.to_string(index=False))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
