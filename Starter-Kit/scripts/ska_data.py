"""Shared loader: one SKA run (record, scale) from data/ecg_ska_results.csv.gz, with P and ż.

    P = exp(−|ΔH/H|)   from the entropy H of two successive steps
    ż = dz/dt          central difference of z = ‖Z‖ (knowledge), dt = delta_t
"""
import pathlib

import numpy as np
import pandas as pd

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
NAMES = ["P→Q", "Q→R", "R→S", "S→T", "T→P"]
COLORS = ["#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#3987e5"]


def load_run(rec, scale_arg, inp="cdot_cos"):
    """Return (steps, scale, age band). scale_arg: a number, or 'selected'."""
    sel = pd.read_csv(DATA / "selected_scales.csv", dtype={"record_id": str}).set_index("record_id")
    if rec not in sel.index:
        raise SystemExit(f"unknown record {rec}; records: {' '.join(sel.index)}")
    scale = float(sel.loc[rec, "scale"]) if scale_arg == "selected" else float(scale_arg)
    d = pd.read_csv(DATA / "ecg_ska_results.csv.gz", dtype={"record_id": str})
    d = d[(d.record_id == rec) & (d.input == inp) & (d.scale == scale)].sort_values("event_index")
    if d.empty:
        have = sorted(pd.read_csv(DATA / "ecg_ska_results.csv.gz", dtype={"record_id": str})
                      .query("record_id == @rec and input == @inp").scale.unique())
        raise SystemExit(f"no run for {rec} at scale {scale:g}; scales run: {', '.join(f'{s:g}' for s in have)}")
    d = d.reset_index(drop=True)
    H = d.entropy.to_numpy(float)
    P = np.full(len(d), np.nan)
    P[1:] = np.exp(-np.abs(np.diff(H) / H[1:]))
    d["P"] = P
    d["zdot"] = np.gradient(d.knowledge.to_numpy(float)) / d.delta_t.to_numpy(float)
    d["tr"] = d.transition.str.replace("-", "→")
    d = d.dropna(subset=["P", "zdot"]).reset_index(drop=True)
    return d, scale, sel.loc[rec, "age_band"].replace("-", "–")
