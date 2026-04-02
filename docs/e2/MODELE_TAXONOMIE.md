# Taxonomie des modèles — clés internes vs vrais noms

Les fichiers JSON et le benchmark utilisent des **clés courtes** (historique du code). Ce document aligne chaque clé sur le **modèle Hugging Face ou le dossier local** réellement chargé.

## Tableau de correspondance (benchmark `AI_BENCHMARK_RESULTS.json`)

| Clé JSON | Nom lisible (démo) | Identifiant technique chargé | Rôle |
|----------|-------------------|--------------------------------|------|
| `bert_multilingual` | BERT multilingue 5★ | `nlptown/bert-base-multilingual-uncased-sentiment` | Baseline multilingue |
| `xlm_roberta_twitter` | XLM-RoBERTa Twitter | `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` | Baseline Twitter multilingue |
| `sentiment_fr` | **Backbone FR** (non fine-tuné projet) | `ac0hik/Sentiment_Analysis_French` | Point de départ avant fine-tuning DataSens |
| `finetuned_local` | **Modèle projet fine-tuné** (même famille que HF) | Chemin local : `models/sentiment_fr-sentiment-finetuned` **ou** valeur de `SENTIMENT_FINETUNED_MODEL_PATH` dans `.env` (ex. `ALMAGNUS/datasens-sentiment-fr` téléchargé en cache) | C’est **le même type de poids** que `ALMAGNUS/datasens-sentiment-fr` quand tu as publié depuis ce dossier |

> **Important :** `finetuned_local` n’est **pas** un nom de modèle sur Hugging Face. C’est une **clé interne** qui pointe vers le checkpoint utilisé pour le benchmark (local ou Hub selon `.env`).

## Hugging Face `ALMAGNUS/datasens-sentiment-fr`

- C’est le **dépôt public** où tu pousses les poids après `publish_best_model_to_hf.py` (ou équivalent).
- Le **79 %** (ou autre) affiché sur la fiche modèle = métriques **validation** au moment du training / de la carte modèle (jeu `val`, pas le petit échantillon du benchmark).

## Pourquoi 79 % (HF) et ~67 % (`finetuned_local` dans le JSON) coexistent

| Mesure | Jeu d’évaluation | Objectif |
|--------|------------------|----------|
| Carte Hugging Face | `val.parquet` (complet, milliers d’exemples) | Qualité **absolue** du modèle fine-tuné |
| `ai_benchmark.py` | `test.parquet` puis **sous-échantillon équilibré** (`--per-class`, défaut 40 par classe → 120 textes) | Comparer **tous les modèles sur le même petit jeu** |

Les deux chiffres peuvent être **vrais en même temps** : périmètres différents.

## Fichiers d’entraînement (`TRAINING_RESULTS.json`, etc.)

| Champ / fichier | Signification |
|-----------------|---------------|
| `"model": "sentiment_fr"` | **Base Hugging Face** utilisée pour lancer le fine-tuning (`ac0hik/Sentiment_Analysis_French`), pas le nom du modèle final publié. |
| `eval_accuracy` / `eval_f1_*` | Métriques sur le **jeu de validation** du run d’entraînement (taille et split du script `finetune_sentiment.py`). |
| Dossier `models/sentiment_fr-sentiment-finetuned/` | Sortie **locale** du fine-tuning (CamemBERT-family fine-tuné sur ton dataset). |
| Dossier `models/camembert-sentiment-finetuned/` | Autre run / ancien nom de sortie ; **ne pas confondre** avec le dépôt HF actuel sans vérifier `config.json` et date. |

## Résumé une phrase

- **`sentiment_fr` (benchmark)** = modèle **ac0hik** tel quel.  
- **`finetuned_local` (benchmark)** = **ton** fine-tuning (dossier local ou id HF lu via `.env`).  
- **`ALMAGNUS/datasens-sentiment-fr`** = **même intention produit** que le fine-tuné local une fois publié ; le 79 % vient d’une **autre évaluation** que le benchmark 120 échantillons.

Pour régénérer les figures après un nouveau benchmark :

```bash
python scripts/ai_benchmark.py
python scripts/plot_e2_results.py
```

Pour les figures **inférence** sur les prédictions réelles :

```bash
python scripts/plot_inference_results.py
```
