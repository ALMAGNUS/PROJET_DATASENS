# Benchmark IA - DataSens E2
Date: 2026-03-18 00:53

## Méthode
Dataset de référence: `C:/Users/Utilisateur/Desktop/PROJET_DATASENS/data/goldai/ia/test.parquet`
Métriques: Accuracy, F1 macro, F1 pondéré, confiance moyenne, latence moyenne (ms).
Répartition des classes évaluées: neg=80, neu=80, pos=80.

## Résultats comparatifs

| Modèle | Accuracy | F1 macro | F1 pondéré | Confiance moy. | Latence moy. (ms) |
|---|---:|---:|---:|---:|---:|
| `finetuned_local` | 0.8417 | 0.8411 | 0.8411 | 0.9015 | 203.58 |
| `sentiment_fr` | 0.5750 | 0.5703 | 0.5703 | 0.7920 | 213.52 |
| `flaubert_multilingual` | 0.4250 | 0.3956 | 0.3956 | 0.8247 | 205.42 |
| `bert_multilingual` | 0.4083 | 0.3346 | 0.3346 | 0.6007 | 212.21 |

## Recommandation
Le modèle recommandé est `finetuned_local` car il obtient le meilleur compromis entre F1 macro et accuracy sur le dataset de référence.
Les résultats détaillés (par classe) sont conservés dans `docs/e2/AI_BENCHMARK_RESULTS.json`.