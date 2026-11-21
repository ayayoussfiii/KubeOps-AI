import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np, torch, torch.nn.functional as F
from sklearn.model_selection import GroupShuffleSplit
from torch_geometric.loader import DataLoader
from gnn.dataset import load_csv
from gnn.model import RootCauseGNN

torch.manual_seed(0)
data, groups = load_csv("data/mini_incidents.csv")
idx = np.arange(len(data))

tr, rest = next(GroupShuffleSplit(1, test_size=0.4, random_state=0).split(idx, groups=groups))
cal_r, te_r = next(GroupShuffleSplit(1, test_size=0.5, random_state=0).split(rest, groups=groups[rest]))
cal, te = rest[cal_r], rest[te_r]

make = lambda ids, sh: DataLoader([data[i] for i in ids], batch_size=32, shuffle=sh)
train_dl, cal_dl, test_dl = make(tr, True), make(cal, False), make(te, False)

model = RootCauseGNN()
opt = torch.optim.Adam(model.parameters(), lr=1e-2)

def accuracy(dl):
    model.eval(); ok = n = 0
    with torch.no_grad():
        for b in dl:
            ok += (model(b).argmax(1) == b.y).sum().item(); n += b.y.numel()
    return ok / n

for epoch in range(1, 51):
    model.train()
    for b in train_dl:
        opt.zero_grad()
        F.cross_entropy(model(b), b.y).backward()
        opt.step()
    if epoch % 10 == 0:
        print(f"epoch {epoch:3d} | train {accuracy(train_dl):.3f} | test {accuracy(test_dl):.3f}")

torch.save(model.state_dict(), "gnn/model.pt")
np.savez("gnn/splits.npz", train=tr, cal=cal, test=te)
