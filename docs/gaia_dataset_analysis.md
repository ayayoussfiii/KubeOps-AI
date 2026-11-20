# Étude du dataset GAIA

Date de consultation : 20 novembre 2026. Domaine : Data Engineering, Graphes et GNN.

## 1. Environnement vérifié

- Projet : `C:\Users\ep\Documents\KubeOps-AI`.
- Branche active : `feature/p1-data-simulation`.
- État initial : arbre de travail propre ; seul fichier applicatif présent : `README.md`.
- Le README local présente un prototype de diagnostic par GNN ; ses exemples de commandes ne constituent pas une implémentation existante.
- Cette tâche produit uniquement ce document. Aucun dataset, modèle ou pipeline n'est créé ; aucune opération de commit, push, merge ou changement de branche n'est effectuée.

## 2. Méthode et niveau de preuve

**Vérifié documentaire** : contenu visible du README officiel et des listes de fichiers GitHub. Cela confirme une description publiée, sans vérifier les données contenues dans les archives.

**Proposition** : choix envisagé pour KubeOps-AI, à tester ultérieurement.

**Non vérifié** : propriété nécessitant un échantillon extrait ou une documentation complémentaire.

L'accès web au dépôt officiel a fonctionné. Les requêtes directes PowerShell vers l'API GitHub et les fichiers bruts ont échoué avec une erreur de connexion ; la consultation a continué via l'outil web. Aucun téléchargement d'archive ni clonage de GAIA n'a été réalisé. Certaines pages de répertoires sont fournies par le moteur web depuis son cache ; aucun SHA de révision n'a été obtenu. L'étude n'est donc pas un inventaire figé à un commit.

## 3. Structure et fichiers pertinents

Structure observée sur les pages GitHub, branche `main` :

```text
GAIA-DataSet/
├── README.md
├── LICENSE
├── .gitattributes
├── .gitignore
├── MicroSS/
│   ├── MicroSS system description.docx
│   ├── metric/    metric_split.z01 … metric_split.z34, metric_split.zip
│   ├── trace/     trace_split.z01 … trace_split.z31, trace_split.zip
│   ├── business/  business_split.z01 … business_split.z45, business_split.zip
│   └── run/       run.zip
└── Companion_Data/
    ├── metric_detection.zip
    ├── metric_forecast.zip
    └── log.zip
```

