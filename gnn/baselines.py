import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np, torch
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from torch_geometric.loader import DataLoader
from gnn.dataset import load_csv
from gnn.model import RootCauseGNN

HERE = Path(__file__).resolve().parent
data, groups = load_csv("data/mini_incidents.csv")
sp = np.load(HERE / "splits.npz")

def xy(ids):
    X = np.stack([data[i].x.numpy().reshape(-1) for i in ids])
    y = np.array([int(data[i].y) for i in ids])
    return X, y

Xtr, ytr = xy(sp["train"]); Xte, yte = xy(sp["test"])

# Baselines : 15 variables a plat, sans structure de graphe
for name, clf in [("Regression logistique", LogisticRegression(max_iter=2000)),
                  ("Random forest", RandomForestClassifier(n_estimators=200, random_state=0))]:
    clf.fit(Xtr, ytr)
    print(f"{name:22s} precision test : {clf.score(Xte, yte):.3f}")

# GNN
model = RootCauseGNN()
model.load_state_dict(torch.load(HERE / "model.pt"))
model.eval()
ok = n = 0
with torch.no_grad():
    for b in DataLoader([data[i] for i in sp["test"]], batch_size=64):
        ok += (model(b).argmax(1) == b.y).sum().item(); n += b.y.numel()
print(f"{'GNN (GCN)':22s} precision test : {ok / n:.3f}")
