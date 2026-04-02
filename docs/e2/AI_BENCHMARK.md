# Benchmark IA - DataSens E2
Date: 2026-04-01 14:01

## Méthode
Dataset de référence: `C:/Users/Utilisateur/Desktop/PROJET_DATASENS/data/goldai/ia/test.parquet`
Métriques: Accuracy, F1 macro, F1 pondéré, confiance moyenne, latence moyenne (ms).
Répartition des classes évaluées: neg=40, neu=40, pos=40.

## Résultats comparatifs

| Modèle | Accuracy | F1 macro | F1 pondéré | Confiance moy. | Latence moy. (ms) |
|---|---:|---:|---:|---:|---:|
| `finetuned_local` | 0.6667 | 0.6676 | 0.6676 | 0.6572 | 196.86 |
| `sentiment_fr` | 0.6000 | 0.5913 | 0.5913 | 0.7983 | 198.08 |
| `xlm_roberta_twitter` | 0.4583 | 0.4324 | 0.4324 | 0.8295 | 206.73 |
| `bert_multilingual` | 0.3750 | 0.3095 | 0.3095 | 0.5856 | 242.30 |

## Recommandation
Le modèle recommandé est `finetuned_local` car il obtient le meilleur compromis entre F1 macro et accuracy sur le dataset de référence.
Les résultats détaillés (par classe) sont conservés dans `docs/e2/AI_BENCHMARK_RESULTS.json`.