Sources : [racine officielle](https://github.com/CloudWise-OpenSource/GAIA-DataSet), [MicroSS](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/MicroSS), [metric](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/MicroSS/metric), [trace](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/MicroSS/trace), [business](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/MicroSS/business), [run](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/MicroSS/run), [Companion_Data](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/Companion_Data).

Les extensions suggèrent des archives ZIP fractionnées pour trois modalités. Par prudence, prévoir que les volumes associés puissent être nécessaires à l'extraction ; un fichier `.z01` ne doit pas être traité comme un CSV autonome. La taille des archives, leurs membres internes et leur extractibilité n'ont pas été vérifiés. Le fichier de description du système a été repéré, mais son contenu n'a pas été consulté.

## 4. Types, formats et colonnes documentés

Les informations suivantes proviennent du [README officiel, sections MicroSS et Companion Data](https://github.com/CloudWise-OpenSource/GAIA-DataSet/blob/main/README.md). Les colonnes sont documentées, sans contrôle des en-têtes réels.

| Modalité | Colonnes documentées |
| --- | --- |
| MicroSS metric | `timestamp`, `value` |
| MicroSS trace | `timestamp`, `host_ip`, `service_name`, `trace_id`, `span_id`, `parent_id`, `start_time`, `end_time`, `url`, `status_code`, `message` |
| MicroSS business et run | `datetime`, `service`, `message` |
| Companion metric_detection | `timestamp`, `value`, `label` |
| Companion metric_forecast | `timestamp`, `value` |

Les métriques MicroSS sont décrites en CSV, avec nœud, IP, indicateur et période dans le nom. Leur horodatage comporte 13 chiffres. Les traces viennent d'OpenTracing. Les dates textuelles sont documentées au format `YYYY-MM-DD hh:mm:ss`. Le README associe `status_code=200` au fonctionnement normal ; Companion utilise `label=0` normal et `1` anomalie.

`run` documente des injections : l'exemple mémoire contient service, début et durée dans `message`, pas dans des colonnes dédiées. Le changelog indique l'ajout d'août 2021 sans nouvelles traces. Companion propose aussi des tâches de parsing, d'anomalie sémantique et de NER sur les logs ; leurs schémas internes restent non inspectés.

## 5. Annotations et limites de leur interprétation

Les règles suivantes sont des propositions de préparation des données, pas des annotations déjà extraites :

- Parser les messages d'injection pour produire une table dérivée avec service ciblé, intervalle et catégorie. Conserver le texte et la provenance pour contrôler chaque extraction.
- Distinguer l'instant d'écriture du journal du début effectif de l'injection. Une ligne de journal peut être émise après le début de l'événement.
- Utiliser le service ciblé comme candidat à une étiquette de cause injectée. Une intervention simulée ne prouve pas à elle seule que tous les symptômes observés ont cette cause.
- Ne pas assimiler une réponse HTTP anormale à une annotation de cause racine : elle peut représenter un effet propagé.
- Ne pas considérer automatiquement toute période sans injection repérée comme saine. Vérifier la couverture des journaux, les effets retardés et les incidents simultanés.
- Exclure les messages révélant l'injection des caractéristiques du modèle. Ils servent à la supervision et leur présence en entrée créerait une fuite de cible.

**Non vérifié** : catalogue exhaustif des injections, nombre d'incidents, équilibre des classes, table de vérité terrain séparée, correspondance exacte entre service ciblé et cause réelle, qualité des labels. Aucune colonne `root_cause`, `fault_type` ou `incident_id` n'est supposée exister dans les données brutes.

## 6. Construction possible du graphe pour le GNN

L'ensemble de cette section décrit des choix proposés pour KubeOps-AI.

### Représentation recommandée pour le premier essai

Construire un graphe de services par fenêtre temporelle. Cette représentation limite le nombre de nœuds et permet de viser un classement des services suspects.

| Élément | Construction proposée | Vérification préalable |
| --- | --- | --- |
| Nœuds | Un nœud par service logique identifié par `service_name`, sauf si les données réelles montrent la nécessité de distinguer plusieurs instances ; conserver `host_ip` comme information complémentaire | Vérifier la stabilité de `service_name` et la nécessité éventuelle de distinguer les instances |
| Arêtes dirigées | Retrouver le span parent dans le même `trace_id`, puis relier son service au service enfant via `parent_id` et `span_id` | Contrôler unicité des identifiants, parents absents et traces incomplètes |
| Caractéristiques de nœuds | Nombre d'appels, proportion de réponses anormales, statistiques des durées calculées avec `end_time - start_time` | Contrôler dates, durées nulles/négatives, doublons et valeurs manquantes |
| Caractéristiques d'arêtes | Volume d'appels entre services, statistiques de latence et d'erreur | Définir les agrégations et le traitement des appels internes au même service |
| Métriques complémentaires | Moyenne, dispersion, maximum et variation d'indicateurs par fenêtre | Vérifier les indicateurs disponibles et la jointure hôte/service ; une métrique hôte n'est pas propre à un service |
| Logs complémentaires | Comptages de messages ou de gabarits par service et fenêtre | Valider parsing et alignement ; filtrer les messages d'injection |
| Cibles | Service ciblé par une injection validée ; éventuellement présence d'incident au niveau du graphe | Construire et relire les intervalles de supervision avant apprentissage |

Une relation d'appel est une dépendance observée, pas une preuve de causalité. Ne pas créer d'arête causale sur la seule proximité de deux horodatages. Une corrélation de métriques constituerait également une hypothèse de relation.

Pour une variante plus proche du graphe d'événements présenté dans le README local, utiliser un nœud par span, des arêtes parent-enfant et, si nécessaire, des arêtes temporelles explicitement typées. Cette variante serait plus volumineuse et n'est pas retenue comme première proposition.

### Alignement et évaluation à prévoir

- Vérifier le fuseau horaire des dates textuelles et l'unité effective des timestamps avant toute jointure ; le fuseau de la machine locale ne définit pas celui de GAIA.
- Proposer des fenêtres d'une minute, à ajuster selon fréquence réelle et durée des incidents. Préserver un masque de données manquantes.
- Définir une règle pour les fenêtres chevauchant partiellement une injection et pour les incidents simultanés ; conserver les cas ambigus hors de la supervision initiale.
- Séparer entraînement, validation et test par incidents et périodes disjointes. Éviter qu'une même trace ou des fenêtres recouvrantes apparaissent dans plusieurs partitions.
- Ajuster normalisation et vocabulaire uniquement sur l'entraînement. Comparer ultérieurement le GNN à une référence simple basée sur les taux d'erreur ou les latences.

## 7. Sous-ensemble minimal proposé

**Choix proposé : MicroSS, traces et enregistrements d'injection sur une même période de juillet 2021, à confirmer après inspection.** Companion n'est pas retenu pour ce premier graphe : l'étude n'a pas établi de jointure entre ses données et les services MicroSS.

1. Obtenir ultérieurement un petit extrait de `run` permettant d'identifier une injection isolée, son service et son intervalle.
2. Sélectionner les traces couvrant cet intervalle, avec environ 15 minutes avant et après comme point de départ ajustable.
3. Garder les traces complètes de la fenêtre, y compris les services voisins, afin de préserver les relations parent-enfant. Viser quelques services connectés si la topologie le permet, sans tronquer arbitrairement les parents.
4. Ajouter une fenêtre de référence sans injection repérée, après vérification de sa couverture. Commencer avec les caractéristiques issues des traces ; ajouter ensuite seulement deux ou trois indicateurs réellement disponibles si nécessaire.

Ce minimum permettrait de vérifier parsing, jointures, graphe et attribution d'étiquettes. **Un seul incident ne suffit pas à entraîner et évaluer un diagnostic généralisable.** Pour un essai supervisé, rechercher ensuite plusieurs incidents indépendants, idéalement sur plusieurs services, permettant les partitions décrites plus haut. Aucun nombre d'incidents disponible n'est garanti ici.

La petite taille de l'extrait final ne garantit pas un petit téléchargement : les archives fractionnées peuvent imposer une acquisition volumineuse. Aucun extrait indépendant téléchargeable n'a été identifié dans les pages consultées. Avant acquisition, vérifier les tailles et la possibilité d'obtenir un extrait ciblé ; ne pas lancer le téléchargement global par défaut.

## 8. Informations encore indisponibles et incohérences

- En-têtes réels, séparateurs, encodages, noms internes et tailles décompressées des fichiers.
- Fréquences d'échantillonnage, unités des indicateurs, taux de données manquantes et synchronisation des modalités.
- Inventaire des services, topologie complète, déploiement Kubernetes éventuel et correspondances avec les hôtes. Ne pas supposer l'existence de pods ou de namespaces.
- Disponibilité de traces pour chaque intervalle candidat et complétude des chaînes parent-enfant.
- Performances possibles du GNN : aucune expérience n'a été menée.
- Le [README officiel](https://github.com/CloudWise-OpenSource/GAIA-DataSet/blob/main/README.md) annonce Apache 2.0, tandis que le [fichier LICENSE consulté](https://github.com/CloudWise-OpenSource/GAIA-DataSet/blob/main/LICENSE) contient GNU GPL version 2. Cette contradiction est constatée, sans conclusion sur les droits applicables aux différentes données ; la clarifier avant redistribution d'extraits.

## 9. Prochaines étapes proposées

1. Fixer la révision GAIA étudiée et inventorier les tailles sans récupérer les archives.
2. Consulter la description MicroSS pour documenter les entités et dépendances attendues.
3. Déterminer un mode d'accès raisonnable à un extrait de traces et d'injections synchronisées.
4. Inspecter quelques lignes réelles et compléter le dictionnaire des données avec formats, unités, fuseau et clés de jointure.
5. Valider manuellement une première injection et ses fenêtres de contexte ; définir les cibles et les exclusions.
6. Étendre à des incidents indépendants avant d'implémenter le graphe, puis le prototype de GNN dans une tâche ultérieure.

## 10. Sources consultées et portée

Toutes les sources ci-dessous appartiennent au dépôt officiel CloudWise-OpenSource/GAIA-DataSet ; consultation du 20 novembre 2026.

| Source | Usage dans cette étude |
| --- | --- |
| [README officiel](https://github.com/CloudWise-OpenSource/GAIA-DataSet/blob/main/README.md) | Types, colonnes documentées, annotations, changelog et annonce de licence ; lecture du rendu à la racine |
| [Racine du dépôt](https://github.com/CloudWise-OpenSource/GAIA-DataSet) | Répertoires et fichiers racine |
| [MicroSS](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/MicroSS) | Modalités et présence du document de description |
| [MicroSS/metric](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/MicroSS/metric) | Noms des archives de métriques |
| [MicroSS/trace](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/MicroSS/trace) | Noms des archives de traces |
| [MicroSS/business](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/MicroSS/business) | Noms des archives de logs métier |
| [MicroSS/run](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/MicroSS/run) | Présence de run.zip |
| [Companion_Data](https://github.com/CloudWise-OpenSource/GAIA-DataSet/tree/main/Companion_Data) | Présence des trois archives complémentaires |
| [LICENSE](https://github.com/CloudWise-OpenSource/GAIA-DataSet/blob/main/LICENSE) et son [contenu brut](https://raw.githubusercontent.com/CloudWise-OpenSource/GAIA-DataSet/refs/heads/main/LICENSE) | Constat du texte GPL-2.0 |

Les propositions de graphe, de sélection et d'évaluation sont des recommandations de travail pour l'équipe KubeOps-AI ; elles ne sont pas présentées comme des résultats validés sur GAIA.
