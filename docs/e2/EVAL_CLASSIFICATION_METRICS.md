# Évaluation classification — DataSens E2
Date : 2026-06-09 11:16

Dataset de test : `data/goldai/ia/test.parquet`

Problème **multiclasse** (négatif / neutre / positif). Specificity, FPR, ROC-AUC et courbes ROC calculés en **one-vs-rest** puis moyennés (macro). ROC-AUC utilise les probabilités prédites (softmax).

## finetuned_local

- Accuracy : **0.6483** (64.8%)
- Precision macro : 0.6253 · Recall macro : 0.6168 · F1 macro : 0.6101
- Specificity macro : 0.8236 · FPR macro : 0.1764 · ROC-AUC macro : **0.8023**

| Classe | Precision | Recall | F1 | Specificity | FPR | ROC-AUC | Support |
|---|---:|---:|---:|---:|---:|---:|---:|
| négatif | 0.7770 | 0.5400 | 0.6372 | 0.8997 | 0.1003 | 0.8654 | 200 |
| neutre | 0.6850 | 0.8700 | 0.7665 | 0.7411 | 0.2589 | 0.8611 | 200 |
| positif | 0.4138 | 0.4404 | 0.4267 | 0.8300 | 0.1700 | 0.6803 | 109 |

Figures : `e2_eval_confusion_finetuned_local.png`, `e2_eval_roc_finetuned_local.png`, `e2_eval_metrics_table_finetuned_local.png`

## sentiment_fr

- Accuracy : **0.6149** (61.5%)
- Precision macro : 0.5788 · Recall macro : 0.5718 · F1 macro : 0.5692
- Specificity macro : 0.8013 · FPR macro : 0.1987 · ROC-AUC macro : **0.7460**

| Classe | Precision | Recall | F1 | Specificity | FPR | ROC-AUC | Support |
|---|---:|---:|---:|---:|---:|---:|---:|
| négatif | 0.6923 | 0.5850 | 0.6341 | 0.8317 | 0.1683 | 0.7608 | 200 |
| neutre | 0.6349 | 0.8000 | 0.7080 | 0.7023 | 0.2977 | 0.8149 | 200 |
| positif | 0.4091 | 0.3303 | 0.3655 | 0.8700 | 0.1300 | 0.6622 | 109 |

Figures : `e2_eval_confusion_sentiment_fr.png`, `e2_eval_roc_sentiment_fr.png`, `e2_eval_metrics_table_sentiment_fr.png`
