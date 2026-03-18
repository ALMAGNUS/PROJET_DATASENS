# Plan d'action – Streamlit Cockpit & E2

## Objectif

Le Streamlit doit montrer tout le traitement des données, la visualisation des bases, et notamment :
1. **L'addition quotidienne des Parquet** dans le fichier GoldAI
2. **La création de la copie IA** pour tester la prédiction (split train/val/test)

---

## Flux des données (à visualiser)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXTRACTION (E1)                                                            │
│  Sources → datasens.db (SQLite buffer quotidien)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXPORT PARQUET                                                              │
│  data/gold/date=YYYY-MM-DD/articles.parquet  (quotidien)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FUSION GOLDAI (merge_parquet_goldai.py)                                     │
│  • Partitions : data/goldai/date=YYYY-MM-DD/goldai.parquet                   │
│  • Fusion : merged_all_dates.parquet (addition incrémentale)                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌──────────────────────────────┐    ┌──────────────────────────────────────────┐
│  MONGODB (stockage long terme)│    │  COPIE IA                                │
│  GridFS Parquet               │    │  data/goldai/ia/                         │
│  Backup manuel ou auto         │    │  • merged_all_dates_annotated.parquet   │
└──────────────────────────────┘    │  • split train/val/test pour prédiction │
                                     └──────────────────────────────────────────┘
```

---

## Bases de données

| Base | Rôle |
|------|------|
| **datasens.db** (SQLite) | Buffer quotidien : extraction, tagging, sentiment |
| **MongoDB** | Stockage long terme des Parquet (archivage) |

---

## Checklist Streamlit

### Onglet / Vue Flux Parquet
- [x] Schéma visuel du flux
- [x] Dates incluses dans GoldAI (metadata.json)
- [x] Nombre de lignes par date
- [x] Taille merged_all_dates.parquet
- [x] Bouton « Fusion GoldAI » pour ajouter les nouvelles dates

### Vue bases
- [x] SQLite : tables, comptages
- [x] MongoDB : fichiers GridFS
- [x] Agrégation RAW/SILVER/GOLD

### Copie IA (prédiction)
- [x] Script `scripts/create_ia_copy.py` : merged_all_dates_annotated.parquet + split train/val/test
- [x] Bouton « Créer copie IA (split) » dans Pilotage
- [x] Affichage dans Flux Parquet (onglet 3)

### E2 à finaliser
- [ ] API endpoints documentés
- [ ] Endpoint /ai/ml/sentiment-goldai visible
- [ ] Tests de prédiction

---

## Priorités

1. **Flux Parquet** : Nouvel onglet montrant l’addition quotidienne
2. **Copie IA** : Script + bouton pour créer le split
3. **Visualisation** : Améliorer les tables/colonnes dans Datasets
