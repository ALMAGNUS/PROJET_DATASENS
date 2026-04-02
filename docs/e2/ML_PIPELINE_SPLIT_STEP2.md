# Separation entrainement vs inference - Etape 2

Cette etape se cale sur l'existant: on ajoute des sorties separees sans casser les scripts historiques.

## Objectif

Creer deux jeux distincts apres GoldAI:

- `data/goldai/app/gold_app_input.parquet` (inference, sans labels)
- `data/goldai/ia/gold_ia_labelled.parquet` (entrainement, avec `sentiment_label`)

## Changements implementes

- Nouveau module:
  - `src/datasets/gold_branches.py`
  - `build_gold_app_input(df)`
  - `build_gold_ia_labelled(df)`
- Nouveau script:
  - `scripts/build_gold_branches.py`
- Compatibilite create_ia_copy:
  - `scripts/create_ia_copy.py` lit en priorite `gold_ia_labelled.parquet`, sinon fallback `merged_all_dates.parquet`.
- Compatibilite inference:
  - `src/ml/inference/goldai_loader.py` lit en priorite `app/gold_app_input.parquet`, sinon fallback `merged_all_dates.parquet`.

## Pourquoi c'est safe pour l'existant

- Les chemins historiques restent valides.
- Si les nouveaux fichiers n'existent pas, le comportement precedent est conserve.
- Les scripts de fine-tuning continuent d'utiliser `data/goldai/ia/train.parquet` / `val.parquet` / `test.parquet`.

## Workflow recommande

```bash
python scripts/merge_parquet_goldai.py
python scripts/build_gold_branches.py
python scripts/create_ia_copy.py
```

