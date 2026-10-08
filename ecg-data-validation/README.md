# ECG Data Stream Validation

Simulated real-time ECG streaming and QuestDB ingestion validation.

## Purpose

- Validate streaming of resting ECG recordings one sample at a time
- Test QuestDB table creation and ILP ingestion
- Collect clean raw ECG values for future SKA analysis

No returns, no entropy, no learning at this stage. **Raw values only.**

## Development environment

AI Agent Host — [Quick start](https://github.com/quantiota/AI-Agent-Host)

## Quick start

```bash
pip install -r requirements.txt

# Download the subject table and the records listed in records.txt from PhysioNet
./fetch_data.sh

# Point at your QuestDB instance
export QDB_PG_HOST=localhost      # pg-wire on 8812, ILP on 9009

# 1. Test the connection
python test_connection.py

# 2. Stream the records into QuestDB
python ecg_stream_validator.py

# 3. Validate the collected data
python validate_data.py
```

Options: `--max-steps N` for a subset, `--rate HZ` for the emission rate, and `--recreate`
to drop an existing non-empty table (refused without it, so a running collection cannot be
destroyed by accident).

## The data

[Autonomic Aging](https://physionet.org/content/autonomic-aging-cardiovascular/1.0.0/)
(PhysioNet): resting ECG from 1,121 healthy volunteers aged 18 to 92, sampled at 1000 Hz.
Ages are given in 15 bands. Heart rate variability is known to decline with age, so the
dataset carries its own reference.

`records.txt` lists the 30 records streamed. Every factor except age is held fixed:

| factor | choice | why |
|---|---|---|
| recorder | `Device` 0, Task Force Monitor | the only recorder present in all 15 age bands |
| sex | women | the only sex present in all 15 bands — this recorder has no men over 74 |
| lead | `ECG1`, the same for every record | the recorder writes two leads |
| subjects | 2 per age band, longest recordings first | 30 records, 18 to 92 years |
| window | the first 15 minutes | the length every selected record has |

BMI is not controlled (18 to 40 in the selection).

## What a step is

The records are walked one sample at a time. Each step carries the ECG at that
millisecond:

```
step k   =  the ECG at t = k ms
value    =  (adc - baseline) / gain       in mV, from the record header
```

`adc` is the raw 16-bit value as stored; `value` is the same sample in millivolts. Nothing
is filtered, detected or rescaled.

## Why 1,000 steps per second

The recordings were sampled at 1000 Hz, so the stream runs at the same rate: one step is
one millisecond of signal, the true clock of the recording. One 15-minute window takes
15 minutes, and the 30 records **7.5 hours**.

## Timestamps are assigned, not measured

Each row is stamped on a **fixed grid** anchored at the run's start time:

```
timestamp(k) = t_start + k / rate_hz
```

These are **assigned** timestamps. A downstream `delta_t` will return exactly `1/rate_hz`
with no jitter. At the native rate that is the recording's own clock, 1 ms, but it describes
the recording, not the replay.

The records are streamed one after another, so `step_index` runs across the whole collection
while `sample_index` restarts at 0 for each record. Read one record at a time:

```sql
SELECT * FROM ecg_steps WHERE record_id = '0060' ORDER BY sample_index;
```

## Schema

```sql
CREATE TABLE ecg_steps (
    record_id SYMBOL,          -- PhysioNet record, e.g. '0060'
    age_band SYMBOL,           -- '18-19' … '85-92'
    channel SYMBOL,            -- ECG1
    step_index LONG,           -- emission order across the collection
    sample_index LONG,         -- position within the record (1 sample = 1 ms)
    adc LONG,                  -- raw 16-bit value
    value DOUBLE,              -- the sample in mV
    rate_hz DOUBLE,            -- emission rate (provenance)
    record_length LONG,        -- samples per record window
    total_steps LONG,
    timestamp TIMESTAMP        -- assigned, on a fixed grid
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

Ingestion uses QuestDB's **InfluxDB line protocol on port 9009** (~600,000 rows/s), not
pg-wire — which caps near 3,500 rows/s and cannot sustain the stream.

## Files

| file | role |
|---|---|
| `ecg_chain.py` | the data source — WFDB reader, record walk, sample events |
| `ecg_stream_validator.py` | paced emission into QuestDB over ILP |
| `test_connection.py` | QuestDB smoke test |
| `validate_data.py` | QC report on the collected stream |
| `config.py` | QuestDB, ILP, ECG and logging configuration |
| `records.txt` | the records streamed, in order |
| `fetch_data.sh` | download the subject table and the records from PhysioNet |

## Output

- `logs/ecg_validation.log`

## Data Collection Summary

Produced by `python validate_data.py` after the full collection.

```
dataset    Autonomic Aging (PhysioNet), lead ECG1, first 15 min per record
records    30 women, 18 to 92 years, 2 per age band, recorder 0
collected  27,000,000 samples  (1000 Hz, 7.5 h, 2026-10-07 19:01 -> 2026-10-08 02:31)
```

The 7.5 h is the signal's own length: 30 records × 900 s at the native rate.

### Stream coverage

| | |
|---|---|
| rows | 27,000,000 |
| distinct `step_index` | 27,000,000 |
| range | 0–26,999,999 |
| repeated steps | 0 |
| gaps within range | 0 |
| timestamps | 26,999,999 ms for 26,999,999 intervals — on the 1 ms grid |

### Records

Every record holds exactly 900,000 samples, `sample_index` 0–899,999, 100.0 % of its window,
with no gaps and no duplicates.

| age band | records | | age band | records |
|---|---|---|---|---|
| 18–19 | 0060, 0465 | | 55–59 | 0082, 0420 |
| 20–24 | 1112, 0002 | | 60–64 | 0053, 0942 |
| 25–29 | 0155, 0515 | | 65–69 | 0413, 0214 |
| 30–34 | 0612, 0275 | | 70–74 | 0229, 0237 |
| 35–39 | 0897, 0248 | | 75–79 | 0153, 0276 |
| 40–44 | 0164, 0314 | | 80–84 | 0312, 0249 |
| 45–49 | 0114, 0395 | | 85–92 | 0188, 0323 |
| 50–54 | 0401, 0936 | | | |

Two records first selected were replaced before the collection: in **0186** (40–44) and
**0365** (55–59) lead ECG1 is mains interference — 50 Hz carries 98 % and 99 % of the signal
power and no beat is visible. They were replaced by the next women in the same band on the
same recorder, longest first: **0314** and **0420** (see `records.txt`).

### Collected vs record files

An independent round trip: for every record, the row count, the sum of `adc` and the mV
range read back from QuestDB against the same window re-read from the file. **All 30
records match exactly.**

### Recording artifacts — kept, as recorded

| record | artifact | extent |
|---|---|---|
| 0229 | a single spike to −14.4 / +18.2 mV | 3 samples at 480 s |
| 0612 | a burst up to +19.0 mV | 3,279 samples, 682–686 s (0.4 % of the window) |

They are in the original files (the round trip matches), so they stay in the raw stream.
Any analysis has to handle them.

All records also carry **50 Hz mains interference** at about 1–4 % of the signal power, and
baseline drift. Both are part of the raw signal and are left untouched here.

### Data quality

```
🔍 Data quality:
   NULL value: 0
   NULL adc: 0
   NULL record_id: 0
   NULL step_index: 0
   NULL sample_index: 0
   duplicate step_index: 0
   step gaps: 0
   sample_index gaps within a record: 0
   duplicate sample_index within a record: 0
   records not matching their file: 0
✅ Data quality PASSED
```
