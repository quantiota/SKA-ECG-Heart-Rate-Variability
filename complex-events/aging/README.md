# Phasors and learner input — one person

**From the raw ECG of one person to the number the SKA learner reads, step by step.**

The person is **record 0060** of the PhysioNet Autonomic Aging database: a woman aged 18–19,
lead ECG1, the first 15 minutes, 1000 Hz. The signal is read from the collected stream
(`ecg_steps`, built by `ecg-data-validation/`): 900,000 samples, **1,085 beats**, median
beat duration RR = 822 ms.

## The input in three lines

**1. The phasor of wave j in beat k**, with x(t) the ECG minus its baseline and t in ms from
the P peak:

$$
r = \frac{RR_k}{2\pi}, \qquad
c_j = \frac{1}{r}\sum_{t \in \text{arc}_j} x(t)\, e^{\,i t / r}
\;\approx\; h_j \cdot 2\sin\!\left(\tfrac{\varphi_j}{2}\right) \cdot e^{\,i\theta_j}
$$

**2. The return**, on the event index n = 5k + j:

$$
\dot c_n = c_n - c_{n-1}
$$

**3. The learner input**, the real part, scaled and squeezed into (0, 1):

$$
x_n = \frac{1}{1 + e^{-s\,\mathrm{Re}\,\dot c_n}}
$$

where h_j is the **mean height** of the wave over its arc (not its peak), θ_j the centre of
the arc and φ_j its width, both as angles, and s is the scale (per mV).

One x_n per wave, five per beat, in order P, Q, R, S, T. The sections below build each line
step by step.

---

## 1. Five waves per beat

Each beat contains five waves, always in the same order: **P → Q → R → S → T**. For each
wave the code finds its **peak** and its **arc**: the stretch of signal around the peak that
stays on the same side of the baseline (above it for P, R, T; below it for Q, S).

![Detection](figures/0060/fig2_detection_real.png)

*Figure 2 — The raw ECG, first three beats. Dots are the peaks; shaded areas are the arcs;
the dotted line is the baseline of each beat.*

## 2. Each wave becomes one complex number: its phasor c

### The definition

Each beat is drawn on a circle whose circumference is the beat's duration:

$$
RR_k = 2\pi r \qquad\Rightarrow\qquad r = \frac{RR_k}{2\pi}
$$

Arc length is time: 1 ms of signal is 1 ms along the circle. A sample at time t (in ms from
the P peak) sits at the angle t / r. With x(t) the ECG minus its baseline, and [a_j, b_j] the
arc of wave j:

$$
c_j = \frac{1}{r}\sum_{t=a_j}^{b_j} x(t)\, e^{\,i t / r}
$$

### What c contains

Write the arc as two angles on the circle — its **centre** θ_j and its **width** φ_j:

$$
\theta_j = \frac{\text{centre of the arc}}{r}, \qquad \varphi_j = \frac{\text{width of the arc}}{r}
$$

With h_j the **mean height** of the wave over its arc, the sum works out to

$$
\boxed{\;c_j = h_j \cdot 2\sin\!\left(\frac{\varphi_j}{2}\right) \cdot e^{\,i\theta_j}\;}
$$

| part of c | equals | meaning |
|---|---|---|
| angle of c | θ_j (+ π if the wave points down) | **where** the wave is in the beat |
| length of c | \|h_j\| · 2 sin(φ_j / 2) | **mean height × chord of the arc** |

For a narrow arc (Q, R, S), 2 sin(φ_j/2) ≈ φ_j, so c_j ≈ h_j φ_j e^{iθ_j}: only the
**product** of mean height and width appears. A tall narrow wave and a short wide wave with the
same product give the same c. The width is still measured separately (column `arc`).

### An example: the R wave of this person

R peaks at 1.68 mV over an arc of 39 ms; its mean height is about 1.0 mV and its arc
0.30 rad, so \|c_R\| ≈ 1.0 × 0.30 = 0.30 mV, as measured.

