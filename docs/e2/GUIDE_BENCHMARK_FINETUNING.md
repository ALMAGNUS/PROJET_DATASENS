# Guide Benchmark & Fine-tuning — DataSens E2

Guide de référence pour piloter le benchmark des modèles de sentiment et le fine-tuning, niveau ingénieur.

---

## 1. D'où viennent les figures ?

Les figures dans `docs/e2/figures/` sont générées à partir des **fichiers JSON existants** :

| Fichier | Contenu |
|---|---|
| `docs/e2/AI_BENCHMARK_RESULTS.json` | Résultats du dernier benchmark (accuracy, F1, latence, per_class) |
| `docs/e2/TRAINING_RESULTS.json` | Résultats du dernier entraînement (quick ou full) — écrit par `finetune_sentiment.py` |
| `docs/e2/TRAINING_RESULTS_QUICK.json` | Legacy — utilisé en fallback si TRAINING_RESULTS.json absent |

**Commande de régénération :**
```bash
python scripts/plot_e2_results.py
```

Cette commande **lit** les JSON et **regénère** les PNG. Elle ne lance pas de benchmark ni d'entraînement. Pour obtenir des figures à jour :

1. Lancer le benchmark ou le fine-tuning
2. Les scripts mettent à jour les JSON (`finetune_sentiment.py` écrit `TRAINING_RESULTS.json` à la fin de chaque run)
3. Relancer `python scripts/plot_e2_results.py`

**Figures training vs benchmark :**
- Les figures `e2_training_{quick|full}_*.png` reflètent le **dernier entraînement** (quick ou full selon le mode).
- Les figures `e2_benchmark_*.png` reflètent le **dernier benchmark** (qui évalue le modèle fine-tuné actif).

---

## 2. Script de benchmark — commandes et métriques

### Commande de base

```bash
python scripts/ai_benchmark.py [OPTIONS]
```

### Options principales

| Option | Effet | Exemple |
|--------|-------|---------|
| *(aucune)* | Benchmark complet sur tout le test set | `python scripts/ai_benchmark.py` |
| `--max-samples N` | Limite à N exemples par classe (neg/neu/pos) | `--max-samples 200` → 600 ex. au total |
| `--output-json PATH` | Chemin de sortie JSON | `--output-json docs/e2/AI_BENCHMARK_RESULTS.json` |

### Exemples

```bash
# Rapide (~5–10 min) — 200 ex. par classe = 600 au total
python scripts/ai_benchmark.py --max-samples 200

# Complet — tout le test.parquet (plus long)
python scripts/ai_benchmark.py
```

### Métriques produites (dans le JSON)

| Métrique | Signification |
|----------|---------------|
| `accuracy` | Taux de prédictions correctes |
| `f1_macro` | Moyenne des F1 par classe (prioritaire) |
| `f1_weighted` | F1 pondéré par le nombre d'exemples |
| `avg_confidence` | Confiance moyenne des prédictions |
| `avg_latency_ms` | Latence moyenne par inférence (ms) |
| `per_class` | Pour chaque classe (neg/neu/pos) : `precision`, `recall`, `f1`, `support` |

### Fichier de sortie

Par défaut : `docs/e2/AI_BENCHMARK_RESULTS.json` (ou chemin spécifié par `--output-json`).

---

## 3. Script de fine-tuning — commandes et hyperparamètres

### Commande de base

```bash
python scripts/finetune_sentiment.py [OPTIONS]
```

### Hyperparamètres exposés en CLI (modifiables sans toucher au code)

