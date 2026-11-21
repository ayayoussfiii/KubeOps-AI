import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np, pandas as pd, networkx as nx
from common.graph import NODES, EDGES

rng = np.random.default_rng(0)
G = nx.DiGraph(EDGES)
rows, sid = [], 0

for root in NODES:
    upstream = nx.ancestors(G, root)
    for _ in range(40):
        sid += 1
        weak_cpu = rng.random() < 0.3
        for _t in range(5):
            row = {"scenario_id": sid, "Root_Cause": root}
            root_lat = rng.normal(5000, 300)
            for n in NODES:
                cpu, lat, err = rng.normal(40, 5), rng.normal(20, 3), rng.normal(0.1, 0.03)
                if n == root:
                    cpu = rng.normal(65, 10) if weak_cpu else rng.normal(99, 1)
                    lat, err = root_lat, rng.normal(5, 0.8)
                elif n in upstream:
                    cpu = rng.normal(35, 5)
                    lat, err = root_lat + rng.normal(100, 30), rng.normal(4, 0.8)
                row[f"{n}_cpu"] = min(max(cpu, 0), 100)
                row[f"{n}_latency"] = max(lat, 1)
                row[f"{n}_error"] = max(err, 0)
            rows.append(row)

pd.DataFrame(rows).to_csv("data/mini_incidents.csv", index=False)
print(len(rows), "lignes ecrites")
