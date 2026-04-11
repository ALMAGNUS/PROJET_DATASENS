# Benchmark IA - DataSens E2
Date: 2026-04-04 16:32

## Méthode
Dataset de référence: `C:/Users/Utilisateur/Desktop/PROJET_DATASENS/data/goldai/ia/test.parquet`
Métriques: Accuracy, F1 macro, F1 pondéré, confiance moyenne, latence moyenne (ms).
Répartition des classes évaluées: neg=120, neu=120, pos=120.

## Résultats comparatifs

| Modèle | Accuracy | F1 macro | F1 pondéré | Confiance moy. | Latence moy. (ms) |
|---|---:|---:|---:|---:|---:|
| `finetuned_local` | 0.6917 | 0.6930 | 0.6930 | 0.6628 | 282.51 |
| `sentiment_fr` | 0.6139 | 0.6093 | 0.6093 | 0.7946 | 283.65 |
| `xlm_roberta_twitter` | 0.4583 | 0.4314 | 0.4314 | 0.8253 | 252.13 |
| `bert_multilingual` | 0.3750 | 0.3034 | 0.3034 | 0.6121 | 279.10 |

## Recommandation
Le modèle recommandé est `finetuned_local` car il obtient le meilleur compromis entre F1 macro et accuracy sur le dataset de référence.
Les résultats détaillés (par classe) sont conservés dans `docs/e2/AI_BENCHMARK_RESULTS.json`.