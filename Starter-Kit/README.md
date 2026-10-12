# SKA-ECG starter kit

**The data and the SKA results of thirty women aged 18 to 92, ready to load and plot.**

The ECG comes from 30 records of the PhysioNet
[Autonomic Aging database](https://physionet.org/content/autonomic-aging-cardiovascular/1.0.0/)
(lead ECG1, 1000 Hz, the first 15 minutes, 2 women per age band). The SKA results are the
output of the SKA real-time learner reading the five waves of each heartbeat. The method is
described in this repository: [`complex-events/`](../complex-events/) for the input, and
[`ska-ecg-engine/`](../ska-ecg-engine/) for the results. The learner itself is not included:
the kit holds its output, not its code.

## Contents

```
Starter-Kit/
├── README.md
├── data/
│   ├── ecg_steps/<record>.csv.gz   raw ECG, one row per sample, one file per woman
│   ├── ecg_ska_results.csv.gz      SKA learner output, one row per step, every run
│   └── selected_scales.csv         record_id, age_band, the scale selected for that woman
├── scripts/
│   ├── load_questdb.py             load the CSV files into QuestDB (the original two tables)
│   ├── plot_record.py              2D and 3D figures for one record and one scale
│   ├── build_cube.py               3D cube (HTML) for one record and one scale
│   ├── ska_data.py                 shared loader (computes P and ż)
│   └── ska_ecg_vr_template.html    the cube template
└── vr/                             one cube per woman, at her selected scale
```

The scripts read the CSV files directly; QuestDB is optional.

## Two ways to read the data

**pandas**, directly from the files:

```python
import pandas as pd
ecg = pd.read_csv("data/ecg_steps/0060.csv.gz")
ska = pd.read_csv("data/ecg_ska_results.csv.gz", dtype={"record_id": str})
```

**QuestDB**, to work in SQL: load the two tables with `scripts/load_questdb.py` (see Quick start).

## Quick start

Python 3 with numpy, pandas, matplotlib (and requests for QuestDB).

```bash
python scripts/plot_record.py 0060 25          # → figures/ska_0060_scale25.png, bands3d_0060_scale25.png
python scripts/plot_record.py 0060 selected    # the scale selected for that woman
python scripts/build_cube.py 0060 25           # → vr/ska_ecg_0060_scale25_vr.html, open in a browser
```

To work in SQL, load the two tables into a QuestDB instance:

```bash
docker run -p 9000:9000 -p 8812:8812 questdb/questdb
python scripts/load_questdb.py                 # all 30 records, or --records 0060 0002
```

```sql
SELECT * FROM ecg_steps WHERE record_id = '0060' ORDER BY sample_index;
SELECT * FROM ecg_ska_results WHERE record_id = '0060' AND input = 'cdot_cos' AND scale = 25 ORDER BY event_index;
```

## `ecg_steps` — the raw ECG

One row per sample, 900,000 per woman (15 minutes at 1000 Hz). Nothing is filtered or rescaled.

| column | meaning |
|---|---|
| `record_id`, `age_band` | PhysioNet record, e.g. `0060`, and its age band, e.g. `18-19` |
| `channel` | `ECG1` |
| `step_index` | emission order across the 30 records |
| `sample_index` | position within the record (1 sample = 1 ms) |
| `adc` | raw 16-bit value |
| `value` | the sample in mV, (adc − baseline) / gain from the record header |
| `rate_hz`, `record_length`, `total_steps` | provenance |
| `timestamp` | assigned on a fixed grid, t_start + k / rate_hz |

## `ecg_ska_results` — the SKA output

For each wave n of the heartbeat (P, Q, R, S, T) the learner reads one number,
x_n = σ(s · Re ċ_n), where ċ_n = c_n − c_{n−1} is the change of the wave's phasor and s is the
scale (per mV). One step is one wave, five steps per beat; a run is 3,500 steps = 700 beats.
Each woman has one run per scale tried, the selected one and the others; the selected scale
is in `selected_scales.csv`. Record 0060 also has the sine and cosine + sine inputs.

| column | meaning |
|---|---|
| `record_id`, `input`, `scale` | the run (`cdot_cos` = Re ċ, `cdot_sin` = Im ċ, `cdot_cossin` = their sum) |
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
| `timestamp` | the wave's time in the recording |

The scripts add two quantities (`scripts/ska_data.py`):

| | definition |
|---|---|
| **P** | the transition probability, P = exp(−\|ΔH / H\|), from the entropy of two successive steps |
| **ż** | ż = dz/dt per second, central difference `np.gradient(z) / delta_t` |

(z, ż, P) is the learner's 3D space: the axes of the figures and the cubes, coloured by the
five transitions P→Q, Q→R, R→S, S→T, T→P.

## Joining with the ECG

`peak` in `ecg_ska_results` is a `sample_index` of `ecg_steps` for the same `record_id`, so each
step of the learner points to the sample of its wave in the raw ECG, and `k` groups the five
waves of one beat.

## License

Scripts: MIT, as this repository. ECG data: from PhysioNet, under the license of the Autonomic
Aging database; cite the database when you use it.
