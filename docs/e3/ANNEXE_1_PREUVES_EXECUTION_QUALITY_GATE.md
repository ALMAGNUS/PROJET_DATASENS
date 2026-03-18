# Annexe 1 - Preuves execution quality gate E3

## Objectif

Prouver que le module E3 est testable, robuste en environnement ecole et integrable en CI/CD, avec une verification automatique des points critiques C9 a C13.

## Commande d'execution locale

```bash
python scripts/run_e3_quality_gate.py
```

## Resultat attendu

- `4 passed` sur le fichier `tests/test_e3_quality_gate.py`.
- Aucune erreur bloquante.
- Warnings eventuels non bloquants (environnement Python local).

## Cas verifies par les tests

1. **RAW vide sans crash API**
   - Scenario: `raw_articles.csv` vide.
   - Attendu: pas de 500, DataFrame vide avec schema compatible.

2. **Fallback drift sans Spark/Java**
   - Scenario: panne simulee `JAVA_GATEWAY_EXITED`.
   - Attendu: `/api/v1/analytics/drift-metrics` retourne 200 avec calcul pandas.

3. **Contrat API predict stable**
   - Scenario: appel `/api/v1/ai/predict` avec service ML mocke.
   - Attendu: reponse JSON conforme au contrat (model, task, result[]).

4. **Metriques Prometheus exposees**
   - Scenario: appel drift puis lecture `/metrics`.
   - Attendu: presence des gauges `datasens_drift_score` et `datasens_drift_articles_total`.

## Preuves CI/CD

- Workflow: `.github/workflows/e3-quality-gate.yml`
- Declenchement: `push` et `pull_request` sur `main`/`develop`.
- Etapes:
  - installation dependances,
  - configuration `PYTHONPATH`,
  - execution `python scripts/run_e3_quality_gate.py`.

## Interpretation de soutenance

Cette annexe demontre que l'integration IA E3 n'est pas seulement documentee: elle est verifiee automatiquement, reproductible localement, et controlee en pipeline CI.  
Le service reste operable meme en environnement contraint (absence Spark/Java), ce qui reduit le risque de regression lors des demonstrations et des livraisons.

