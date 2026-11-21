import sys, json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np, torch
from torch_geometric.data import Data
from common.graph import NODES, FEATURES, edge_index
from gnn.dataset import normalize
from gnn.model import RootCauseGNN

HERE = Path(__file__).resolve().parent
_state = {}

def _load():
    if not _state:
        model = RootCauseGNN()
        model.load_state_dict(torch.load(HERE / "model.pt"))
        model.eval()
        _state["model"] = model
        _state["cfg"] = json.load(open(HERE / "conformal.json"))
    return _state["model"], _state["cfg"]

def predict_root_cause(metrics, alpha=0.05):
    """metrics : dict plat {"Frontend_cpu": ..., "Frontend_latency": ..., "Frontend_error": ...}
    Retourne (service le plus probable, sa probabilite, ensemble de prediction conforme)."""
    model, cfg = _load()
    x = np.array([[metrics[f"{n}_{f}"] for f in FEATURES] for n in NODES], dtype=np.float32)[None]
    x = normalize(x)[0]
    data = Data(x=torch.tensor(x), edge_index=edge_index())
    with torch.no_grad():
        logp = torch.log_softmax(model(data).double(), dim=1)[0].numpy()
    best = int(np.argmax(logp))
    ensemble = [NODES[i] for i in range(len(NODES)) if -logp[i] <= cfg[str(alpha)]]
    return NODES[best], float(np.exp(logp[best])), ensemble

def needs_human(ensemble):
    """Escalade vers un humain si l'ensemble n'a pas exactement un seul service."""
    return len(ensemble) != 1

if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("data/mini_incidents.csv")
    row = df.iloc[0].to_dict()
    service, p, ens = predict_root_cause(row)
    print("Vraie cause :", row["Root_Cause"])
    print("Prediction  :", service, f"{p:.1%}", "| ensemble :", ens, "| humain :", needs_human(ens))
    normal = {f"{n}_cpu": 40.0 for n in NODES}
    normal.update({f"{n}_latency": 20.0 for n in NODES})
    normal.update({f"{n}_error": 0.1 for n in NODES})
    service, p, ens = predict_root_cause(normal)
    print("Systeme sain :", service, f"{p:.1%}", "| ensemble :", ens, "| humain :", needs_human(ens))