![Phasors in the complex plane](figures/0060/fig4_c_complex_plane.png)

*Figure 4 — Every phasor c_j of the 1,085 beats. Each wave forms its own cluster.*

![Phasors along the event index](figures/0060/fig5_c_event_index.png)

*Figure 5 — Re c and Im c along the event index (5 events per beat): the same five levels
repeat beat after beat.*

The beat as a whole has one phasor, the sum of its five:

$$
C_k = c_P + c_Q + c_R + c_S + c_T
$$

## 3. What the learner reads

The learner reads **one number between 0 and 1 per wave**, five per beat, in order. It is
made in three steps:

$$
\dot c_n = c_n - c_{n-1}
\qquad\longrightarrow\qquad
\mathrm{Re}\,\dot c_n
\qquad\longrightarrow\qquad
x_n = \frac{1}{1 + e^{-s\,\mathrm{Re}\,\dot c_n}}
$$

1. **the return** ċ — the change from the previous wave to this one;
2. **its real part** (the cosine) — the learner reads one real number;
3. **squeezed into (0, 1)** by the sigmoid, scale s.

Two real beats of this person, at scale 25 (the scale of her cube in
[`../../ska-ecg-engine/`](../../ska-ecg-engine/)):

| beat | wave | change | Re ċ | **x — the input** |
|---|---|---|---|---|
| 10 | P | T→P | +0.280 | **0.999** |
| 10 | Q | P→Q | −0.055 | **0.204** |
| 10 | R | Q→R | +0.195 | **0.992** |
| 10 | S | R→S | −0.181 | **0.011** |
| 10 | T | S→T | −0.262 | **0.001** |
| 11 | P | T→P | +0.302 | **0.999** |
| 11 | Q | P→Q | −0.055 | **0.201** |
| 11 | R | Q→R | +0.202 | **0.994** |
| 11 | S | R→S | −0.187 | **0.009** |
| 11 | T | S→T | −0.275 | **0.001** |

The learner therefore receives five values that repeat with each beat and change slightly
from one beat to the next.

![Return along the event index](figures/0060/fig6_cdot_event_index.png)

*Figure 6 — Re ċ and Im ċ along the event index, coloured by transition.*

## 4. The two streams side by side

![Levels per input](figures/0060/fig7_cdot_levels.png)

*Figure 7 — Left: Re ċ alone. Middle: Im ċ alone. Right: both together.*

## 5. The beat phasor and the rhythm

![|C| and RR](figures/0060/fig8_absC_RR.png)

*Figure 8 — The length of the beat phasor \|C_k\| and the beat duration RR, beat by beat.*

---

## Beat detection

The R peaks are found on a **cleaned copy** of the signal (50 Hz removed, QRS band 5–20 Hz),
then located on the raw signal; every value above — peaks, arcs, phasors — is computed on the
**raw** signal (`r_peaks` and `detect` in `../ska_complex_events.py`). The other four waves are
searched in fixed windows around each R peak, so the detection assumes the normal order
P → Q → R → S → T. A wave that does not reach its expected sign is marked absent
(`present` = False) and gives c = 0.

## Files

| file | content |
|---|---|
| `make_aging_figures.py` | figures 2, 4–8 for one record, read from `ecg_steps` |
| `detect_beats.py` | kept for older imports; the detection lives in `../ska_complex_events.py` |
| `complex_events_0060.csv` | one row per wave: peak, arc, peak height, present, RR, c, ċ, transition |
| `figures/0060/` | the figures above |

The phasor construction itself is `../ska_complex_events.py`, used unchanged.

Requires `ecg-data-validation/` next to `complex-events/`, with the records fetched and the
stream collected into `ecg_steps` (see its README), and the packages in
`../requirements.txt`.

```bash
python make_aging_figures.py 0060     # figures and CSV for one person
```
