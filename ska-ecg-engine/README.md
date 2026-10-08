# SKA learning on the ECG event stream — results


[<img src="../ecg_thumbnail.png" width="1280" height="720"
/>](https://youtu.be/gYEbg5lCm6o)

* Record 0060, PhysioNet Autonomic Aging: a healthy woman aged 18–19, raw ECG at 1000 Hz, 700 beats. Each wave of the heartbeat (P, Q, R, S, T) becomes a phasor on a circle whose circumference is the beat's duration. The learner reads one number per wave, the cosine of the phasor's step from the previous wave. Without labels or rules about cardiology, it organises the five transitions of the heartbeat (P→Q, Q→R, R→S, S→T, T→P) into five separate, stable bands in its own space (z, ż, P), where z is knowledge, ż its flow and P the transition probability.

A normal heart has five transitions. An abnormal one should add new bands.*



**What the SKA learner does with the five waves of the heartbeat: nine runs on one person
(three inputs × three scales), then each of 30 women at a fixed scale and at her own scale.**

This folder holds the **results** of the SKA engine: the learner's output for every step,
and the figures. The engine code is not published. The data it reads is reproducible from
the two phase-1 folders: [`ecg-data-validation/`](../ecg-data-validation/) (the collected
stream `ecg_steps`) and [`complex-events/`](../complex-events/) (the phasors and the input).

The people are the 30 women of the PhysioNet
[Autonomic Aging database](https://physionet.org/content/autonomic-aging-cardiovascular/1.0.0/)
selected in phase 1 ([`ecg-data-validation/records.txt`](../ecg-data-validation/records.txt)):
two per age band from 18 to 92, lead ECG1, 1000 Hz, 15 minutes each. The first, **record
0060** (aged 18–19, 1,085 beats), was studied in detail.

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

Three quantities per step, all in the run CSVs (P and ż computed from the learner's output):

| | definition |
|---|---|
| **H** | the learner's entropy (`entropy`) |
| **P** | the transition probability, P = exp(−\|ΔH / H\|) |
| **z, ż** | the knowledge z = ‖Z‖ (`knowledge`) and its rate ż = dz/dt, per second — central difference `np.gradient(z) / Δt` as in the genomic engine (`zdot`), or backward difference Δz / Δt (`zdot_back`) |

(z, ż, P) is the learner's own 3D space. A state of the heart is **found** when its
transition forms its own band there.

## Record 0060: nine runs

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

## All 30 women: cosine, scale 25

One run per woman, input `cdot_cos`, scale 25, 3,500 steps — the setting that gave five
separate P bands on 0060. Same measures as above. The table is
[`results/scale25/summary_scale25_cos.csv`](results/scale25/summary_scale25_cos.csv).

| record | age | x at 0 or 1 | distinct H curves | P bands overlapping | in (ż, P), ż central | in (ż, P), ż backward |
|---|---|---|---|---|---|---|
| 0060 | 18-19 | 56 % | 3 | **none** | **none** | **none** |
| 0465 | 18-19 | 37 % | 4 | 5 pairs | S→T/T→P | S→T/T→P |
| 1112 | 20-24 | 23 % | 4 | 6 pairs | P→Q/R→S, S→T/T→P | S→T/T→P |
| 0002 | 20-24 | 1 % | 3 | 3 pairs | **none** | P→Q/T→P |
| 0155 | 25-29 | 56 % | 3 | **none** | **none** | **none** |
| 0515 | 25-29 | 56 % | 3 | P→Q/R→S, Q→R/S→T | P→Q/R→S | **none** |
| 0612 | 30-34 | 0 % | 1 | P→Q/R→S, Q→R/T→P | P→Q/R→S | **none** |
| 0275 | 30-34 | 39 % | 4 | 7 pairs | P→Q/R→S, R→S/S→T, S→T/T→P | P→Q/R→S |
| 0897 | 35-39 | 1 % | 5 | 7 pairs | P→Q/S→T, Q→R/R→S, S→T/T→P | Q→R/R→S |
| 0248 | 35-39 | 36 % | 3 | P→Q/R→S | P→Q/R→S | **none** |
| 0164 | 40-44 | 39 % | 3 | 3 pairs | P→Q/R→S | P→Q/R→S |
| 0314 | 40-44 | 35 % | 2 | P→Q/R→S | P→Q/R→S | P→Q/R→S |
| 0114 | 45-49 | 5 % | 3 | 7 pairs | P→Q/R→S, Q→R/R→S, S→T/T→P | P→Q/R→S, Q→R/R→S, S→T/T→P |
| 0395 | 45-49 | 27 % | 4 | 6 pairs | P→Q/R→S, Q→R/R→S, S→T/T→P | Q→R/R→S |
| 0401 | 50-54 | 50 % | 2 | 4 pairs | P→Q/R→S, S→T/T→P | P→Q/R→S |
| 0936 | 50-54 | 17 % | 4 | 8 pairs | P→Q/S→T, Q→R/R→S, S→T/T→P | Q→R/R→S |
| 0082 | 55-59 | 15 % | 5 | 7 pairs | P→Q/R→S, R→S/S→T, S→T/T→P | P→Q/R→S |
| 0420 | 55-59 | 36 % | 4 | 3 pairs | P→Q/R→S, S→T/T→P | P→Q/R→S |
| 0053 | 60-64 | 4 % | 3 | P→Q/R→S, Q→R/T→P | P→Q/R→S | **none** |
| 0942 | 60-64 | 5 % | 4 | 5 pairs | **none** | S→T/T→P |
| 0413 | 65-69 | 0 % | 3 | 7 pairs | P→Q/R→S, S→T/T→P | S→T/T→P |
| 0214 | 65-69 | 2 % | 2 | P→Q/S→T, Q→R/T→P | P→Q/S→T | P→Q/S→T |
| 0229 | 70-74 | 36 % | 5 | 6 pairs | P→Q/S→T, Q→R/R→S, R→S/S→T, R→S/T→P, S→T/T→P | Q→R/R→S, R→S/S→T, R→S/T→P, S→T/T→P |
| 0237 | 70-74 | 8 % | 4 | 7 pairs | P→Q/R→S, Q→R/R→S, R→S/S→T, S→T/T→P | P→Q/R→S, Q→R/R→S |
| 0153 | 75-79 | 39 % | 4 | Q→R/S→T | **none** | **none** |
| 0276 | 75-79 | 0 % | 3 | 6 pairs | P→Q/Q→R, P→Q/S→T, S→T/T→P | P→Q/S→T, S→T/T→P |
| 0312 | 80-84 | 1 % | 4 | 7 pairs | S→T/T→P | S→T/T→P |
| 0249 | 80-84 | 0 % | 1 | P→Q/R→S, Q→R/T→P | **none** | **none** |
| 0188 | 85-92 | 5 % | 4 | 8 pairs | Q→R/S→T, S→T/T→P | P→Q/T→P, S→T/T→P |
| 0323 | 85-92 | 0 % | 3 | 3 pairs | **none** | S→T/T→P |

Mean P per transition:

| record | age | P→Q | Q→R | R→S | S→T | T→P |
|---|---|---|---|---|---|---|
| 0060 | 18-19 | 0.14 | 0.52 | 0.02 | 0.94 | 0.44 |
| 0465 | 18-19 | 0.20 | 0.56 | 0.14 | 0.61 | 0.44 |
| 1112 | 20-24 | 0.33 | 0.62 | 0.15 | 0.67 | 0.45 |
| 0002 | 20-24 | 0.46 | 0.64 | 0.10 | 0.84 | 0.52 |
| 0155 | 25-29 | 0.15 | 0.52 | 0.02 | 0.94 | 0.45 |
| 0515 | 25-29 | 0.21 | 0.54 | 0.04 | 0.89 | 0.45 |
| 0612 | 30-34 | 0.38 | 0.61 | 0.26 | 0.86 | 0.60 |
| 0275 | 30-34 | 0.18 | 0.55 | 0.20 | 0.52 | 0.45 |
| 0897 | 35-39 | 0.21 | 0.60 | 0.62 | 0.38 | 0.48 |
| 0248 | 35-39 | 0.16 | 0.54 | 0.04 | 0.85 | 0.44 |
| 0164 | 40-44 | 0.06 | 0.48 | 0.07 | 0.70 | 0.44 |
| 0314 | 40-44 | 0.04 | 0.47 | 0.03 | 0.85 | 0.44 |
| 0114 | 45-49 | 0.12 | 0.51 | 0.24 | 0.72 | 0.50 |
| 0395 | 45-49 | 0.12 | 0.52 | 0.31 | 0.36 | 0.45 |
| 0401 | 50-54 | 0.05 | 0.47 | 0.08 | 0.70 | 0.44 |
| 0936 | 50-54 | 0.06 | 0.51 | 0.55 | 0.29 | 0.46 |
| 0082 | 55-59 | 0.09 | 0.51 | 0.42 | 0.30 | 0.45 |
| 0420 | 55-59 | 0.14 | 0.54 | 0.18 | 0.48 | 0.44 |
| 0053 | 60-64 | 0.17 | 0.53 | 0.09 | 0.85 | 0.47 |
| 0942 | 60-64 | 0.28 | 0.59 | 0.06 | 0.77 | 0.52 |
| 0413 | 65-69 | 0.13 | 0.52 | 0.40 | 0.54 | 0.50 |
| 0214 | 65-69 | 0.10 | 0.50 | 0.96 | 0.05 | 0.48 |
| 0229 | 70-74 | 0.11 | 0.55 | 0.47 | 0.28 | 0.44 |
| 0237 | 70-74 | 0.17 | 0.56 | 0.35 | 0.42 | 0.46 |
| 0153 | 75-79 | 0.22 | 0.57 | 0.13 | 0.56 | 0.45 |
| 0276 | 75-79 | 0.68 | 0.73 | 0.43 | 0.69 | 0.90 |
| 0312 | 80-84 | 0.41 | 0.59 | 0.13 | 0.62 | 0.70 |
| 0249 | 80-84 | 0.34 | 0.61 | 0.41 | 0.93 | 0.61 |
| 0188 | 85-92 | 0.32 | 0.63 | 0.36 | 0.58 | 0.49 |
| 0323 | 85-92 | 0.31 | 0.57 | 0.04 | 0.74 | 0.54 |

### What it shows

- **Five separate P bands for 2 women of 30**: 0060 and 0155. Their five levels agree to
  within about 0.01 (S→T 0.94, Q→R 0.52, T→P 0.44–0.45, P→Q 0.14–0.15, R→S 0.02).
- **In (ż, P), five separate bands under both ż definitions for 4 of 30**: 0060, 0155,
  0153, 0249.
- **Two bands are shared by almost every heart**: T→P at P = 0.44–0.50 (22 of 30) and Q→R
  at 0.47–0.64 (28 of 30).
- **R→S and S→T vary from woman to woman** and can swap: in 0214 R→S is at 0.97 and S→T at
  0.05, the reverse of 0060.
- **The fixed scale explains much of it.** The share of x at 0 or 1 runs from 0 % to 59 %
  between women. The two women with five clean bands both have 56 %; the more saturated
  the input, the fewer overlaps (correlation −0.42). The saturation falls with age
  (Spearman −0.48, p = 0.007): the waves are smaller in older women, so the same scale in
  mV reads them more weakly.
- **Age**: the mean P of T→P and of R→S rises with age (Spearman +0.42, p = 0.02, and
  +0.37, p = 0.04), but with a fixed scale this cannot be separated from the change in
  saturation.

## All 30 women: a scale per woman

The fixed scale 25 reads each heart at a different saturation (0 % to 59 % of x at 0 or 1).
Here every woman is read at the saturation of 0060's best run, **56 % of x at 0 or 1**.
x reaches the edge when |s·u| > ln 99, so the scale is

$$
s_w = \frac{\ln 99}{q_{0.44}(|u|)}
$$

where q₀.₄₄(|u|) is the 44th percentile of the woman's |Re ċ| over the **first 500 steps**
(the learning phase): the scale is fixed before the bands are measured and uses no future
data, as it would in real time. It gives s = 25.1 for 0060 and 24.9 for 0155, the two women
with five clean bands at scale 25. The scales are in
[`results/scale_per_woman/scale_per_woman.csv`](results/scale_per_woman/scale_per_woman.csv)
and the measures in
[`results/scale_per_woman/summary_scale_per_woman_cos.csv`](results/scale_per_woman/summary_scale_per_woman_cos.csv).

| record | age | scale | x at 0 or 1 | distinct H curves | P bands overlapping | in (ż, P), ż central | in (ż, P), ż backward |
|---|---|---|---|---|---|---|---|
| 0060 | 18-19 | 25.1 | 56 % | 3 | **none** | **none** | **none** |
| 0465 | 18-19 | 40.4 | 46 % | 3 | 3 pairs | **none** | **none** |
| 1112 | 20-24 | 48.2 | 54 % | 3 | 3 pairs | P→Q/R→S | P→Q/R→S |
| 0002 | 20-24 | 64.3 | 64 % | 3 | **none** | **none** | **none** |
| 0155 | 25-29 | 24.9 | 56 % | 3 | **none** | **none** | **none** |
| 0515 | 25-29 | 28.8 | 61 % | 3 | P→Q/R→S, Q→R/S→T | P→Q/R→S | P→Q/R→S |
| 0612 | 30-34 | 101.6 | 56 % | 1 | P→Q/R→S, Q→R/T→P | P→Q/R→S | P→Q/R→S |
| 0275 | 30-34 | 46.5 | 54 % | 3 | 6 pairs | P→Q/R→S, S→T/T→P | P→Q/R→S |
| 0897 | 35-39 | 113.4 | 62 % | 2 | 8 pairs | P→Q/R→S, Q→R/R→S, Q→R/S→T, Q→R/T→P, S→T/T→P | P→Q/R→S, Q→R/R→S |
| 0248 | 35-39 | 33.8 | 54 % | 3 | P→Q/R→S | P→Q/R→S | P→Q/R→S |
| 0164 | 40-44 | 36.6 | 54 % | 2 | P→Q/R→S, Q→R/T→P | P→Q/R→S | P→Q/R→S |
| 0314 | 40-44 | 32.6 | 54 % | 2 | P→Q/R→S | **none** | P→Q/R→S |
| 0114 | 45-49 | 60.4 | 58 % | 1 | 7 pairs | P→Q/R→S, Q→R/R→S, S→T/T→P | P→Q/R→S |
| 0395 | 45-49 | 61.8 | 55 % | 1 | 7 pairs | P→Q/R→S, Q→R/R→S, S→T/T→P | P→Q/R→S |
| 0401 | 50-54 | 26.6 | 56 % | 2 | 4 pairs | P→Q/R→S, S→T/T→P | P→Q/R→S |
| 0936 | 50-54 | 55.9 | 61 % | 3 | 8 pairs | P→Q/R→S, P→Q/S→T, Q→R/R→S, S→T/T→P | P→Q/R→S, P→Q/S→T, Q→R/R→S |
| 0082 | 55-59 | 55.2 | 53 % | 3 | 7 pairs | P→Q/R→S, R→S/S→T, S→T/T→P | P→Q/R→S |
| 0420 | 55-59 | 65.4 | 60 % | 2 | P→Q/R→S, Q→R/T→P | P→Q/R→S | P→Q/R→S |
| 0053 | 60-64 | 44.1 | 56 % | 1 | P→Q/R→S, Q→R/T→P | P→Q/R→S | P→Q/R→S |
| 0942 | 60-64 | 55.3 | 58 % | 3 | P→Q/R→S, Q→R/T→P | P→Q/R→S | P→Q/R→S |
| 0413 | 65-69 | 61.6 | 55 % | 3 | 8 pairs | P→Q/R→S, R→S/S→T, S→T/T→P | P→Q/R→S |
| 0214 | 65-69 | 52.5 | 64 % | 1 | P→Q/S→T, Q→R/T→P | P→Q/S→T | P→Q/S→T |
| 0229 | 70-74 | 67.8 | 54 % | 3 | 7 pairs | P→Q/R→S, Q→R/R→S, R→S/S→T, R→S/T→P, S→T/T→P | P→Q/R→S, Q→R/R→S, R→S/S→T, R→S/T→P, S→T/T→P |
| 0237 | 70-74 | 69.5 | 52 % | 2 | 4 pairs | P→Q/R→S, S→T/T→P | P→Q/R→S |
| 0153 | 75-79 | 54.6 | 55 % | 4 | P→Q/R→S | **none** | **none** |
| 0276 | 75-79 | 237 | 59 % | 1 | 3 pairs | **none** | S→T/T→P |
| 0312 | 80-84 | 96.6 | 54 % | 3 | 4 pairs | P→Q/R→S, S→T/T→P | P→Q/R→S, S→T/T→P |
| 0249 | 80-84 | 112.3 | 54 % | 1 | P→Q/R→S, Q→R/T→P | P→Q/R→S | **none** |
| 0188 | 85-92 | 97.5 | 56 % | 1 | P→Q/R→S, Q→R/T→P | P→Q/R→S | **none** |
| 0323 | 85-92 | 44.6 | 53 % | 4 | Q→R/T→P | **none** | **none** |

Mean P per transition:

| record | age | P→Q | Q→R | R→S | S→T | T→P |
|---|---|---|---|---|---|---|
| 0060 | 18-19 | 0.14 | 0.52 | 0.02 | 0.95 | 0.44 |
| 0465 | 18-19 | 0.09 | 0.50 | 0.06 | 0.80 | 0.44 |
| 1112 | 20-24 | 0.18 | 0.54 | 0.08 | 0.85 | 0.44 |
| 0002 | 20-24 | 0.21 | 0.54 | 0.01 | 0.93 | 0.45 |
| 0155 | 25-29 | 0.15 | 0.52 | 0.02 | 0.94 | 0.45 |
| 0515 | 25-29 | 0.18 | 0.53 | 0.04 | 0.91 | 0.45 |
| 0612 | 30-34 | 0.02 | 0.45 | 0.02 | 0.91 | 0.45 |
| 0275 | 30-34 | 0.05 | 0.48 | 0.09 | 0.76 | 0.44 |
| 0897 | 35-39 | 0.02 | 0.45 | 0.25 | 0.55 | 0.44 |
| 0248 | 35-39 | 0.10 | 0.50 | 0.02 | 0.93 | 0.44 |
| 0164 | 40-44 | 0.02 | 0.45 | 0.03 | 0.86 | 0.44 |
| 0314 | 40-44 | 0.02 | 0.45 | 0.02 | 0.92 | 0.44 |
| 0114 | 45-49 | 0.02 | 0.44 | 0.10 | 0.79 | 0.45 |
| 0395 | 45-49 | 0.02 | 0.45 | 0.10 | 0.67 | 0.44 |
| 0401 | 50-54 | 0.04 | 0.47 | 0.07 | 0.72 | 0.44 |
| 0936 | 50-54 | 0.02 | 0.46 | 0.40 | 0.38 | 0.45 |
| 0082 | 55-59 | 0.02 | 0.45 | 0.26 | 0.46 | 0.44 |
| 0420 | 55-59 | 0.01 | 0.44 | 0.02 | 0.91 | 0.44 |
| 0053 | 60-64 | 0.06 | 0.47 | 0.04 | 0.91 | 0.44 |
| 0942 | 60-64 | 0.10 | 0.49 | 0.01 | 0.86 | 0.46 |
| 0413 | 65-69 | 0.02 | 0.45 | 0.17 | 0.52 | 0.44 |
| 0214 | 65-69 | 0.04 | 0.47 | 0.99 | 0.04 | 0.46 |
| 0229 | 70-74 | 0.02 | 0.45 | 0.14 | 0.58 | 0.44 |
| 0237 | 70-74 | 0.02 | 0.45 | 0.10 | 0.68 | 0.44 |
| 0153 | 75-79 | 0.05 | 0.47 | 0.01 | 0.91 | 0.44 |
| 0276 | 75-79 | 0.04 | 0.47 | 0.04 | 0.49 | 0.86 |
| 0312 | 80-84 | 0.06 | 0.46 | 0.03 | 0.62 | 0.55 |
| 0249 | 80-84 | 0.01 | 0.44 | 0.02 | 0.93 | 0.44 |
| 0188 | 85-92 | 0.05 | 0.46 | 0.03 | 0.90 | 0.43 |
| 0323 | 85-92 | 0.12 | 0.51 | 0.01 | 0.80 | 0.48 |

### Fixed scale against scale per woman

![The five transition bands across 30 women](results/bands_30_women.png)

*Mean P of each transition for every woman, sorted by age. Left: fixed scale 25. Right:
scale per woman. An open circle marks a transition whose input is at x = 0 or 1 in at least
90 % of its steps: its level is set mostly by the edge of the sigmoid.*


| | scale 25 | scale per woman |
|---|---|---|
| spread of x at 0 or 1 between women (sd) | 20 points | 3.8 points |
| five separate P bands | 2 of 30 | **3 of 30** (0060, 0155, 0002) |
| five separate bands in (ż, P), both ż definitions | 4 of 30 | **6 of 30** (0060, 0465, 0002, 0155, 0153, 0323) |
| median number of overlapping P pairs (of 10) | 4.5 | **2** |
| Q→R band at P = 0.44–0.55 | 17 of 30 | **30 of 30** |
| T→P band at P = 0.43–0.47 | 18 of 30 | **27 of 30** |
| most frequent overlap | P→Q/R→S and Q→R/S→T (21 each) | P→Q/R→S (25) |

### What it shows

- **Q→R and T→P sit at the same level in almost every heart** (30 and 27 of 30; the T→P
  exceptions are 0276, 0312 and 0323), but partly because of the scale rule: at 56 %
  saturation the input of T→P is at x = 1 in 99 % of its steps (median over the women), and
  S→T, which precedes it, at x = 0 in 96 %. T→P is then a jump from one edge to the other,
  and its P is nearly fixed by construction. Q→R is less pinned (x = 1 in 68 % of its
  steps). The transitions that stay off the edges, P→Q and R→S, are the ones that differ
  between women.

  | transition | x at 1 | x at 0 |
  |---|---|---|
  | P→Q | 0 % | 0.5 % |
  | Q→R | 68 % | 0 % |
  | R→S | 0 % | 13 % |
  | S→T | 0 % | 96 % |
  | T→P | 99 % | 0 % |

  *Median share of each transition's steps with x at the edge (above 0.99 or below 0.01),
  over the 30 women, per-woman scale.*
- **The separation improves but is not complete**: the median woman has 2 overlapping pairs
  instead of 4.5. Five clean P bands remain rare (3 of 30).
- **The main remaining overlap is P→Q with R→S** (25 of 30): with this scale both fall near
  P = 0, at the bottom of the P axis.
- **The age trends at scale 25 were the saturation.** The rise of T→P and R→S with age
  (p = 0.02 and 0.04 at scale 25) disappears (Spearman +0.03 and +0.03). What remains is a
  weak fall of P→Q and S→T with age (Spearman −0.35, p = 0.06, and −0.36, p = 0.05),
  borderline with 30 women.
- **R→S and S→T still differ from woman to woman** (0214: R→S 0.99, S→T 0.04).

## Limits

- **30 healthy women**, 15 minutes each, one lead. Nothing here is a result about hearts in
  general, nor about men.
- **ż is partly timing.** ż divides the change of z by the time since the previous wave, and
  that time differs a lot by transition (≈ 30 ms for Q→R, several hundred for T→P). Part of
  the separation along ż comes from the timing of the beat, not from the input x.
- **z mostly counts steps**: it grows with the size of the matrix. The separation that
  matters is in P and ż.
- **9 beats of 1,085 have no S wave in 0060** (see `complex-events/`); they are the few
  points away from their bands. Other women may have their own; they were not inspected one
  by one.
- **The bands are transition bands.** P compares each step with the previous one, so a band
  is a passage between two successive waves, not a property of one value. The order
  P → Q → R → S → T is therefore part of what is learned: it is the structure of the beat.
  In pathology that order breaks, and new transitions should appear as new bands.
- **The scale.** A fixed scale in mV gives each woman a different input range (see `x_min`,
  `x_max` in `complex-events/aging/summary_all.csv`), and this shapes the bands. The
  per-woman rule removes most of it, but a fixed 56 % puts about three of the five
  transitions at the edges; for a heart where only two transitions are large it could clip
  a small one. An alternative is s = c / median(|u|), with c set to give 25 on 0060.

## Next test

**A scale that saturates less.** The 56 % rule pins T→P and S→T to the edges, so their
common level cannot be read as a property of the heart. The next run uses
s = c / median(|u|), with c set to give 25 on 0060, on the same 30 women. The question: do
Q→R and T→P stay common when they are no longer pinned, and does P→Q separate from R→S?

## Layout of `results/`

```
results/
├── bands_30_women.png the five bands across the 30 women, both scales
├── 0060/              the detailed study of record 0060: 9 runs (3 inputs × scales 5, 25, 50)
├── scale25/           all 30 women at the fixed scale 25, cosine input
│   ├── <record>/      ska_<record>_runs.csv and figures/
│   └── summary_scale25_cos.csv
└── scale_per_woman/   all 30 women at their own scale, cosine input
    ├── <record>/      ska_<record>_runs.csv and figures/
    ├── scale_per_woman.csv
    └── summary_scale_per_woman_cos.csv
```

## Figures

**`results/0060/figures/`**, for each input (`cdot_cos`, `cdot_sin`, `cdot_cossin`); no suffix = scale 5, `_scale25`,
`_scale50`:

| file | shows |
|---|---|
| `ska_0060_<input>[_scaleN].png` | H (top) and P (bottom) along the step index, coloured by transition |
| `bands3d_0060_<input>[_scaleN].png` | the bands in the learner's space (z, ż, P) |
| `bands3d_0060_compare[_scaleN].png` | the three inputs side by side in (z, ż, P) |

21 figures: 9 + 9 + 3.

**`results/scale25/<record>/figures/`**, for each of the 30 women:
`ska_<record>_cdot_cos_scale25.png` (H and P) and `bands3d_<record>_cdot_cos_scale25.png`
(the bands in (z, ż, P)).

**`results/scale_per_woman/<record>/figures/`**: the same two figures, with the woman's own
scale in the name, e.g. `ska_0465_cdot_cos_scale40.4.png`.

## Data — `ska_<record>_runs.csv`

One row per step, ordered by input, scale and step: 9 runs × 3,500 = 31,500 rows in
`results/0060/`, one run × 3,500 rows per woman in `results/scale25/<record>/` and in
`results/scale_per_woman/<record>/`.
`results/scale25/summary_scale25_cos.csv` holds one row per woman with the measures of the
30-woman table at scale 25, and `results/scale_per_woman/summary_scale_per_woman_cos.csv`
the same for the per-woman scale (with a `scale` column).

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
