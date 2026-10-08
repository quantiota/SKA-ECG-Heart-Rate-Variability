"""ECG record reader — the data source for the validation stream.

Turns WFDB records (header + 16-bit binary) into a sequence of samples, one per
millisecond, for a single fixed lead:

    sample k  =  the ECG at t = k ms
    value     =  (adc - baseline) / gain     in mV, from the record header

Records are emitted one after another, each over the same window. Raw values
only: no filtering, no beat detection, no scaling.
"""
from __future__ import annotations

import csv
import pathlib

import numpy as np

AGE_BANDS = {1: '18-19', 2: '20-24', 3: '25-29', 4: '30-34', 5: '35-39',
             6: '40-44', 7: '45-49', 8: '50-54', 9: '55-59', 10: '60-64',
             11: '65-69', 12: '70-74', 13: '75-79', 14: '80-84', 15: '85-92'}


def read_header(path):
    """WFDB .hea -> fs, n, and gain/baseline/name per signal.

    Gains carry the baseline in parentheses, e.g. '23356.8192(1481)/mV':
    physical = (adc - baseline) / gain.
    """
    lines = [l for l in pathlib.Path(path).read_text().splitlines()
             if l.strip() and not l.startswith('#')]
    _, nsig, fs, n = lines[0].split()[:4]
    signals = []
    for l in lines[1:1 + int(nsig)]:
        f = l.split()
        g = f[2].split('/')[0]
        gain, base = (float(g.split('(')[0]), float(g.split('(')[1].rstrip(')'))) \
            if '(' in g else (float(g), 0.0)
        signals.append({'file': f[0], 'fmt': f[1], 'gain': gain, 'baseline': base,
                        'name': f[-1]})
    return {'nsig': int(nsig), 'fs': float(fs), 'n': int(n), 'signals': signals}


def read_records(path):
    """records.txt -> record IDs, in order (first column, '#' lines ignored)."""
    return [l.split()[0] for l in pathlib.Path(path).read_text().splitlines()
            if l.strip() and not l.startswith('#')]


def read_subjects(data_dir):
    """subject-info.csv -> {ID: row}. Sex is coded 0 male, 1 female."""
    return {r['ID']: r for r in csv.DictReader(open(pathlib.Path(data_dir) / 'subject-info.csv'))}


class ECGRecord:
    """One record, one lead, over a fixed window."""

    def __init__(self, data_dir, record_id, channel, window_s):
        self.record_id = record_id
        hdr = read_header(pathlib.Path(data_dir) / f'{record_id}.hea')
        names = [s['name'] for s in hdr['signals']]
        if channel not in names:
            raise SystemExit(f'record {record_id} has no channel {channel!r}; has {names}')
        sig = hdr['signals'][names.index(channel)]
        if sig['fmt'] != '16':
            raise SystemExit(f'record {record_id}: format {sig["fmt"]} not supported')
        self.fs, self.gain, self.baseline = hdr['fs'], sig['gain'], sig['baseline']

        raw = np.fromfile(pathlib.Path(data_dir) / sig['file'], dtype='<i2')
        if raw.size != hdr['n'] * hdr['nsig']:
            raise SystemExit(f'record {record_id}: header says {hdr["n"]:,} samples, '
                             f'file holds {raw.size // hdr["nsig"]:,}')
        adc = raw.reshape(-1, hdr['nsig'])[:, names.index(channel)]
        n_win = int(round(window_s * self.fs))
        if n_win > adc.size:
            raise SystemExit(f'record {record_id}: {adc.size / self.fs:.0f} s, shorter than '
                             f'the {window_s} s window')
        self.adc = adc[:n_win].astype(np.int64)

    @property
    def n(self):
        return int(self.adc.size)

    def value(self):
        """The samples in mV."""
        return (self.adc - self.baseline) / self.gain


class ECGChain:
    """Walks the listed records and yields one event per sample."""

    def __init__(self, data_dir, records, channel, window_s, max_steps=None):
        self.data_dir = pathlib.Path(data_dir)
        self.records = list(records)
        self.channel = channel
        self.window_s = window_s
        self.max_steps = max_steps
        self.subjects = read_subjects(self.data_dir)
        missing = [r for r in self.records if r not in self.subjects]
        if missing:
            raise SystemExit(f'records not in subject-info.csv: {missing}')

    @property
    def record_length(self):
        return int(round(self.window_s * 1000))

    @property
    def total_steps(self):
        return self.record_length * len(self.records)

    def events(self):
        step = 0
        for rid in self.records:
            rec = ECGRecord(self.data_dir, rid, self.channel, self.window_s)
            s = self.subjects[rid]
            band = AGE_BANDS.get(int(s['Age_group'])) if s['Age_group'] != 'NaN' else 'unknown'
            v = rec.value()
            for k in range(rec.n):
                if self.max_steps is not None and step >= self.max_steps:
                    return
                yield {'step': step, 'record_id': rid, 'age_band': band,
                       'sample_index': k, 'adc': int(rec.adc[k]), 'value': float(v[k])}
                step += 1


if __name__ == '__main__':
    import sys
    from config import ECG_CONFIG as C
    rid = sys.argv[1] if len(sys.argv) > 1 else read_records(C['records'])[0]
    r = ECGRecord(C['data_dir'], rid, C['channel'], C['window_s'])
    v = r.value()
    print(f'record   {rid}\nchannel  {C["channel"]}\nfs       {r.fs:.0f} Hz\n'
          f'samples  {r.n:,} ({r.n / r.fs:.0f} s)\nvalue    {v.min():+.3f} .. {v.max():+.3f} mV')
