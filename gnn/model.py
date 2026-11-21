import torch, torch.nn as nn, torch.nn.functional as F
from torch_geometric.nn import GCNConv

class RootCauseGNN(nn.Module):
    def __init__(self, in_dim=3, hidden=32, n_nodes=5):
        super().__init__()
        self.n_nodes = n_nodes
        self.conv1 = GCNConv(in_dim, hidden)
        self.conv2 = GCNConv(hidden, hidden)
        self.out = nn.Linear(hidden + in_dim, 1)

    def forward(self, data):
        h = F.relu(self.conv1(data.x, data.edge_index))
        h = F.relu(self.conv2(h, data.edge_index))
        h = torch.cat([h, data.x], dim=1)
        return self.out(h).view(-1, self.n_nodes)
