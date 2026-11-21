import torch

NODES = ["Frontend", "APIGateway", "Auth", "Payment", "Database"]
IDX = {n: i for i, n in enumerate(NODES)}
EDGES = [("Frontend", "APIGateway"), ("APIGateway", "Auth"),
         ("APIGateway", "Payment"), ("Auth", "Database"), ("Payment", "Database")]
FEATURES = ["cpu", "latency", "error"]

def columns():
    return [f"{n}_{f}" for n in NODES for f in FEATURES]

def edge_index(undirected=True):
    src = [IDX[a] for a, b in EDGES]
    dst = [IDX[b] for a, b in EDGES]
    if undirected:
        src, dst = src + dst, dst + src
    return torch.tensor([src, dst], dtype=torch.long)