| Option | Défaut | Rôle |
|--------|--------|------|
| `--model` | `sentiment_fr` | Backbone : `sentiment_fr`, `bert_multilingual`, `camembert`, `flaubert` |
| `--epochs` | 3 | Nombre d'epochs |
| `--batch-size` | 16 | Taille de batch (CPU : 8–16) |
| `--lr` | 2e-5 | Learning rate |
| `--max-length` | 256 | Longueur max en tokens (troncation) |
| `--max-train-samples` | 0 (= tout) | Limite d'exemples d'entraînement |
| `--max-val-samples` | 0 (= tout) | Limite d'exemples de validation |
| `--output-dir` | `models/{model}-sentiment-finetuned` | Dossier de sortie |
| `--topics` | *(vide)* | Filtrer par topics (ex: `finance,politique`). Améliore restitution veille. |
| `--eval-only` | — | Évalue un modèle déjà entraîné (pas d'entraînement) |

### Hyperparamètres codés en dur (dans `scripts/finetune_sentiment.py`)

| Paramètre | Valeur | Ligne ~ | Rôle |
|-----------|--------|---------|------|
| `weight_decay` | 0,01 | 285 | Régularisation L2 |
| `warmup_ratio` | 0,1 | 286 | 10 % des steps en warmup |
| `logging_steps` | 50 | 287 | Fréquence des logs |
| `eval_strategy` | `"epoch"` | 288 | Évaluation à chaque epoch |
| `save_strategy` | `"epoch"` | 289 | Sauvegarde à chaque epoch |
| `load_best_model_at_end` | True | 290 | Charge le meilleur checkpoint en fin de run |
| `metric_for_best_model` | `"f1_macro"` | 291 | Critère de sélection du meilleur modèle |
| `class_weight` | `"balanced"` | via `compute_class_weight` | Poids automatiques pour déséquilibre de classes |

Pour modifier `weight_decay` ou `warmup_ratio`, éditer `scripts/finetune_sentiment.py` dans le bloc `TrainingArguments` (vers la ligne 279).

### Exemples

```bash
# Fine-tuning recommandé (sentiment_fr + class weights)
python scripts/finetune_sentiment.py --model sentiment_fr --epochs 3

# Avec learning rate plus agressif (si loss stagne)
python scripts/finetune_sentiment.py --model sentiment_fr --epochs 3 --lr 3e-5

# Mode rapide pour démo (~30–40 min CPU)
python scripts/finetune_sentiment.py --model sentiment_fr --epochs 1 --max-train-samples 3000 --max-val-samples 800

# Batch plus petit si RAM limitée
python scripts/finetune_sentiment.py --model sentiment_fr --epochs 3 --batch-size 8

# Évaluer un modèle déjà entraîné
python scripts/finetune_sentiment.py --eval-only
```

---

## 4. Métriques de fine-tuning — ce qu'il faut suivre

### Pendant l'entraînement (Trainer Hugging Face)

| Métrique | Signification | Bon signe |
|----------|---------------|-----------|
| `loss` (train) | Cross-entropy sur l'entraînement | Décroît régulièrement |
| `eval_loss` | Cross-entropy sur la validation | Décroît, puis peut remonter (overfitting) |
| `eval_accuracy` | Taux de bonnes prédictions sur la validation | Monte |
| `eval_f1_macro` | F1 macro sur la validation | Monte (priorité) |
| `eval_f1_pos` | F1 sur la classe positif | > 0,4 (sinon classe ignorée) |
| `eval_f1_neg`, `eval_f1_neu` | F1 par classe | Homogènes entre classes |

### Cross-entropy (entropy)

La loss utilisée est la **Cross-Entropy** :

- Mesure l'écart entre les probabilités prédites et les labels réels.
- Plus la loss est basse, plus le modèle est confiant et correct.
- Forme typique : forte au début, puis décroissance.

### Où sont enregistrées ces métriques ?

- `models/{model}-sentiment-finetuned/trainer_state.json` : historique complet (loss, eval_*, etc.)
- `models/{model}-sentiment-finetuned/checkpoint-*/` : checkpoints par epoch

---

## 5. Piloter l'amélioration du fine-tuning

### 5.1 Class imbalance (priorité)

- **Problème** : classe minoritaire (ex. positif) ignorée → F1 pos = 0.
- **Solution** : `class_weight='balanced'` (déjà dans le script v2).
- **Vérifier** : `eval_f1_pos` > 0,4 après entraînement.

### 5.2 Learning rate (`--lr`)

- Trop élevé : loss instable, divergence.
- Trop bas : apprentissage lent, sous-optimisation.
- Valeurs typiques : 2e-5 à 5e-5 pour BERT-like.
- Si la loss stagne : essayer 3e-5 ou 5e-5.

### 5.3 Nombre d'epochs (`--epochs`)

- Trop peu : sous-apprentissage.
- Trop : overfitting (eval_loss remonte).
- Stratégie : `load_best_model_at_end=True` + `metric_for_best_model="f1_macro"` (déjà en place).
- En pratique : 2–4 epochs souvent suffisant.

### 5.4 Batch size (`--batch-size`)

- CPU : 8 ou 16.
- Plus grand : plus stable, mais plus lent et plus de RAM.
- Plus petit : plus de bruit, mais parfois meilleure généralisation.

### 5.5 Warmup (`warmup_ratio`)

- Déjà à 0,1 (10 % des steps en warmup).
- Utile pour éviter des spikes de loss au début.

### 5.6 Weight decay (`weight_decay`)

- Déjà à 0,01.
- Régularisation L2 pour limiter l'overfitting.

### 5.7 Métrique de sélection du meilleur modèle

- `metric_for_best_model="f1_macro"` : on garde le checkpoint avec le meilleur F1 macro.
- Évite de garder un modèle qui maximise l'accuracy en ignorant une classe.

### 5.8 Synthèse des hyperparamètres — tableau de référence

| Hyperparamètre | Où le modifier | Valeur actuelle | Effet si on augmente |
|----------------|----------------|----------------|----------------------|
| `--model` | CLI | `sentiment_fr` | Autre backbone (camembert, flaubert) |
| `--epochs` | CLI | 3 | Plus d'apprentissage, risque overfitting |
| `--batch-size` | CLI | 16 | Plus stable, plus lent, plus de RAM |
| `--lr` | CLI | 2e-5 | Convergence plus rapide, risque divergence |
| `--max-length` | CLI | 256 | Contexte plus long, plus lent |
| `weight_decay` | Code (l.285) | 0,01 | Plus de régularisation, moins d'overfitting |
| `warmup_ratio` | Code (l.286) | 0,1 | Warmup plus long, loss plus stable au démarrage |
| `class_weight` | Code (automatique) | balanced | Corrige le déséquilibre des classes |

---

## 6. Checklist "pilotage"

1. **Avant** : lancer un benchmark pour connaître le niveau de base.
2. **Backbone** : partir du meilleur pré-entraîné (`sentiment_fr`).
3. **Class weights** : toujours activés sur données déséquilibrées.
4. **Métrique** : optimiser le F1 macro, pas seulement l'accuracy.
5. **Surveiller** : `eval_f1_pos` pour la classe minoritaire.
6. **Après** : relancer le benchmark pour comparer avant/après.
7. **Courbes** : si `eval_loss` remonte alors que `train_loss` baisse → overfitting → moins d'epochs ou plus de régularisation.

---

## 7. Cartographie des fichiers

| Élément | Emplacement |
|---------|-------------|
| Copie IA | `scripts/create_ia_copy.py` (option `--topics finance,politique`) |
| Benchmark | `scripts/ai_benchmark.py` |
| Fine-tuning | `scripts/finetune_sentiment.py` |
| Résultats benchmark | `docs/e2/AI_BENCHMARK_RESULTS.json` |
| Résultats training | `docs/e2/TRAINING_RESULTS.json` (écrit par finetune) + `models/*/trainer_state.json` |
| Figures | `python scripts/plot_e2_results.py` → `docs/e2/figures/` |
| Modèle actif | `.env` → `SENTIMENT_FINETUNED_MODEL_PATH` |

---

## 8. Workflow complet recommandé

```bash
# 1. Copie IA (optionnel : --topics finance,politique pour veille ciblée)
python scripts/create_ia_copy.py
# python scripts/create_ia_copy.py --topics finance,politique

# 2. Benchmark initial (savoir où on en est)
python scripts/ai_benchmark.py --dataset data/goldai/ia/test.parquet --per-class 120

# 3. Fine-tuning (sentiment_fr + class weights)
python scripts/finetune_sentiment.py --model sentiment_fr --epochs 3

# 4. Activer le modèle dans .env
# SENTIMENT_FINETUNED_MODEL_PATH=models/sentiment_fr-sentiment-finetuned

# 5. Re-benchmark + figures
python scripts/ai_benchmark.py --dataset data/goldai/ia/test.parquet --per-class 120
python scripts/plot_e2_results.py
# Ou en une commande : scripts/run_benchmark_et_plots.bat
```

### Différence : run_benchmark_et_plots.bat vs run_training_loop_e2.bat

| Script | Entraînement | Benchmark | Figures |
|--------|--------------|-----------|---------|
| `run_benchmark_et_plots.bat` | **Non** | Oui | Oui |
| `run_training_loop_e2.bat` | **Oui** (quick par défaut, `--full` pour full) | Oui | Oui |

**Pourquoi le benchmark « relance » l'entraînement ?**  
Si vous lancez `run_training_loop_e2.bat`, ce script exécute la **boucle complète** : copie IA → fine-tuning → benchmark → figures. Il lance donc toujours un entraînement (quick par défaut). Pour **uniquement** benchmark + figures sans ré-entraîner : utilisez `run_benchmark_et_plots.bat`.

---

## 9. Modèles benchmark — identité technique

| Clé benchmark | Modèle HuggingFace | Description |
|---------------|-------------------|-------------|
| `sentiment_fr` | `ac0hik/Sentiment_Analysis_French` | Modèle FR dédié, presse/opinion — **meilleur du benchmark** |
| `finetuned_local` | Config `.env` ou `models/sentiment_fr-sentiment-finetuned` (priorité) ou `models/camembert-sentiment-finetuned` | Modèle fine-tuné sur données projet |
| `flaubert_multilingual` | `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` | XLM-RoBERTa multilingue Twitter — **N.B. : ce n'est pas FlauBERT** |
| `bert_multilingual` | `nlptown/bert-base-multilingual-uncased-sentiment` | BERT multilingue 5★ (1-2→neg, 3→neu, 4-5→pos) — pas CamemBERT |

### Glossaire : backbone (à ne pas confondre)

Le **backbone** (modèle de base) est le modèle pré-entraîné sur lequel on effectue le fine-tuning. C'est l'architecture + les poids initiaux qu'on adapte à nos données. Dans ce projet : `sentiment_fr`, `camembert`, `bert_multilingual`, `flaubert` sont des backbones.

**À ne pas confondre avec :**
- **Barebone** : système minimal (ex. PC sans composants) — terme informatique général
- **Blackbone** : pas un terme standard en ML
