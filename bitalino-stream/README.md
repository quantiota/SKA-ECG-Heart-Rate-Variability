# BITalino ECG stream

**Real-time raw ECG from a BITalino (r)evolution board, streamed sample by sample into
QuestDB for the SKA real-time learner.**

The stream is the input side only: acquisition, scaling and ingestion. No filtering, no
beat detection and no learning happen here.

## Requirements

- BITalino (r)evolution Board Kit, connected by **Bluetooth** (the device has no USB data link)
- Python ≥ 3.8
- QuestDB with ILP enabled on port 9009
- `pip install -r requirements.txt` (`bitalino`, `numpy`)
- Linux: the Bluetooth headers, needed to build `bitalino`: `sudo apt install libbluetooth-dev`

The device is addressed by its Bluetooth MAC address (Linux, macOS) or its Bluetooth serial port (Windows, e.g. `COM3`).

## Electrodes

Three electrodes, lead II, matched by **sleeve colour**:

![Electrode placement, lead II](docs/electrode_placement.png)

| sleeve | role | position |
|---|---|---|
| black | − | under the right collarbone |
| red | + | lower left ribcage |
| white | reference | under the left collarbone |

On the Board Kit the ECG sensor is wired to channel **A2**, so the stream reads `--channel 1`
(0 = A1, 1 = A2, …).

## Safety

BITalino is a research kit, **not a medical device**. It runs on its own battery and sends
its data by Bluetooth, so it has no wired link to the computer. **Never wear the electrodes
while the BITalino is charging.** Nothing in this repository is
intended for diagnosis.

## Quick start

**1. Install** (Linux)

```bash
sudo apt install libbluetooth-dev python3-venv
git clone https://github.com/quantiota/SKA-ECG-Heart-Rate-Variability.git
cd SKA-ECG-Heart-Rate-Variability/bitalino-stream
python3 -m venv ~/bitalino-venv
source ~/bitalino-venv/bin/activate
pip install -r requirements.txt
```

**2. Test without hardware** — synthetic ECG, rows printed to the console

```bash
python ska_stream.py --simulate --seconds 5 --dry-run
```

**3. Pair the BITalino** — switch it on, then pair with PIN `1234` and note its MAC address

```bash
bluetoothctl
  scan on                      # wait for BITalino-XX-XX and its MAC address
  pair XX:XX:XX:XX:XX:XX       # PIN 1234
  trust XX:XX:XX:XX:XX:XX
  quit
```

**4. Live stream** — ECG on A2 → QuestDB table `ecg_stream`, QuestDB on the same computer

```bash
python ska_stream.py --port XX:XX:XX:XX:XX:XX --channel 1 --host localhost --ilp-port 9009
```

Stop with Ctrl-C, or add `--seconds 300` for a 5-minute recording.

**5. Record without QuestDB** (e.g. on a Raspberry Pi during an activity), load it later

```bash
python ska_stream.py --port XX:XX:XX:XX:XX:XX --channel 1 --dry-run > run.ilp
nc localhost 9009 < run.ilp        # later, on the computer running QuestDB
```

The rows keep their original timestamps and `run` tag.

Options: `--channel` (0 = A1), `--seconds` (0 = until Ctrl-C), `--block` (samples per read),
`--run` (tag for this acquisition), `--host`, `--ilp-port`, `--table`, `--dry-run`, `--simulate`.

## What is written

One row per sample in the table `ecg_stream`:

| column | meaning |
|---|---|
| `run` | tag identifying the acquisition — default its UTC start time, e.g. `20261007T121500` |
| `sample_index` | 0, 1, 2, … — the internal clock (1 sample = 1 ms) |
| `adc` | raw 10-bit value, 0–1023 |
| `level` | `adc / 1023`, the input level in [0, 1] |
| `seq` | BITalino sequence number (0–15), used to count dropped packets |
| `timestamp` | start time + `sample_index` × 1 ms (constant step) |
| `source` | `bitalino` or `simulate` |

The learner reads the stream on the sample index, one `run` at a time. Wall-clock time is
kept only as a constant 1 ms step.

The clock survives dropped packets. Samples lost in transmission are detected from the
sequence number and skipped in `sample_index`, so the samples after a loss keep their true
position and RR intervals are not shortened. Losses of up to 15 consecutive samples are
counted exactly (15 shows up as a repeated sequence number); the 4-bit sequence number cannot
tell larger losses apart, so they are counted modulo 16.

The simulator (`--simulate`) produces a synthetic ECG with real beat-to-beat variability —
respiratory sinus arrhythmia plus random beat-to-beat variability, SDNN ≈ 30 ms over 5 minutes — so an HRV pipeline can be tested end to end without the board.

## Technical specifications

| Feature | Value |
|---|---|
| Sampling rate | 1000 Hz |
| ADC resolution | 10-bit |
| Channel | A2 (ECG, Board Kit) — `--channel 1` |
| Data | raw value per sample, no processing |
| Ingestion | QuestDB ILP, TCP 9009 |

## Data flow

```text
BITalino (Bluetooth, 1000 Hz)
     ↓
ska_stream.py  — raw ADC → level in [0, 1], one row per sample
     ↓
QuestDB  (table ecg_stream, ILP 9009)
     ↓
SKA real-time learner
     ↓
Grafana (live visualization)
```

## Documentation

Manufacturer documents in [`docs/`](docs/): quick-start guide, user manual and board-kit datasheet. `docs/electrode_placement.png` is the electrode figure above.
