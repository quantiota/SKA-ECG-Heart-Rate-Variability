#!/usr/bin/env python3
"""Load the kit's CSV files into QuestDB, as the two tables of the original database.

    ecg_steps        raw ECG samples, one row per sample (data/ecg_steps/<record>.csv.gz)
    ecg_ska_results  SKA learner output, one row per step (data/ecg_ska_results.csv.gz)

Uses the QuestDB HTTP import endpoint (/imp, port 9000). Start QuestDB first, for example
    docker run -p 9000:9000 -p 8812:8812 questdb/questdb

Usage
    python scripts/load_questdb.py                       # localhost:9000, all records
    python scripts/load_questdb.py --host questdb --records 0060 0002
Requires: requests
"""
import argparse
import gzip
import json
import pathlib

import requests

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"

# Column types of the original tables (other columns are typed by QuestDB from the CSV)
SCHEMA = {
    "ecg_steps": [
        {"name": "record_id", "type": "SYMBOL"}, {"name": "age_band", "type": "SYMBOL"},
        {"name": "channel", "type": "SYMBOL"}, {"name": "step_index", "type": "LONG"},
        {"name": "sample_index", "type": "LONG"}, {"name": "adc", "type": "LONG"},
        {"name": "value", "type": "DOUBLE"}, {"name": "rate_hz", "type": "DOUBLE"},
        {"name": "record_length", "type": "LONG"}, {"name": "total_steps", "type": "LONG"},
        {"name": "timestamp", "type": "TIMESTAMP", "pattern": "yyyy-MM-dd HH:mm:ss.SSSUUU"},
    ],
    "ecg_ska_results": [
        {"name": "record_id", "type": "SYMBOL"}, {"name": "input", "type": "SYMBOL"},
        {"name": "event", "type": "SYMBOL"}, {"name": "transition", "type": "SYMBOL"},
        {"name": "event_index", "type": "LONG"}, {"name": "k", "type": "LONG"},
        {"name": "peak", "type": "LONG"}, {"name": "matrix_size", "type": "LONG"},
        {"name": "timestamp", "type": "TIMESTAMP", "pattern": "yyyy-MM-dd HH:mm:ss.SSSUUU"},
    ],
}


def load(url, table, name, payload):
    r = requests.post(f"{url}/imp", params={"name": table, "timestamp": "timestamp", "partitionBy": "DAY",
                                            "fmt": "json", "overwrite": "false"},
                      files={"schema": (None, json.dumps(SCHEMA[table])), "data": (name, payload)})
    r.raise_for_status()
    res = r.json()
    if res.get("status") != "OK" or res.get("rowsRejected", 0):
        raise SystemExit(f"{name}: {res}")
    print(f"{table:16s} {name:24s} {res['rowsImported']:>9,} rows")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--records", nargs="*", help="record ids for ecg_steps (default: all)")
    a = ap.parse_args()
    url = f"http://{a.host}:{a.port}"

    load(url, "ecg_ska_results", "ecg_ska_results.csv", gzip.decompress((DATA / "ecg_ska_results.csv.gz").read_bytes()))
    files = sorted((DATA / "ecg_steps").glob("*.csv.gz"))
    if a.records:
        files = [f for f in files if f.name.split(".")[0] in a.records]
    for f in files:
        load(url, "ecg_steps", f.name, gzip.decompress(f.read_bytes()))


if __name__ == "__main__":
    main()
