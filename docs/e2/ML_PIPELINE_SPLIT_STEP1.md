# Separation entrainement vs inference - Etape 1

Cette etape pose les garde-fous anti-fuite de cible sans casser le pipeline existant.

## Objectif

Eviter qu'une colonne de verite terrain (ex: `sentiment_label`) soit utilisee dans la branche inference.

## Ce qui a ete ajoute

- Contrats de donnees:
  - `src/data_contracts/schemas.py`
  - `CommonFeatures`
  - `TrainingRecord`
  - `InferenceInput`
  - `PredictionOutput`
- Garde-fous:
  - `src/data_contracts/guards.py`
  - `assert_no_target_leakage(columns)`
  - `assert_training_label_present(columns, label_col="sentiment_label")`
- Integration immediate:
  - `src/ml/inference/sentiment.py`
  - verification systematique des colonnes chargees avant inference.
- Tests:
  - `tests/test_data_contracts_guards.py`

## Comportement attendu

- Si une colonne label (`sentiment_label`, `label`, `target`, `y_true`) se trouve dans l'entree inference, on stoppe avec erreur explicite.
- La branche entrainement doit contenir `sentiment_label`.

## Impact sur E1

- Aucun changement de schema de sortie existant a ce stade.
- Aucun changement de commande run E1.
- Cette etape prepare l'Etape 2 (creation des jeux separes `gold_app_input` et `gold_ia_labelled`).

## Maintenance

Si vous changez les noms de colonnes cibles:

1. Mettre a jour `TARGET_LABEL_COLUMNS` dans `src/data_contracts/guards.py`.
2. Adapter les tests `tests/test_data_contracts_guards.py`.
3. Relancer les tests cibles.

Commande:

```bash
python -m pytest tests/test_data_contracts_guards.py
```

