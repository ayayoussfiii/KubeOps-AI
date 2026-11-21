import numpy as np, pandas as pd, torch
from torch_geometric.data import Data
from common.graph import NODES, FEATURES, IDX, edge_index, columns

def normalize(a):
    a = a.copy()
    a[..., 0] /= 100
    a[..., 1] = np.log1p(a[..., 1]) / np.log1p(6000)
    a[..., 2] /= 10
    return a

def load_csv(path):
    df = pd.read_csv(path)
    X = df[columns()].to_numpy(dtype=np.float32).reshape(-1, len(NODES), len(FEATURES))
    X = normalize(X)
    y = df["Root_Cause"].map(IDX).to_numpy()
    ei = edge_index()
    data = [Data(x=torch.tensor(X[i]), edge_index=ei, y=torch.tensor(int(y[i])))
            for i in range(len(df))]
    return data, df["scenario_id"].to_numpy()
