# Bloc GNN et sûreté (cause racine + prédiction conforme)

Ce bloc localise le service à l'origine d'une panne dans un graphe de microservices, et indique quand il faut demander l'avis d'un humain. **Toutes les données sont simulées** (`data/make_mini_csv.py`) : les chiffres ci-dessous ne disent rien de ce que donnerait un vrai cluster.

## Contenu

| Fichier | Rôle |
|---|---|
| `common/graph.py` | Nœuds, arêtes, variables et `edge_index` (ordre des nœuds partagé par toute l'équipe) |
| `data/make_mini_csv.py` | Génère `data/mini_incidents.csv` : pannes sur les 5 services, avec cascade de symptômes et services « distracteurs » |
| `gnn/dataset.py` | Lecture du CSV, normalisation, conversion en objets PyTorch Geometric |
| `gnn/model.py` | GCN à 2 couches qui renvoie un score par nœud (le nœud au score maximal est la cause racine) |
| `gnn/train.py` | Entraînement, découpage entraînement / calibration / test **par scénario de panne** |
| `gnn/conformal.py` | Prédiction conforme manuelle, moyenne sur 200 redécoupages |
| `gnn/calibrate.py` | Calcule et sauvegarde les seuils conformes (`conformal.json`) |
| `gnn/predict.py` | `predict_root_cause(metrics)` et `needs_human(ensemble)` |
| `gnn/mapie_check.py` | Vérification avec MAPIE 1.6.0 |

## Exécution

```cmd
python data\make_mini_csv.py
python gnn\train.py
python gnn\calibrate.py
python gnn\predict.py
```

`model.pt`, `splits.npz` et `conformal.json` ne sont pas versionnés : il faut relancer ces étapes après tout changement du CSV.

## Interface pour l'orchestration

```python
from gnn.predict import predict_root_cause, needs_human

service, proba, ensemble = predict_root_cause(metrics, alpha=0.05)
if needs_human(ensemble):
    ...  # escalade vers un humain
```

`metrics` est un dictionnaire plat `{noeud}_{cpu|latency|error}`. **Tester `needs_human` avant d'utiliser `service`** : quand l'ensemble est vide, le service renvoyé n'est pas fiable.

## Résultats (données simulées)

Prédiction conforme manuelle, couverture moyenne sur 200 découpages calibration / test par scénario :

| alpha | cible | couverture | escalade humaine |
|---|---|---|---|
| 0,10 | 0,90 | 0,903 ± 0,029 | 9,6 % |
| 0,05 | 0,95 | 0,953 ± 0,019 | 4,5 % |
| 0,01 | 0,99 | 0,993 ± 0,006 | 0,6 % |

Comparaison avec MAPIE 1.6.0 sur **un seul** découpage (couverture) :

| niveau | MAPIE | Manuel |
|---|---|---|
| 0,90 | 0,827 | 0,830 |
| 0,95 | 0,913 | 0,917 |
| 0,99 | 0,980 | 0,987 |

Les deux méthodes concordent à moins d'un point. Sur un seul découpage, la couverture peut tomber de quelques points sous la cible : la garantie conforme porte sur la moyenne, d'où le tableau précédent.

## Limites

- Données simulées, petit jeu de calibration (environ 150 scénarios).
- Les ensembles de prédiction ont une taille de 0 ou 1, jamais 2 : le modèle est très sûr ou pas du tout. La règle d'escalade revient donc à « ensemble vide ».
- Pas de classe « système sain » : un système sain donne en pratique un ensemble vide, donc une escalade.
- Avec des données moins faciles, il faudra recalibrer et réévaluer.
