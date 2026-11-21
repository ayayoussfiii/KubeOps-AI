import sys, json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np, torch
from torch_geometric.loader import DataLoader
from gnn.dataset import load_csv
from gnn.model import RootCauseGNN

HERE = Path(__file__).resolve().parent
data, groups = load_csv("data/mini_incidents.csv")
sp = np.load(HERE / "splits.npz")
model = RootCauseGNN()
model.load_state_dict(torch.load(HERE / "model.pt"))
model.eval()

L, Y = [], []
with torch.no_grad():
    for b in DataLoader([data[i] for i in sp["cal"]], batch_size=64):
        L.append(torch.log_softmax(model(b).double(), dim=1).numpy())
        Y.append(b.y.numpy())
nll = -np.concatenate(L)
Y = np.concatenate(Y)
scores = nll[np.arange(len(Y)), Y]

cfg = {}
for alpha in (0.1, 0.05, 0.01):
    n = len(scores)
    cfg[str(alpha)] = float(np.quantile(scores, min(np.ceil((n + 1) * (1 - alpha)) / n, 1.0), method="higher"))
json.dump(cfg, open(HERE / "conformal.json", "w"))
print("seuils conformes sauvegardes :", cfg)
