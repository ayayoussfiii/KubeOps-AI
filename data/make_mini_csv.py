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
    others = [n for n in NODES if n != root and n not in upstream]
    for _ in range(150):
        sid += 1
        weak_cpu = rng.random() < 0.5
        distractor = rng.choice(NODES[:0] + [n for n in NODES if n != root]) if rng.random() < 0.3 else None
        for _t in range(2):
            row = {"scenario_id": sid, "Root_Cause": root}
            root_lat = rng.normal(5000, 500)
            for n in NODES:
                cpu, lat, err = rng.normal(40, 8), rng.normal(20, 5), rng.normal(0.2, 0.1)
                if n == root:
                    cpu = rng.normal(55, 15) if weak_cpu else rng.normal(95, 5)
                    lat, err = root_lat, rng.normal(4.5, 1.5)
                elif n in upstream:
                    cpu = rng.normal(45, 12)
                    lat, err = root_lat * rng.uniform(0.9, 1.3), rng.normal(4.0, 1.5)
                if n == distractor:
                    cpu, err = rng.normal(90, 8), rng.normal(3.0, 1.0)
                row[f"{n}_cpu"] = min(max(cpu, 0), 100)
                row[f"{n}_latency"] = max(lat, 1)
                row[f"{n}_error"] = max(err, 0)
            rows.append(row)

pd.DataFrame(rows).to_csv("data/mini_incidents.csv", index=False)
print(len(rows), "lignes ecrites")
