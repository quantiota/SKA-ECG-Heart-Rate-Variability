"""Timing file for add_replay.py: delta_t and beat index of every point of a cube.
The cube's points are matched to the run's steps on z (knowledge), so any first-step offset is found automatically.
Usage: python make_timing.py cube.html ecg_ska_results.csv.gz <record> <scale> timing.json"""
import sys, json
import numpy as np, pandas as pd
cube, csv, rec, scale, out = sys.argv[1:6]
s = open(cube).read(); i = s.find("const D ="); e = s.find("};", i) + 1
cz = np.array(json.loads(s[i + 9:e])["z"])
d = pd.read_csv(csv, dtype={"record_id": str})
d = d[(d.record_id == rec) & (d.input == "cdot_cos") & (d.scale == float(scale))].sort_values("event_index").reset_index(drop=True)
z = d.knowledge.round(2).to_numpy()
for off in range(0, len(z) - len(cz) + 1):
    if np.all(np.abs(z[off:off + len(cz)] - cz) < 0.006):
        break
else:
    sys.exit("the cube's points do not match this run")
sl = slice(off, off + len(cz))
json.dump({"dt": [round(float(x), 4) for x in d.delta_t.to_numpy()[sl]],
           "k": [int(x) for x in d.k.to_numpy()[sl]]}, open(out, "w"))
print(f"saved {out} | {len(cz)} points from step {off} | recording {d.delta_t.to_numpy()[sl].sum():.1f} s")
