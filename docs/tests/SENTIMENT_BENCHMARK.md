# Jeu de test — classification de sentiment

Un jeu de textes de test a été constitué afin d'évaluer la capacité du modèle à distinguer les sentiments positifs, neutres et négatifs. Ce jeu inclut des cas simples, des formulations ambiguës et des phrases ironiques afin d'observer les limites du modèle au-delà d'une classification évidente.

## Fichiers

| Fichier | Rôle |
|---------|------|
| `data/tests/sentiment_benchmark_corpus.csv` | Corpus de référence (`id`, `text`, `label_expected`) — 60 phrases |
| `scripts/run_sentiment_benchmark_corpus.py` | Exécute ac0hik + calibration (`finalize_sentiment`) sur tout le corpus |
| `reports/sentiment_benchmark_corpus_results.csv` | Résultats détaillés avec prédictions |
| `reports/sentiment_benchmark_corpus_results.json` | Synthèse (accuracy globale et par catégorie) |

## Catégories

| Préfixe | Description | Exemples |
|---------|-------------|----------|
| P01–P10 | Positifs évidents | satisfaction, qualité, performance |
| N01–N10 | Négatifs évidents | lenteur, déception, incohérence |
| NE01–NE10 | Neutres factuels | descriptions techniques sans opinion |
| A01–A10 | Ambigus / mitigés | contrastes « mais », « même si » |
| I01–I10 | Ironie / formulations piégeuses | « Super, encore une erreur… » |
| D01–D10 | Contexte DataSens / projet IA | pipeline, CamemBERT, monitoring |

Le sous-ensemble **30 phrases** (P + NE + N) correspond au mini jeu équilibré pour un test rapide.

## Lancer l'évaluation

```powershell
cd <racine-du-projet>
.\.venv\Scripts\Activate.ps1
python scripts/run_sentiment_benchmark_corpus.py
```

## Format de sortie

```
id,text,label_expected,label_predicted,confidence_score,sentiment_score,is_correct,refined
```

- `refined` : règle de post-traitement appliquée (`mixed_contrast`, `irony_prefix`, `understatement_positive`, `factual_neutral`) ou vide si prédiction brute du modèle.

## Calibration

Le modèle de base `ac0hik/Sentiment_Analysis_French` est complété par `finalize_sentiment()` dans `src/ml/inference/sentiment_postprocess.py` pour :

- phrases contrastées mitigées → neutre ;
- ironie explicite (préfixe positif + contenu négatif) → négatif ;
- litote positive (« pas mal, je m'attendais à pire ») → positif ;
- énoncés factuels sans marqueur affectif → neutre.

Les cas les plus difficiles (ironie implicite, sarcasme contextuel) restent une limite connue du modèle sans fine-tuning dédié.
