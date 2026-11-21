import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np, torch
from torch_geometric.loader import DataLoader
from gnn.dataset import load_csv
from gnn.model import RootCauseGNN

data, groups = load_csv("data/mini_incidents.csv")
sp = np.load("gnn/splits.npz")
model = RootCauseGNN()
model.load_state_dict(torch.load("gnn/model.pt"))
model.eval()

def probs(ids):
    P, Y = [], []
    with torch.no_grad():
        for b in DataLoader([data[i] for i in ids], batch_size=64):
            P.append(torch.softmax(model(b), dim=1).numpy()); Y.append(b.y.numpy())
    return np.concatenate(P), np.concatenate(Y)

Pc, Yc = probs(sp["cal"])
Pt, Yt = probs(sp["test"])

scores = 1 - Pc[np.arange(len(Yc)), Yc]
for alpha in (0.1, 0.05, 0.01):
    n = len(scores)
    q = np.quantile(scores, min(np.ceil((n + 1) * (1 - alpha)) / n, 1.0), method="higher")
    sets = Pt >= 1 - q
    coverage = sets[np.arange(len(Yt)), Yt].mean()
    size = sets.sum(1)
    print(f"alpha={alpha}: couverture {coverage:.3f} (cible {1-alpha:.2f}) | taille moyenne {size.mean():.2f} | escalade humaine (taille != 1) {(size != 1).mean():.3f}")
