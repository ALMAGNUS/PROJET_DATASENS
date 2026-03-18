# Annexe 10 - Preuves execution E2

## Objectif

Prouver l'execution reelle des composants critiques du bloc E2: benchmark, entrainement rapide CPU, API IA et monitorage.

## Commandes d'execution (local)

### 1) Boucle entrainement + benchmark (mode quick)

```bash
scripts\run_training_loop_e2.bat
```

Attendu:
- creation/maj environnement `.venv_benchmark`,
- regeneration des splits `data/goldai/ia/*.parquet`,
- fine-tuning rapide (`epoch=1` en mode quick),
- benchmark multi-modeles execute et rapports generes.

### 2) Benchmark seul (rejouable)

```bash
scripts\run_benchmark_e2.bat
```

Attendu:
- comparaison des modeles sur `data/goldai/ia/test.parquet`,
- generation du resultat detaille dans `docs/e2/AI_BENCHMARK_RESULTS.json`.

### 3) API E2 + endpoints IA

```bash
python run_e2_api.py
```

Verifier:
- `http://localhost:8001/health`
- `http://localhost:8001/redoc`
- `http://localhost:8001/openapi.json`
- `POST /api/v1/ai/predict`

### 4) Drift + metriques

Appeler:
- `GET /api/v1/analytics/drift-metrics?target_date=YYYY-MM-DD`
- `GET /metrics`

Attendu:
- reponse JSON drift avec `drift_score` et `articles_total`,
- presence des gauges `datasens_drift_*` dans Prometheus metrics.

## Resultats techniques a citer dans le dossier

- Entrainer et benchmarker sur poste CPU ecole est faisable en mode quick.
- Le benchmark distingue clairement les modeles (qualite/latence/confiance).
- Le service reste pilotable en production via metriques exposees.
- La documentation d'API est auditable (ReDoc/OpenAPI).

## Interpretation de soutenance

Ces executions montrent que E2 n'est pas un dossier theorique: la chaine complete de parametrage, integration, evaluation et supervision IA est operationnelle et reproductible.

