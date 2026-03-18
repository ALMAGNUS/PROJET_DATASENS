# 📋 Dossier E1 — Guide 3 : Préparer le dataset pour l'IA (E2)

**Pour le jury** : Les données GOLD produites par E1 sont partitionnées par date. Pour l’IA, nous les fusionnons en un dataset unique (GoldAI) en utilisant une approche incrémentale : seules les nouvelles dates sont intégrées, grâce à des métadonnées. Le dataset est dédupliqué, puis divisé en train/validation/test pour l’entraînement et l’évaluation des modèles. Cette chaîne garantit un flux reproductible et scalable, depuis E1 jusqu’au fine-tuning CamemBERT/FlauBERT et à l’inférence via l’API E2. Les scripts décrits sont ceux utilisés en production.

**Objectif** : Transformer les données GOLD E1 en dataset exploitable par l'IA E2. Méthodes pro : incrémental, déduplication, split, traçabilité.

---

## 1. Chaîne de production

Le pipeline E1 produit des fichiers GOLD partitionnés par date. Pour l'entraînement ou l'inférence des modèles IA, nous avons besoin d'un dataset unique, dédupliqué et découpé en ensembles train/validation/test. La chaîne ci-dessous décrit les scripts qui réalisent cette transformation, de manière incrémentale et reproductible.

```
E1 GOLD (data/gold/date=YYYY-MM-DD/) 
    → merge_parquet_goldai.py 
    → GoldAI (data/goldai/merged_all_dates.parquet)
    → create_ia_copy.py 
    → Split train/val/test (data/goldai/ia/)
    → finetune_sentiment.py / goldai_loader
```

---

## 2. Étape 1 : Fusion incrémentale GOLD → GoldAI

### 2.1 Pourquoi GoldAI ?

Les fichiers GOLD sont stockés par date pour faciliter les mises à jour incrémentales. L'IA exige un seul fichier fusionné pour charger facilement tout le corpus. GoldAI est ce fichier intermédiaire : il agrège les GOLD tout en conservant un mécanisme incrémental (via `metadata.json`) pour ne pas refusionner les dates déjà traitées.

- **GOLD** : Fichiers partitionnés par date (un Parquet par jour)
- **GoldAI** : Un seul fichier fusionné + dédupliqué pour l'IA
- **Incrémental** : Ne refusionne que les nouvelles dates (metadata.json)

### 2.2 Commande

```bash
python scripts/merge_parquet_goldai.py
```

### 2.3 Astuces pro

| Astuce | Rôle |
|--------|------|
| **Métadonnées** | `metadata.json` stocke `dates_included`, `total_rows`, `last_merge` → évite de refusionner les anciennes dates |
| **Déduplication** | Par colonne `id`, keep='last' (plus récent gagne) |
| **Backup** | Avant écrasement de `merged_all_dates.parquet` → `merged_all_dates_v{N}.parquet` |
| **PySpark** | Utilisation de Spark pour les gros volumes (scalable) |

### 2.4 Structure GoldAI

```
data/goldai/
├── metadata.json           # dates_included, total_rows, version
├── merged_all_dates.parquet # Dataset fusionné pour l'IA
└── date=YYYY-MM-DD/
    └── goldai.parquet      # Partition par date (optionnel)
```

---

## 3. Étape 2 : Copie IA avec split train/val/test

### 3.1 Commande

```bash
# Split par défaut : 80% train, 10% val, 10% test
python scripts/create_ia_copy.py

# Split personnalisé
python scripts/create_ia_copy.py --train 0.7 --val 0.15 --test 0.15
```

### 3.2 Astuces pro

| Astuce | Rôle |
|--------|------|
| **Shuffle** | `df.sample(frac=1, random_state=42)` → reproductibilité |
| **Copie annotée** | `merged_all_dates_annotated.parquet` = même contenu, prêt pour ML |
| **Split** | train/val/test évite le data leakage et permet l'évaluation |

### 3.3 Structure IA

```
data/goldai/ia/
├── merged_all_dates_annotated.parquet  # Copie complète
├── train.parquet
├── val.parquet
└── test.parquet
```

---

## 4. Étape 3 : Charger GoldAI pour l'inférence

### 4.1 Via goldai_loader (Python)

Le module `goldai_loader` fournit des fonctions pour charger le dataset GoldAI dans un DataFrame pandas et en extraire les paires (id, title, content) nécessaires à l'inférence. On peut limiter le nombre de lignes chargées pour des tests rapides.

```python
from src.ml.inference.goldai_loader import load_goldai, get_goldai_texts

# Charger tout le merged
df = load_goldai(limit=1000, use_merged=True)

# Extraire (id, title, content) pour l'inférence
texts = get_goldai_texts(df)
for id_, title, content in texts[:5]:
    print(f"{id_}: {title[:50]}...")
```

### 4.2 Via l'API E2

L'API E2 expose un endpoint dédié qui applique le modèle de sentiment (keyword ou ML fine-tuné) sur un échantillon du dataset GoldAI. L'authentification par Bearer token est requise.

```http
GET /api/v1/ai/ml/sentiment-goldai?limit=50
Authorization: Bearer YOUR_TOKEN
```

Retourne les prédictions de sentiment sur un échantillon GoldAI.

---

## 5. Étape 4 : Fine-tuning (optionnel)

### 5.1 Prérequis

- GoldAI fusionné + `create_ia_copy.py` exécuté
- PyTorch, Transformers (CamemBERT / FlauBERT)

### 5.2 Commande

```bash
# Fine-tuning CamemBERT (défaut)
python scripts/finetune_sentiment.py --model camembert --epochs 3

# Évaluation uniquement (sans entraînement)
python scripts/finetune_sentiment.py --eval-only
```

### 5.3 Chemin du modèle fine-tuné

Ajouter dans `.env` :
```
SENTIMENT_FINETUNED_MODEL_PATH=models/camembert-sentiment-finetuned
```

---

## 6. Checklist pro — ordre des opérations

1. **Lancer le pipeline E1** : `python main.py` (génère GOLD par date)
2. **Fusionner** : `python scripts/merge_parquet_goldai.py`
3. **Vérifier** : `data/goldai/merged_all_dates.parquet` existe
4. **Split IA** : `python scripts/create_ia_copy.py`
5. **Fine-tuning** (optionnel) : `python scripts/finetune_sentiment.py`
6. **API** : L'endpoint `/api/v1/ai/ml/sentiment-goldai` lit GoldAI

---

## 7. Scripts de référence

| Script | Rôle |
|--------|------|
| `merge_parquet_goldai.py` | Fusion incrémentale GOLD → GoldAI |
| `create_ia_copy.py` | Split train/val/test |
| `finetune_sentiment.py` | Fine-tuning CamemBERT/FlauBERT |

| Module | Rôle |
|--------|------|
| `src/ml/inference/goldai_loader.py` | Charge GoldAI pour l'inférence |
| `src/ml/inference/sentiment.py` | Inférence sentiment (keyword ou ML) |

---

## 8. Colonnes attendues dans GoldAI

- `id`, `source`, `title`, `content`, `url`
- `fingerprint`, `collected_at`, `quality_score`
- `topic_1`, `topic_1_score`, `topic_2`, `topic_2_score`
- `sentiment`, `sentiment_score`
