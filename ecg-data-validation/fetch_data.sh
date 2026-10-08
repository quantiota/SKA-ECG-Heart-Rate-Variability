#!/usr/bin/env bash
# Download the subject table and the records listed in records.txt from the
# PhysioNet Autonomic Aging database. Files already present are kept.
set -euo pipefail
BASE="https://physionet.org/files/autonomic-aging-cardiovascular/1.0.0"
mkdir -p data
echo "Fetching subject-info.csv ..."
[ -s data/subject-info.csv ] || curl -sS -o data/subject-info.csv "$BASE/subject-info.csv"
for id in $(grep -v '^#' records.txt | awk 'NF {print $1}'); do
  for ext in hea dat; do
    f="data/$id.$ext"
    if [ ! -s "$f" ]; then
      curl -sS -o "$f.part" "$BASE/$id.$ext" && mv "$f.part" "$f"
    fi
  done
  echo "  $id  $(du -h "data/$id.dat" | cut -f1)"
done
echo "Done: $(ls data/*.dat | wc -l) records in data/"
