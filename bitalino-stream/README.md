# BITalino ECG stream

**Real-time raw ECG from a BITalino (r)evolution board, learned on the fly by the SKA
real-time learner, with every sample and the learner's state stored in QuestDB.**

The learner reads each sample the moment it arrives. QuestDB only stores; it is not in the
learning path. No filtering and no beat detection happen anywhere.

## Requirements

- BITalino (r)evolution Board Kit, connected by **USB** (preferred — Bluetooth can drop packets)
- Python ≥ 3.8
- QuestDB with ILP enabled on port 9009
- `pip install -r requirements.txt` (`bitalino`, `numpy`)

Serial port: Linux `/dev/ttyUSB0`, macOS `/dev/tty.*`, Windows `COM3` (check Device Manager).

## Safety

BITalino is a research kit, **not a medical device**. When the electrodes are on the body,
run the computer **on battery, unplugged from the mains**. Nothing in this repository is
intended for diagnosis.

## Quick start

```bash
git clone https://github.com/quantiota/SKA-ECG-Heart-Rate-Variability.git
cd SKA-ECG-Heart-Rate-Variability/bitalino-stream
pip install -r requirements.txt

# test without hardware: synthetic ECG, rows printed to the console
python ska_stream.py --simulate --seconds 5 --dry-run

# live: ECG on channel A1, learned on the fly, stored in QuestDB table ecg_stream
python ska_stream.py --port /dev/ttyUSB0 --learner ska_engine:SKALearner

# raw stream only (no learner)
python ska_stream.py --port /dev/ttyUSB0
```

Options: `--learner` (module:Class), `--channel` (0 = A1), `--seconds` (0 = until Ctrl-C),
`--host`, `--ilp-port`, `--table`, `--dry-run`, `--simulate`.

## The learner

The SKA real-time engine is proprietary and not included. It plugs in with
`--learner module:Class`; the class must provide

```python
def step(self, level: float) -> dict[str, float]: ...
```

called once per sample, in order, with the input level in [0, 1]. The fields it returns
(for example `knowledge`, `entropy`, `P`) are written to the same row as the sample.

## What is written

One row per sample in the table `ecg_stream`:

| column | meaning |
|---|---|
| `sample_index` | 0, 1, 2, … — the internal clock (1 sample = 1 ms) |
| `adc` | raw 10-bit value, 0–1023 |
| `level` | `adc / 1023`, the input level in [0, 1] |
| `seq` | BITalino sequence number (0–15), used to count dropped packets |
| learner fields | whatever `step()` returns — e.g. `knowledge`, `entropy`, `P` |
| `timestamp` | start time + `sample_index` × 1 ms (constant step) |
| `source` | `bitalino` or `simulate` |

The learner reads the stream on the sample index. Wall-clock time is kept only as a
constant 1 ms step.

## Technical specifications

| Feature | Value |
|---|---|
| Sampling rate | 1000 Hz |
| ADC resolution | 10-bit |
| Channel | A1 (ECG) |
| Data | raw value per sample, no processing |
| Ingestion | QuestDB ILP, TCP 9009 |

## Data flow

```text
BITalino (USB, 1000 Hz)
     ↓
ska_stream.py ── raw ADC → level in [0, 1]
     ↓
SKA real-time learner  (in process, sample by sample)
     ↓
QuestDB  (table ecg_stream, ILP 9009 — raw sample + learner state, one row per sample)
     ↓
Grafana (live visualization)
```

## Documentation

Manufacturer documents in [`docs/`](docs/): quick-start guide, user manual and board-kit datasheet.
