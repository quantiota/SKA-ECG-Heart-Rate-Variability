"""
Entropic characteristic time of the heart: the total learning time (arXiv:2504.03214, §2.2, T = η × K)
until the entropy is 90 % saturated.

The learner's time step is Δt_k, the real time between waves k−1 and k (ska_core.py updates W with
−Δt_k × 1e-7 × gradient). The total time is therefore the sum of the steps:

    tau_H = Σ_{k ≤ K} Δt_k = ∫_0^{t_K} dt = t_K       (seconds; also given in minutes)

    K    = the step (wave) where the entropy is 90 % saturated: for each transition, the first step after the
           entropy minimum where |H| ≤ 10 % of |H_min|; the heart is saturated when its slowest transition is.

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
        d = pd.read_csv(folder / f"ska_{rec}_runs.csv",
                        usecols=["input", "scale", "transition", "event_index", "entropy", "delta_t"])
        d = d[(d.input == "cdot_cos") & (d.scale == scale)].sort_values("event_index").reset_index(drop=True)
        if d.empty:
            raise SystemExit(f"{rec}: no rows for input=cdot_cos scale={scale:g}")
        t = d.delta_t.fillna(0).cumsum()                       # ∫ dt: real time since the first wave (s)
        row = dict(record=rec, selected="yes" if sel is not None else "no", scale=scale)
        K = {}
        for tr, g in d.dropna(subset=["entropy"]).groupby("transition"):
            H = g.entropy.values
            i0 = H.argmin()
            hit = np.flatnonzero(np.abs(H[i0:]) <= (1 - SATURATION) * abs(H[i0]))
            K[tr] = g.index[i0 + hit[0]] if len(hit) else None
            row[f"tau_{tr}_s"] = t[K[tr]] if K[tr] is not None else np.nan
        slow = max(TRANSITIONS, key=lambda tr: -1 if K[tr] is None else K[tr])
        row.update(tau_H_s=row[f"tau_{slow}_s"], tau_H_min=row[f"tau_{slow}_s"] / 60, slowest=slow, K=int(K[slow]) + 1,
                   waves=len(d))
        rows.append(row)
    o = pd.DataFrame(rows)
    o.to_csv(out, index=False, float_format="%.1f")
    print(o.to_string(index=False))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
