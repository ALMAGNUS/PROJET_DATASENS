# Separation entrainement vs inference - Etape 3

Cette etape finalise la branche inference dediee sans casser l'existant.

## Objectif

Sortir un objet explicite de prediction applicative:

- `GOLD_APP_PREDICTIONS` en Parquet partitionne
- conservation optionnelle de `model_output` (SQLite) pour compatibilite

## Ce qui a ete ajoute

- `src/ml/inference/sentiment.py`
  - `build_prediction_frame(...)`
  - `write_predictions_parquet(...)`
- `scripts/run_inference_pipeline.py`
  - pipeline inference autonome: `GOLD_APP_INPUT -> GOLD_APP_PREDICTIONS`
- API `GET /ai/ml/sentiment-goldai`
  - quand `persist=true`, ecrit:
    - SQLite `model_output` (historique)
    - Parquet `predictions_parquet` (nouveau contrat)

## Emplacement de sortie

`data/goldai/predictions/date=YYYY-MM-DD/run=<inference_run_id>/predictions.parquet`

## Workflow recommande

```bash
python scripts/merge_parquet_goldai.py
python scripts/build_gold_branches.py
python scripts/run_inference_pipeline.py --limit 500 --persist-model-output
```

## Compatibilite

- Aucun endpoint supprime.
- `model_output` reste disponible.
- La nouvelle sortie Parquet s'ajoute pour tracer les runs inference.

