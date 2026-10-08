# SKA learning on the ECG event stream — results

[<img src="../ecg_thumbnail.png" width="1280" height="720"
/>](https://youtu.be/gYEbg5lCm6o)

*Record 0060, PhysioNet Autonomic Aging: a healthy woman aged 18–19, raw ECG at 1000 Hz, 700 beats. Each wave of the heartbeat (P, Q, R, S, T) becomes a phasor on a circle whose circumference is the beat's duration. The learner reads one number per wave, the cosine of the phasor's step from the previous wave. Without labels or rules about cardiology, it organises the five transitions of the heartbeat (P→Q, Q→R, R→S, S→T, T→P) into five separate, stable bands in its own space (z, ż, P), where z is knowledge, ż its flow and P the transition probability.

A normal heart has five transitions. An abnormal one should add new bands.*

**What the SKA learner does with the five waves of the heartbeat: nine runs on one person,
three inputs × three scales.**

This folder holds the **results** of the SKA engine: the learner's output for every step,
and the figures. The engine code is not published. The data it reads is reproducible from
the two phase-1 folders: [`ecg-data-validation/`](../ecg-data-validation/) (the collected
stream `ecg_steps`) and [`complex-events/`](../complex-events/) (the phasors and the input).

The person is **record 0060** of the PhysioNet Autonomic Aging database: a woman aged
18–19, lead ECG1, 1000 Hz, 15 minutes, 1,085 beats.

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

with **s = 5, 25 or 50** (per mV). One step is one wave, five steps per beat. Each run is one
loop of **3,500 steps = 700 beats**, the size limit of the learner's matrix. The time between
steps is the real time between the peaks of successive waves.

## What is measured

Three quantities per step, all in `ska_0060_runs.csv` (P and ż computed from the learner's output):

| | definition |
|---|---|
| **H** | the learner's entropy (`entropy`) |
| **P** | the transition probability, P = exp(−\|ΔH / H\|) |
| **z, ż** | the knowledge z = ‖Z‖ (`knowledge`) and its rate ż = dz/dt, per second — central difference `np.gradient(z) / Δt` as in the genomic engine (`zdot`), or backward difference Δz / Δt (`zdot_back`) |

(z, ż, P) is the learner's own 3D space. A state of the heart is **found** when its
transition forms its own band there.

## The nine runs

| input | scale | x at 0 or 1 | distinct H curves | P bands overlapping (d′ ≤ 3) | in (ż, P), ż central | in (ż, P), ż backward |
|---|---|---|---|---|---|---|
| cosine | 5 | 0 % | **5** | P→Q/T→P, P→Q/R→S, Q→R/S→T | **none** | **none** |
| cosine | 25 | 56 % | 3 | **none** | **none** | **none** |
| cosine | 50 | 80 % | 3 | P→Q/R→S | P→Q/R→S (1.8) | none |
| sine | 5 | 0 % | 4 | P→Q/T→P, Q→R/T→P, S→T/T→P | S→T/T→P (2.9) | none |
| sine | 25 | 40 % | 4 | 6 pairs | none | none |
| sine | 50 | 59 % | 3 | 4 pairs | none | P→Q/S→T (2.2) |
| cosine + sine | 5 | 0 % | **5** | 6 pairs | S→T/T→P (2.3) | S→T/T→P (1.1) |
| cosine + sine | 25 | 62 % | 3 | Q→R/T→P | none | none |
| cosine + sine | 50 | 79 % | 2 | Q→R/T→P | none | none |

Measured after step 500 (the learning phase). Two H curves count as one when their median
gap is under 3 % of their depth; two transitions overlap in (ż, P) when their Mahalanobis
distance is under 3. The (ż, P) result depends on how ż is taken on three rows; the
cosine at scales 5 and 25 separates all five under both definitions. Leaving out the 9 beats
without S changes none of the rows.

Mean P per transition:

| input | scale | P→Q | Q→R | R→S | S→T | T→P |
|---|---|---|---|---|---|---|
| cosine | 5 | 0.56 | 0.74 | 0.46 | 0.82 | 0.57 |
| cosine | 25 | 0.14 | 0.52 | 0.02 | 0.95 | 0.44 |
| cosine | 50 | 0.03 | 0.46 | 0.01 | 1.00 | 0.44 |
| sine | 5 | 0.89 | 0.74 | 0.30 | 0.64 | 0.72 |
| sine | 25 | 0.67 | 0.61 | 0.02 | 0.46 | 0.20 |
| sine | 50 | 0.62 | 0.56 | 0.02 | 0.45 | 0.09 |
| cosine + sine | 5 | 0.59 | 0.65 | 0.11 | 0.72 | 0.64 |
| cosine + sine | 25 | 0.09 | 0.49 | 0.01 | 0.91 | 0.45 |
| cosine + sine | 50 | 0.01 | 0.44 | 0.01 | 0.99 | 0.44 |

## What it shows

- **The five states emerge.** With the cosine input, the learner separates all five
  transitions: in H at scale 5 (five distinct curves), in P at scale 25 (five bands, no
  pair overlapping), and in the (ż, P) plane at both, whichever way ż is taken.
- **The scale trades H against P.** At low scale the input keeps its full range and H keeps
  the five states apart. At higher scale the input becomes almost binary: H merges the
  transitions that land on the same edge (Q→R with T→P at x ≈ 1, R→S with S→T at x ≈ 0),
  while P — which compares each step with the previous one — sharpens into thin bands.
  At 50 P starts merging again.
- **The cosine carries the most.** The sine merges the transitions around the T wave at
  every scale; the sum of cosine and sine is not better than the cosine alone.
- **The learner registers a change of state by itself.** Around step 3,270 (beat 654, minute
  9) the R→S band shifts in the scale-5 runs: P rises from 0.29 to 0.32 with the sine, and
  from 0.104 to 0.111 with cosine + sine. The same beat is where the rhythm slows (mean RR
  818 ms over beats 550–649, 848 ms over beats 654–700, the end of the run) and where the
  phasors step in `complex-events/` (figures 6 and 8).

## Limits

- **One person**, healthy, 15 minutes. Nothing here is a result about hearts in general.
- **ż is partly timing.** ż divides the change of z by the time since the previous wave, and
  that time differs a lot by transition (≈ 30 ms for Q→R, several hundred for T→P). Part of
  the separation along ż comes from the timing of the beat, not from the input x.
- **z mostly counts steps**: it grows with the size of the matrix. The separation that
  matters is in P and ż.
- **9 beats of 1,085 have no S wave** (see `complex-events/`); they are the few points away
  from their bands.
- **The bands are transition bands.** P compares each step with the previous one, so a band
  is a passage between two successive waves, not a property of one value. The order
  P → Q → R → S → T is therefore part of what is learned: it is the structure of the beat.
  In pathology that order breaks, and new transitions should appear as new bands.
- **The scale is in mV and fixed.** On other people the same scale gives a narrower or wider
  input range (see `x_min`, `x_max` in `complex-events/aging/summary_all.csv`).

## Next test

**Other women, same dataset.** The other 29 women already collected in phase 1 —
PhysioNet [Autonomic Aging database](https://physionet.org/content/autonomic-aging-cardiovascular/1.0.0/),
the records listed in [`ecg-data-validation/records.txt`](../ecg-data-validation/records.txt),
two per age band from 18 to 92, lead ECG1, 1000 Hz, already in `ecg_steps`. Same inputs and
scales as here. The question: do the five bands emerge for every healthy heart, and do they
move with age?

## Figures — `results/0060/figures/`

For each input (`cdot_cos`, `cdot_sin`, `cdot_cossin`); no suffix = scale 5, `_scale25`,
`_scale50`:

| file | shows |
|---|---|
| `ska_0060_<input>[_scaleN].png` | H (top) and P (bottom) along the step index, coloured by transition |
| `bands3d_0060_<input>[_scaleN].png` | the bands in the learner's space (z, ż, P) |
| `bands3d_0060_compare[_scaleN].png` | the three inputs side by side in (z, ż, P) |

21 figures: 9 + 9 + 3.

## Data — `results/0060/ska_0060_runs.csv`

One row per step, 9 runs × 3,500 steps = 31,500 rows, ordered by input, scale and step.

| column | meaning |
|---|---|
| `record_id`, `input`, `scale` | the run |
| `event`, `transition` | the wave (P, Q, R, S, T) and the transition into it |
| `event_index`, `k`, `peak` | step n = 5k + j, beat k, sample index of the wave's peak |
| `value_cos`, `value_sin` | Re c_n, Im c_n (mV) |
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
