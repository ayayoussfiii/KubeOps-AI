import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np, torch
from sklearn.model_selection import GroupShuffleSplit
from torch_geometric.loader import DataLoader
from gnn.dataset import load_csv
from gnn.model import RootCauseGNN

data, groups = load_csv("data/mini_incidents.csv")
sp = np.load("gnn/splits.npz")
model = RootCauseGNN()
model.load_state_dict(torch.load("gnn/model.pt"))
model.eval()

pool = np.concatenate([sp["cal"], sp["test"]])
L, Y = [], []
with torch.no_grad():
    for b in DataLoader([data[i] for i in pool], batch_size=64):
        L.append(torch.log_softmax(model(b).double(), dim=1).numpy())
        Y.append(b.y.numpy())
nll = -np.concatenate(L)          # (N, 5) : -log p, pas de saturation
Y = np.concatenate(Y)
gp = groups[pool]

for alpha in (0.1, 0.05, 0.01):
    cov, size, empty, esc = [], [], [], []
    for seed in range(200):
        c, t = next(GroupShuffleSplit(1, test_size=0.5, random_state=seed).split(pool, groups=gp))
        sc = nll[c, Y[c]]
        n = len(sc)
        q = np.quantile(sc, min(np.ceil((n + 1) * (1 - alpha)) / n, 1.0), method="higher")
        sets = nll[t] <= q
        s = sets.sum(1)
        cov.append(sets[np.arange(len(t)), Y[t]].mean())
        size.append(s.mean()); empty.append((s == 0).mean()); esc.append((s != 1).mean())
    print(f"alpha={alpha}: couverture {np.mean(cov):.3f} +/- {np.std(cov):.3f} (cible {1-alpha:.2f}) | taille moyenne {np.mean(size):.2f} | ensembles vides {np.mean(empty):.3f} | escalade (taille != 1) {np.mean(esc):.3f}")
