import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np, torch
import mapie
from sklearn.base import BaseEstimator, ClassifierMixin
from torch_geometric.data import Data
from common.graph import NODES, edge_index
from gnn.dataset import load_csv
from gnn.model import RootCauseGNN

HERE = Path(__file__).resolve().parent
print("version MAPIE :", mapie.__version__)

data, groups = load_csv("data/mini_incidents.csv")
sp = np.load(HERE / "splits.npz")
model = RootCauseGNN()
model.load_state_dict(torch.load(HERE / "model.pt"))
model.eval()
EI = edge_index()

def to_xy(ids):
    X = np.stack([data[i].x.numpy().reshape(-1) for i in ids]).astype(np.float32)
    y = np.array([int(data[i].y) for i in ids])
    return X, y

class GNNWrapper(ClassifierMixin, BaseEstimator):
    """Enveloppe sklearn autour du GNN PyTorch (entree : 15 variables normalisees)."""
    def __init__(self, n_classes=len(NODES)):
        self.n_classes = n_classes
        self.classes_ = np.arange(n_classes)
    def __sklearn_is_fitted__(self):
        return True
    def fit(self, X, y):
        return self
    def predict_proba(self, X):
        P = []
        with torch.no_grad():
            for row in np.asarray(X, dtype=np.float32):
                d = Data(x=torch.tensor(row.reshape(len(NODES), -1)), edge_index=EI)
                P.append(torch.softmax(model(d).double(), dim=1)[0].numpy())
        return np.array(P)
    def predict(self, X):
        return self.predict_proba(X).argmax(1)

Xc, yc = to_xy(sp["cal"])
Xt, yt = to_xy(sp["test"])
est = GNNWrapper()
levels = [0.9, 0.95, 0.99]

def report(name, sets):            # sets : (n, 5, len(levels)) booleens
    for k, lv in enumerate(levels):
        s = sets[:, :, k]
        cov = s[np.arange(len(yt)), yt].mean()
        size = s.sum(1)
        print(f"{name} niveau {lv}: couverture {cov:.3f} | taille moyenne {size.mean():.2f} | vides {(size == 0).mean():.3f} | escalade {(size != 1).mean():.3f}")

# --- MAPIE ---
try:
    from mapie.classification import SplitConformalClassifier
    scc = SplitConformalClassifier(estimator=est, confidence_level=levels,
                                   conformity_score="lac", prefit=True)
    scc.conformalize(Xc, yc)
    _, sets = scc.predict_set(Xt)
    report("MAPIE (v1)  ", np.asarray(sets, dtype=bool))
except ImportError:
    from mapie.classification import MapieClassifier
    mc = MapieClassifier(estimator=est, cv="prefit", method="lac")
    mc.fit(Xc, yc)
    _, sets = mc.predict(Xt, alpha=[1 - l for l in levels])
    report("MAPIE (v0.x)", np.asarray(sets, dtype=bool))

# --- Version manuelle, meme decoupage ---
Pc, Pt = est.predict_proba(Xc), est.predict_proba(Xt)
nll_c = -np.log(np.clip(Pc[np.arange(len(yc)), yc], 1e-300, None))
nll_t = -np.log(np.clip(Pt, 1e-300, None))
man = []
for lv in levels:
    n = len(nll_c)
    q = np.quantile(nll_c, min(np.ceil((n + 1) * lv) / n, 1.0), method="higher")
    man.append(nll_t <= q)
report("Manuel      ", np.stack(man, axis=2))
