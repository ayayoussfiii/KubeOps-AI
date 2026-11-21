import numpy as np, networkx as nx, torch, torch.nn as nn, torch.nn.functional as F

def make_topology(rng, n):
    edges = []
    for j in range(1, n):
        k = 1 if rng.random() < 0.6 else 2
        parents = rng.choice(j, size=min(k, j), replace=False)
        edges += [(int(p), j) for p in parents]      # p appelle j
    return edges

def make_scenario(rng, n, edges):
    G = nx.DiGraph(); G.add_nodes_from(range(n)); G.add_edges_from(edges)
    root = int(rng.integers(n))
    anc = nx.ancestors(G, root)                      # services qui dependent de la cause racine
    x = np.stack([rng.normal(40, 10, n), rng.normal(20, 6, n), rng.normal(0.2, 0.1, n)], 1)
    root_lat = rng.normal(5000, 800)
    weak = rng.random() < 0.5
    x[root] = [rng.normal(55, 15) if weak else rng.normal(95, 5), root_lat, rng.normal(4.5, 1.5)]
    dist = nx.single_source_shortest_path_length(G.reverse(), root)
    for a in anc:
        lat = root_lat * (0.8 ** (dist[a] - 1)) * rng.uniform(0.6, 1.3)
        if rng.random() < 0.25:                      # service amont sans aucun symptome
            x[a] = [rng.normal(40, 10), rng.normal(20, 6), rng.normal(0.2, 0.1)]
        else:
            x[a] = [rng.normal(45, 12), lat, rng.normal(3.5, 1.5)]
    others = [v for v in range(n) if v != root and v not in anc]
    if others and rng.random() < 0.3:                # distracteur : CPU haute sans etre la cause
        d = int(rng.choice(others)); x[d, 0] = rng.normal(90, 8); x[d, 2] = rng.normal(3.0, 1.0)
    x[:, 0] = np.clip(x[:, 0], 0, 100) / 100
    x[:, 1] = np.log1p(np.clip(x[:, 1], 1, None)) / np.log1p(6000)
    x[:, 2] = np.clip(x[:, 2], 0, None) / 10
    return x.astype(np.float32), root

def build_set(rng, n_topo, n_per, size_range):
    samples = []
    for _ in range(n_topo):
        n = int(rng.integers(size_range[0], size_range[1] + 1))
        edges = make_topology(rng, n)
        ei = np.array(edges, dtype=np.int64).T
        for _ in range(n_per):
            x, r = make_scenario(rng, n, edges)
            samples.append((x, ei, r))
    return samples

def collate(samples):
    xs, eis, roots, batch, ptr, off = [], [], [], [], [0], 0
    for g, (x, ei, r) in enumerate(samples):
        n = len(x)
        xs.append(torch.tensor(x)); eis.append(torch.tensor(ei) + off)
        roots.append(off + r); batch += [g] * n; off += n; ptr.append(off)
    return torch.cat(xs), torch.cat(eis, 1), torch.tensor(roots), torch.tensor(batch), ptr

class Layer(nn.Module):
    def __init__(self, i, o, use_graph):
        super().__init__()
        self.use_graph = use_graph
        self.w_self = nn.Linear(i, o)
        self.w_succ = nn.Linear(i, o, bias=False)    # messages venant des services appeles
        self.w_pred = nn.Linear(i, o, bias=False)    # messages venant des appelants
    def forward(self, h, ei):
        out = self.w_self(h)
        if self.use_graph:
            src, dst = ei
            N = h.size(0)
            ones = torch.ones(src.size(0), 1)
            deg_s = torch.zeros(N, 1).index_add_(0, src, ones).clamp(min=1)
            deg_p = torch.zeros(N, 1).index_add_(0, dst, ones).clamp(min=1)
            succ = torch.zeros_like(h).index_add_(0, src, h[dst]) / deg_s
            pred = torch.zeros_like(h).index_add_(0, dst, h[src]) / deg_p
            out = out + self.w_succ(succ) + self.w_pred(pred)
        return F.relu(out)

class Net(nn.Module):
    def __init__(self, use_graph, hidden=32):
        super().__init__()
        self.l1 = Layer(3, hidden, use_graph); self.l2 = Layer(hidden, hidden, use_graph)
        self.head = nn.Linear(hidden + 3, 1)
    def forward(self, x, ei):
        h = self.l2(self.l1(x, ei), ei)
        return self.head(torch.cat([h, x], 1)).squeeze(1)

def group_logsoftmax(s, batch, G):
    m = torch.full((G,), -1e30).scatter_reduce(0, batch, s, reduce="amax", include_self=True)
    e = torch.exp(s - m[batch])
    z = torch.zeros(G).index_add_(0, batch, e)
    return s - m[batch] - torch.log(z[batch])

def accuracy(net, samples):
    net.eval(); ok = 0
    with torch.no_grad():
        for i in range(0, len(samples), 64):
            chunk = samples[i:i + 64]
            x, ei, roots, batch, ptr = collate(chunk)
            s = net(x, ei)
            for g in range(len(chunk)):
                ok += int(int(torch.argmax(s[ptr[g]:ptr[g + 1]])) == int(roots[g]) - ptr[g])
    return ok / len(samples)

def train(net, samples, rng, epochs=40, bs=32):
    opt = torch.optim.Adam(net.parameters(), lr=5e-3)
    for _ in range(epochs):
        net.train()
        order = rng.permutation(len(samples))
        for i in range(0, len(order), bs):
            chunk = [samples[j] for j in order[i:i + bs]]
            x, ei, roots, batch, ptr = collate(chunk)
            lp = group_logsoftmax(net(x, ei), batch, len(chunk))
            loss = -lp[roots].mean()
            opt.zero_grad(); loss.backward(); opt.step()

if __name__ == "__main__":
    res = {("sans", "meme taille"): [], ("sans", "plus grand"): [], ("avec", "meme taille"): [], ("avec", "plus grand"): []}
    for seed in range(3):
        rng = np.random.default_rng(seed)
        tr = build_set(rng, 40, 15, (5, 8))          # 600 pannes sur 40 topologies
        te_same = build_set(rng, 25, 8, (5, 8))      # topologies jamais vues, 5 a 8 services
        te_big = build_set(rng, 25, 8, (10, 12))     # topologies jamais vues, 10 a 12 services
        for name, ug in (("sans", False), ("avec", True)):
            torch.manual_seed(seed)
            net = Net(ug)
            train(net, tr, np.random.default_rng(seed))
            res[(name, "meme taille")].append(accuracy(net, te_same))
            res[(name, "plus grand")].append(accuracy(net, te_big))
        print("seed", seed, "termine", flush=True)
    for (name, tset), v in res.items():
        print(f"{name:5s} graphe | test {tset:12s}: {np.mean(v):.3f} +/- {np.std(v):.3f}")
