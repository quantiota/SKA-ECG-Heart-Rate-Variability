# SKA learning on the ECG event stream — results

**What the SKA learner does with the five waves of the heartbeat, in thirty women aged 18 to 92.**

This folder holds the **results** of the SKA engine: the learner's output for every step,
and the figures. The engine code is not published. The data it reads is reproducible from
the two phase-1 folders: [`ecg-data-validation/`](../ecg-data-validation/) (the collected
stream `ecg_steps`) and [`complex-events/`](../complex-events/) (the phasors and the input).

The women are 30 records of the PhysioNet
[Autonomic Aging database](https://physionet.org/content/autonomic-aging-cardiovascular/1.0.0/),
lead ECG1, 1000 Hz.

---

## The question

Each beat has five waves, P → Q → R → S → T, so a normal heart has five transitions:
P→Q, Q→R, R→S, S→T, T→P. **Does the learner, reading one number per wave, find these five
states on its own?** If it does, the phasor construction of `complex-events/` carries the
structure of the beat.

## The input

For each wave n, its phasor c_n (see [`complex-events/aging/README.md`](../complex-events/aging/README.md)),
then the return and the input:

$$
\dot c_n = c_n - c_{n-1}, \qquad
x_n = \frac{1}{1 + e^{-s\, u_n}}
$$

| input | u_n |
|---|---|
| `cdot_cos` | Re ċ_n — cosine |
| `cdot_sin` | Im ċ_n — sine |
| `cdot_cossin` | Re ċ_n + Im ċ_n — cosine + sine |

with **s** the scale (per mV). One step is one wave, five steps per beat. Each run is one
loop of **3,500 steps = 700 beats**, the size limit of the learner's matrix. The time between
steps is the real time between the peaks of successive waves.

## The learner's 3D space

Three quantities per step, all in the run CSVs (P and ż computed from the learner's output):

| | definition |
|---|---|
| **H** | the learner's entropy (`entropy`) |
| **P** | the transition probability, P = exp(−\|ΔH / H\|) |
| **z, ż** | the knowledge z = ‖Z‖ (`knowledge`) and its rate ż = dz/dt, per second — central difference `np.gradient(z) / Δt` as in the genomic engine (`zdot`), or backward difference Δz / Δt (`zdot_back`) |

(z, ż, P) is the learner's own 3D space. A state of the heart is **found** when its
transition forms its own band there.

## Record 0060: choosing the input

A woman aged 18–19, 15 minutes, 1,085 beats. Nine runs: the three inputs × scales 5, 25
and 50, figures in [`results/0060/figures/`](results/0060/figures/). The cosine is the input
kept for the thirty women.

## Thirty women

The 30 women of [`ecg-data-validation/records.txt`](../ecg-data-validation/records.txt), two
per age band from 18 to 92, lead ECG1, 1000 Hz. Cosine input. Each of the other 29 women
starts at scale 25; the scale is then set by hand, one woman at a time, from her figures.
One cube per woman: the steps of her selected run in (z, ż, P), one colour per transition.
It opens in a browser, or in a headset (WebXR).

| age | record | scale | cube |
|---|---|---|---|
| 18–19 | 0060 | 25 | [`ska_ecg_0060_scale25_vr.html`](vr/ska_ecg_0060_scale25_vr.html) |
| 18–19 | 0465 | 70 | [`ska_ecg_0465_scale70_vr.html`](vr/ska_ecg_0465_scale70_vr.html) |
| 20–24 | 1112 | 50 | [`ska_ecg_1112_scale50_vr.html`](vr/ska_ecg_1112_scale50_vr.html) |
| 20–24 | 0002 | 60 | [`ska_ecg_0002_scale60_vr.html`](vr/ska_ecg_0002_scale60_vr.html) |
| 25–29 | 0155 | 25 | [`ska_ecg_0155_scale25_vr.html`](vr/ska_ecg_0155_scale25_vr.html) |
| 25–29 | 0515 | 35 | [`ska_ecg_0515_scale35_vr.html`](vr/ska_ecg_0515_scale35_vr.html) |
| 30–34 | 1053 | 25 | [`ska_ecg_1053_scale25_vr.html`](vr/ska_ecg_1053_scale25_vr.html) |
| 30–34 | 0275 | 70 | [`ska_ecg_0275_scale70_vr.html`](vr/ska_ecg_0275_scale70_vr.html) |
| 35–39 | 0897 | 25 | [`ska_ecg_0897_scale25_vr.html`](vr/ska_ecg_0897_scale25_vr.html) |
| 35–39 | 0248 | 25 | [`ska_ecg_0248_scale25_vr.html`](vr/ska_ecg_0248_scale25_vr.html) |
| 40–44 | 0164 | 40 | [`ska_ecg_0164_scale40_vr.html`](vr/ska_ecg_0164_scale40_vr.html) |
| 40–44 | 0314 | 25 | [`ska_ecg_0314_scale25_vr.html`](vr/ska_ecg_0314_scale25_vr.html) |
| 45–49 | 0114 | 25 | [`ska_ecg_0114_scale25_vr.html`](vr/ska_ecg_0114_scale25_vr.html) |
| 45–49 | 0395 | 30 | [`ska_ecg_0395_scale30_vr.html`](vr/ska_ecg_0395_scale30_vr.html) |
| 50–54 | 0401 | 35 | [`ska_ecg_0401_scale35_vr.html`](vr/ska_ecg_0401_scale35_vr.html) |
| 50–54 | 0936 | 25 | [`ska_ecg_0936_scale25_vr.html`](vr/ska_ecg_0936_scale25_vr.html) |
| 55–59 | 0082 | 25 | [`ska_ecg_0082_scale25_vr.html`](vr/ska_ecg_0082_scale25_vr.html) |
| 55–59 | 0420 | 35 | [`ska_ecg_0420_scale35_vr.html`](vr/ska_ecg_0420_scale35_vr.html) |
| 60–64 | 0053 | 25 | [`ska_ecg_0053_scale25_vr.html`](vr/ska_ecg_0053_scale25_vr.html) |
| 60–64 | 0942 | 25 | [`ska_ecg_0942_scale25_vr.html`](vr/ska_ecg_0942_scale25_vr.html) |
| 65–69 | 0413 | 35 | [`ska_ecg_0413_scale35_vr.html`](vr/ska_ecg_0413_scale35_vr.html) |
| 65–69 | 0214 | 25 | [`ska_ecg_0214_scale25_vr.html`](vr/ska_ecg_0214_scale25_vr.html) |
| 70–74 | 0229 | 5 | [`ska_ecg_0229_scale5_vr.html`](vr/ska_ecg_0229_scale5_vr.html) |
| 70–74 | 0237 | 25 | [`ska_ecg_0237_scale25_vr.html`](vr/ska_ecg_0237_scale25_vr.html) |
| 75–79 | 0153 | 25 | [`ska_ecg_0153_scale25_vr.html`](vr/ska_ecg_0153_scale25_vr.html) |
| 75–79 | 0276 | 25 | [`ska_ecg_0276_scale25_vr.html`](vr/ska_ecg_0276_scale25_vr.html) |
| 80–84 | 0312 | 25 | [`ska_ecg_0312_scale25_vr.html`](vr/ska_ecg_0312_scale25_vr.html) |
| 80–84 | 0889 | 35 | [`ska_ecg_0889_scale35_vr.html`](vr/ska_ecg_0889_scale35_vr.html) |
| 85–92 | 0188 | 30 | [`ska_ecg_0188_scale30_vr.html`](vr/ska_ecg_0188_scale30_vr.html) |
| 85–92 | 0912 | 35 | [`ska_ecg_0912_scale35_vr.html`](vr/ska_ecg_0912_scale35_vr.html) |

## Limits

- **Thirty women**, healthy, one lead, 700 beats each. Nothing here is a result about hearts
  in general.
- **ż is partly timing.** ż divides the change of z by the time since the previous wave, and
  that time differs a lot by transition (≈ 30 ms for Q→R, several hundred for T→P). Part of
  the separation along ż comes from the timing of the beat, not from the input x.
- **z mostly counts steps.** The separation that matters is in P and ż.
- **The bands are transition bands.** P compares each step with the previous one, so a band
  is a passage between two successive waves, not a property of one value. The order
  P → Q → R → S → T is therefore part of what is learned: it is the structure of the beat.
- **The scale is in mV.** The amplitude of the waves is a characteristic of the person, so
  the same scale gives other people a narrower or wider input range. The ECG and the phasors
  stay raw; only the scale of the sigmoid has to be set for each person.

## Files

```
build_ecg_vr.py              fills the cube template with one run (record, scale)
ska_ecg_vr_template.html     the cube (Three.js), placeholders __DATA__ and __DESCRIPTION__
results/
└── <record>/                one folder per woman (30)
    ├── ska_<record>_runs.csv    every run of the record, one row per step
    └── figures/
vr/
└── ska_ecg_<record>_scale<s>_vr.html   one cube per woman, at her selected scale (30)
```

`figures/` holds, for each run, `ska_*` (H and P along the steps) and `bands3d_*` (the bands in
(z, ż, P)); the selected run ends in `_selected`.

To rebuild a cube:

```bash
python build_ecg_vr.py ska_ecg_vr_template.html results/0912/ska_0912_runs.csv 35 "85–92" vr/ska_ecg_0912_scale35_vr.html
```

## Data — `results/<record>/ska_<record>_runs.csv`

One row per step, 3,500 steps per run, ordered by input, scale and step. Record 0060 has the
9 runs above (31,500 rows); the other women have one cosine run per scale tried.

| column | meaning |
|---|---|
| `record_id`, `input`, `scale` | the run |
| `event`, `transition` | the wave (P, Q, R, S, T) and the transition into it |
| `event_index`, `k`, `peak` | step n = 5k + j, beat k, sample index of the wave's peak |
| `value_cos`, `value_sin` | Re c_n, Im c_n (mV); 0 when the wave is absent |
| `value_return` | u_n: Re ċ_n, Im ċ_n or their sum (mV) |
| `x_input` | x_n, what the learner reads |
| `rr` | the beat's duration (ms) |
| `knowledge` | z = ‖Z‖ |
| `decision`, `decision_norm` | the learner's last decision D and ‖D‖ |
| `entropy` | H |
| `delta_t` | time since the previous wave (s) |
| `cosine_similarity`, `delta_h_over_delta_d`, `frobenius_norm`, `matrix_size` | learner diagnostics |
| `P`, `zdot`, `zdot_back` | **computed at export**, not stored by the engine: P = exp(−\|ΔH/H\|) from `entropy`; ż from `knowledge` and `delta_t`, central (`zdot`) and backward (`zdot_back`) difference |
| `timestamp` | the wave's time in the recording |
