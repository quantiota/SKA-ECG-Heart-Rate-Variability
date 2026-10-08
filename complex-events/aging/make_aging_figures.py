#!/usr/bin/env python3
"""Reproduce the complex-events figures on an Autonomic Aging record.

The construction is ska_complex_events.py, imported unchanged (same_sign_arc,
complex_events). Beats are located with detect_beats.detect_robust(), which finds them on
a cleaned copy and keeps every measurement on the raw signal. The signal is lead ECG1 of an Autonomic Aging record, first 15 minutes,
in mV, read with ecg-data-validation/ecg_chain.py.

    python make_aging_figures.py 0060
"""
import itertools
import pathlib
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent / "ecg-data-validation"))
from ska_complex_events import same_sign_arc, complex_events   # unchanged
from detect_beats import detect_robust   # beats found on a cleaned copy, measured raw
from ecg_chain import ECGRecord, read_subjects, AGE_BANDS

INK = "#1f1f1d"; MUTE = "#6b6a63"; GRID = "#e6e5df"; BG = "#fcfcfb"
C = dict(zip("PQRST", ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
TR = ["P→Q", "Q→R", "R→S", "S→T", "T→P"]; CT = {t: C[t[-1]] for t in TR}


def style(a, ygrid=True):
    a.set_facecolor(BG); a.tick_params(colors=MUTE); a.set_axisbelow(True)
    if ygrid:
        a.grid(axis="y", color=GRID, lw=.6)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        a.spines[s].set_color(GRID)


def head(fig, t, sub):
    fig.suptitle(t, x=0.04, ha="left", color=INK, fontsize=14, fontweight="bold")
    fig.text(0.04, 0.915, sub, color=MUTE, fontsize=9.5)


def load_from_db(rid):
    """The record's samples as collected in QuestDB (ecg_steps), in mV, in order."""
    import psycopg2
    from config import QDB_CONFIG
    conn = psycopg2.connect(**QDB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT value FROM ecg_steps WHERE record_id = %s ORDER BY sample_index;", (rid,))
    x = np.array([r[0] for r in cur.fetchall()], dtype=float)
    conn.close()
    if x.size != 900_000:
        raise SystemExit(f"{rid}: {x.size:,} samples in ecg_steps, expected 900,000")
    return x


def main(rid, quiet=False):
    data = HERE.parent.parent / "ecg-data-validation" / "data"
    subj = read_subjects(data)[rid]
    band = AGE_BANDS[int(subj["Age_group"])]
    sex = {"0": "man", "1": "woman"}[subj["Sex"]]
    x = load_from_db(rid)
    beats = detect_robust(x)
    d = complex_events(x, beats)
    e = d.dropna(subset=["cdot_cos"])
    src = f"Autonomic Aging {rid} ({sex}, {band}), ECG1, 15 min, from ecg_steps"
    out = HERE / "figures" / rid
    out.mkdir(parents=True, exist_ok=True)
    d.to_csv(HERE / f"complex_events_{rid}.csv", index=False)

    # fig2: detection on the raw ECG, first 3 beats
    fig, ax = plt.subplots(figsize=(15, 5), facecolor=BG); style(ax)
    lo, hi = beats[0][0]["P"] - 250, beats[3][0]["P"] + 50
    ax.plot(np.arange(lo, hi), x[lo:hi], color=INK, lw=1)
    for ev, base in beats[:3]:
        xb = x - base
        ax.plot([ev["P"] - 250, ev["T"] + 300], [base, base], color=MUTE, lw=.6, ls=":")
        for n, pk in ev.items():
            a, b = same_sign_arc(xb, pk, pk - 150, pk + 250)
            ax.fill_between(np.arange(a, b), base, x[a:b], color=C[n], alpha=.35, lw=0)
            ax.scatter([pk], [x[pk]], color=C[n], s=30, zorder=3)
            ax.annotate(n, (pk, x[pk]), xytext=(0, 7 if xb[pk] > 0 else -14),
                        textcoords="offset points", ha="center", color=INK, fontsize=10,
                        fontweight="bold")
    ax.set_xlabel("sample index (1 ms)", color=MUTE); ax.set_ylabel("ECG (mV)", color=MUTE)
    head(fig, "Event detection on the raw ECG — peaks and base arcs",
         f"Shaded = base arc of each event, against the per-beat baseline (dotted). {src}, "
         f"first 3 beats.")
    fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(out / "fig2_detection_real.png", dpi=150,
                                                      facecolor=BG); plt.close()

    # fig4: z per event in the complex plane
    fig, ax = plt.subplots(figsize=(9, 8.4), facecolor=BG); style(ax, False)
    ax.grid(color=GRID, lw=.6); ax.axhline(0, color=MUTE, lw=.6); ax.axvline(0, color=MUTE, lw=.6)
    for n in "PQRST":
        m = d.event == n
        ax.scatter(d.c_cos[m], d.c_sin[m], s=8, color=C[n], lw=0, label=n, alpha=.6)
        ax.annotate(n, (d.c_cos[m].mean(), d.c_sin[m].mean()), xytext=(10, 0),
                    textcoords="offset points", color=INK, fontsize=12, fontweight="bold",
                    va="center")
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("cosine  Re c_j  (mV)", color=MUTE); ax.set_ylabel("sine  Im c_j  (mV)", color=MUTE)
    ax.legend(frameon=False, ncol=5, loc="lower right", bbox_to_anchor=(1, 1.0), labelcolor=INK)
    head(fig, "Each event is a cluster in the complex plane",
         f"c_j for {d.k.nunique():,} beats × 5 events. {src}.")
    fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(out / "fig4_c_complex_plane.png", dpi=150,
                                                      facecolor=BG); plt.close()

    # fig5: cosine and sine of z along the event index
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(15, 8), sharex=True, facecolor=BG)
    for a, col, lab in ((a1, "c_cos", "cosine  Re c_j"), (a2, "c_sin", "sine  Im c_j")):
        style(a); a.axhline(0, color=MUTE, lw=.6)
        for n in "PQRST":
            m = d.event == n
            a.scatter(d.event_index[m], d[col][m], s=4, color=C[n], lw=0, label=n)
        a.set_ylabel(f"{lab}  (mV)", color=MUTE)
    a1.legend(ncol=5, frameon=False, loc="lower right", bbox_to_anchor=(1, 1.0), labelcolor=INK,
              markerscale=3)
    a2.set_xlabel("event index n = 5k + j", color=MUTE)
    head(fig, "The beat repeats the same five levels along the event index",
         f"Cosine and sine of c_j, colour = event. {src}, {len(d):,} events.")
    fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(out / "fig5_c_event_index.png", dpi=150,
                                                      facecolor=BG); plt.close()

    # fig6: cosine and sine of c-dot along the event index
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(15, 8), sharex=True, facecolor=BG)
    for a, col, lab in ((a1, "cdot_cos", "cosine  Re ċ"), (a2, "cdot_sin", "sine  Im ċ")):
        style(a); a.axhline(0, color=MUTE, lw=.6)
        for tr in TR:
            m = e.transition == tr
            a.scatter(e.event_index[m], e[col][m], s=4, color=CT[tr], lw=0, label=tr)
        a.set_ylabel(f"{lab}  (mV)", color=MUTE)
    a1.legend(ncol=5, frameon=False, loc="lower right", bbox_to_anchor=(1, 1.0), labelcolor=INK,
              markerscale=3)
    a2.set_xlabel("event index n = 5k + j", color=MUTE)
    head(fig, "Candidate learner inputs: cosine and sine of ċ along the event index",
         f"ċ_n = c_n − c_(n−1), colour = transition. {src}, {len(e):,} transitions.")
    fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(out / "fig6_cdot_event_index.png", dpi=150,
                                                      facecolor=BG); plt.close()

    # fig7: levels per input, and the plane
    def dprime(col, a, b):
        u, v = e[e.transition == a][col], e[e.transition == b][col]
        return abs(u.mean() - v.mean()) / np.sqrt((u.var() + v.var()) / 2)

    fig = plt.figure(figsize=(15, 6.6), facecolor=BG)
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.25])
    rng = np.random.default_rng(0)
    summary = {}
    for i, (col, lab) in enumerate((("cdot_cos", "cosine  Re ċ"), ("cdot_sin", "sine  Im ċ"))):
        a = fig.add_subplot(gs[i]); style(a)
        for tr in TR:
            v = e[col][e.transition == tr]
            a.scatter(rng.uniform(-.35, .35, len(v)), v, s=4, color=CT[tr], lw=0, alpha=.6)
            a.annotate(tr, (0.42, v.mean()), xytext=(4, 0), textcoords="offset points",
                       va="center", fontsize=9.5, color=INK)
        merged = [(p, q) for p, q in itertools.combinations(TR, 2) if dprime(col, p, q) <= 3]
        summary[col] = merged
        a.set_xlim(-.5, 1.3); a.set_xticks([]); a.set_ylabel(f"{lab}  (mV)", color=MUTE)
        a.set_title(f"{'cosine' if i == 0 else 'sine'} alone: "
                    f"{len(merged)} overlapping pair{'s' if len(merged) != 1 else ''} (d′ ≤ 3)"
                    + ("\n" + "; ".join(f"{p} / {q}" for p, q in merged) if merged else ""),
                    loc="left", color=INK, fontsize=11)
    a = fig.add_subplot(gs[2]); style(a, False); a.grid(color=GRID, lw=.6)
    a.axhline(0, color=MUTE, lw=.6); a.axvline(0, color=MUTE, lw=.6)
    for tr in TR:
        m = e.transition == tr
        a.scatter(e.cdot_cos[m], e.cdot_sin[m], s=4, color=CT[tr], lw=0, alpha=.6)
        a.annotate(tr, (e.cdot_cos[m].mean(), e.cdot_sin[m].mean()), xytext=(8, 6),
                   textcoords="offset points", fontsize=10, color=INK)
    best = min((np.sqrt((lambda X, Y: (X.mean(0) - Y.mean(0)) @ np.linalg.solve(
        (np.cov(X.T) + np.cov(Y.T)) / 2, X.mean(0) - Y.mean(0)))(
        e[e.transition == p][["cdot_cos", "cdot_sin"]].values,
        e[e.transition == q][["cdot_cos", "cdot_sin"]].values)), p, q)
        for p, q in itertools.combinations(TR, 2))
    a.set_xlabel("cosine  Re ċ (mV)", color=MUTE); a.set_ylabel("sine  Im ċ (mV)", color=MUTE)
    a.set_title(f"cosine + sine together: smallest separation {best[0]:.1f}\n"
                f"(Mahalanobis, {best[1]} vs {best[2]})", loc="left", color=INK, fontsize=11)
    head(fig, "Which input separates the five transitions?",
         f"Each dot = one transition ċ_n. {src}, {d.k.nunique():,} beats.")
    fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(out / "fig7_cdot_levels.png", dpi=150,
                                                      facecolor=BG); plt.close()

    # fig8: |Z| and RR per beat — two panels, one axis each
    Ck = d.assign(c=d.c_cos + 1j * d.c_sin).groupby("k").agg(C=("c", "sum"), RR=("RR", "first"),
                                                            r=("r", "first"))
    rho = np.corrcoef(np.abs(Ck.C), Ck.RR)[0, 1]
    rho_r = np.corrcoef(np.abs(Ck.C) * Ck.r, Ck.RR)[0, 1]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(15, 7), sharex=True, facecolor=BG)
    style(a1); style(a2)
    a1.plot(Ck.index, np.abs(Ck.C), color="#1baf7a", lw=.8); a1.set_ylabel("|C_k|  (mV)", color=MUTE)
    a2.plot(Ck.index, Ck.RR, color=INK, lw=.8); a2.set_ylabel("RR  (ms)", color=MUTE)
    a2.set_xlabel("cycle index k", color=MUTE)
    head(fig, f"|C_k| follows the rhythm — corr(|C|, RR) = {rho:+.2f}",
         f"{rho_r:+.2f} with the 1/r prefactor removed (|C|·r). {src}.")
    fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(out / "fig8_absC_RR.png", dpi=150,
                                                      facecolor=BG); plt.close()

    summary_row = dict(record=rid, age=band, beats=d.k.nunique(), RR=float(Ck.RR.median()),
                       cos_overlaps=len(summary["cdot_cos"]), sin_overlaps=len(summary["cdot_sin"]),
                       maha=float(best[0]), maha_pair=f"{best[1]} / {best[2]}",
                       rho=float(rho), rho_r=float(rho_r))
    if quiet:
        return summary_row
    # the tables
    print(f"{src}: {d.k.nunique():,} beats, {len(d):,} events, RR {Ck.RR.median():.0f} ms "
          f"({Ck.RR.min()}–{Ck.RR.max()})")
    print("\nc_j per event (mV)          cosine            sine")
    for n in "PQRST":
        m = d[d.event == n]
        print(f"  {n}                     {m.c_cos.mean():+.3f} ± {m.c_cos.std():.3f}   "
              f"{m.c_sin.mean():+.3f} ± {m.c_sin.std():.3f}")
    print("\nċ per transition (mV)       cosine            sine")
    for tr in TR:
        m = e[e.transition == tr]
        print(f"  {tr}  n={len(m):5d}      {m.cdot_cos.mean():+.3f} ± {m.cdot_cos.std():.3f}   "
              f"{m.cdot_sin.mean():+.3f} ± {m.cdot_sin.std():.3f}")
    for col in ("cdot_cos", "cdot_sin"):
        print(f"\n{col}: overlapping pairs (d' <= 3): "
              f"{', '.join(f'{p}/{q} ({dprime(col, p, q):.2f})' for p, q in summary[col]) or 'none'}")
    print(f"smallest 2D Mahalanobis {best[0]:.1f} ({best[1]} vs {best[2]})")
    print(f"corr(|C|, RR) {rho:+.2f}   with 1/r removed {rho_r:+.2f}")
    print(f"figures -> {out}")
    return summary_row


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        from ecg_chain import read_records
        ids = read_records(HERE.parent.parent / "ecg-data-validation" / "records.txt")
        rows = []
        for rid in ids:
            rows.append(main(rid, quiet=True))
            r = rows[-1]
            print(f"  {r['record']}  {r['age']:6s} {r['beats']:5d} beats  RR {r['RR']:5.0f} ms  "
                  f"overlaps cos {r['cos_overlaps']} sin {r['sin_overlaps']}  "
                  f"Mahalanobis {r['maha']:5.1f} ({r['maha_pair']})  "
                  f"corr(|C|,RR) {r['rho']:+.2f} / {r['rho_r']:+.2f}", flush=True)
        import csv
        with open(HERE / "summary_all.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        print(f"summary -> {HERE / 'summary_all.csv'}")
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else "0060")
