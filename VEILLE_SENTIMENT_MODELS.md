# Veille technologique – Modèles d’analyse de sentiment (FR)

Benchmark des modèles utilisables pour la prédiction de sentiment dans DataSens (Cockpit IA).

## Spec technique (prêt à l’emploi + CPU)

- **Modèle** : fine-tuné FR (CamemBERT/FlauBERT bruts ne font pas sentiment)
- **Params CPU** : `max_length=256`, `batch_size=8` (i7) ou 4 (i5), `device=-1`
- **Threads** : `torch.set_num_threads(6-8)` (i7 vPro), 4-6 (i5), `TOKENIZERS_PARALLELISM=false`
- **3 classes** : POSITIVE / NEUTRAL / NEGATIVE + confidence (max prob)
- **Score continu** : `sentiment_score = p_pos - p_neg` ∈ [-1, +1] (finance-friendly)
- **MODEL_OUTPUT** : `label`, `score`, `model_id`, `inference_ms`, `created_at`, `raw_data_id`

---

## Modèles configurés

| Modèle | HF ID | Accuracy | Tâche | Usage |
|--------|-------|----------|-------|-------|
| **sentiment_fr** | `ac0hik/Sentiment_Analysis_French` | **76,54 %** | pos/nég/neutre | **Recommandé** – meilleur score FR |
| **camembert** | `cmarkea/distilcamembert-base-sentiment` | 61 % exact, 88,8 % top-2 | 5★ → pos/neu/neg | Léger, optimisé CPU |
| **flaubert** | `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` | ~70 % (multilingue) | pos/nég/neutre | XLM-RoBERTa, tweets |

---

## Détails par modèle

### 1. sentiment_fr (ac0hik)
- **Base** : CamemBERT
- **Données** : Tweet_sentiment_multilingual (partie française)
- **Classes** : positif, négatif, neutre
- **Accuracy** : 76,54 %
- **Usage** : cas général, tweets et textes courts

### 2. camembert (DistilCamemBERT)
- **Base** : DistilCamemBERT (Credit Mutuel Arkea)
- **Données** : 205k avis Amazon + 236k critiques AlloCiné
- **Classes** : 1–5 étoiles → mappé en pos/neutre/nég
- **Accuracy** : 61 % exacte, 88,8 % top-2
- **Usage** : avis clients, critiques, texte assez long

### 3. flaubert (XLM-RoBERTa)
- **Base** : XLM-RoBERTa
- **Données** : tweets multilingues
- **Classes** : positif, négatif, neutre
- **Usage** : tweets, texte informel

---

## Modèles à suivre (veille)

| Modèle | Lien | Commentaire |
|--------|------|-------------|
| `astrosbd/french_emotion_camembert` | [HF](https://huggingface.co/astrosbd/french_emotion_camembert) | Émotions (joie, tristesse, colère) – 82,95 % |
| `nlptown/flaubert_small_cased_sentiment` | [HF](https://huggingface.co/nlptown/flaubert_small_cased_sentiment) | FlauBERT 5★ avis FR – 61,56 % |
| `bhadresh-savani/bert-base-go-emotion-multilingual` | [HF](https://huggingface.co/bhadresh-savani/bert-base-go-emotion-multilingual) | 27 émotions multilingues |
| Modèles BGE / embeddings 2025 | MTEB | Pour RAG / classification par similarité |

---

## Configuration (.env)

```env
# Modèles sentiment (optionnel – valeurs par défaut dans config.py)
SENTIMENT_FR_MODEL_PATH=ac0hik/Sentiment_Analysis_French
CAMEMBERT_MODEL_PATH=cmarkea/distilcamembert-base-sentiment
FLAUBERT_MODEL_PATH=cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual

# Modèle fine-tuné (prioritaire si défini)
# SENTIMENT_FINETUNED_MODEL_PATH=models/camembert-sentiment-finetuned
```

---

## Test dans le Cockpit

1. Onglet **IA** → **1. Prédiction de sentiment**
2. Choisir un modèle (sentiment_fr recommandé)
3. Tester plusieurs formulations pour comparer
4. Premier appel : téléchargement du modèle (quelques minutes)
