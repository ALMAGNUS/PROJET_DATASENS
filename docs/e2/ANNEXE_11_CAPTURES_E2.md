# Annexe 11 - Captures E2 (checklist)

## Regle de nommage

Nom de fichier recommande:

`E2_ANNEXE11_<NUMERO>_<SUJET>.png`

Exemples:
- `E2_ANNEXE11_01_BENCHMARK_RESULTS.png`
- `E2_ANNEXE11_02_TRAINING_QUICK_OK.png`
- `E2_ANNEXE11_03_API_PREDICT_RESPONSE.png`
- `E2_ANNEXE11_04_REDOC_OPENAPI.png`
- `E2_ANNEXE11_05_PROMETHEUS_DRIFT_METRICS.png`
- `E2_ANNEXE11_06_GRAFANA_OVERVIEW.png`
- `E2_ANNEXE11_07_UPTIME_KUMA_STATUS.png`

## Captures obligatoires

### Capture 1 - Benchmark C7
- Titre dossier: "Benchmark IA C7 - Comparatif modeles"
- Montrer: tableau final (accuracy, f1 macro, latence) depuis `AI_BENCHMARK.md` ou JSON.

### Capture 2 - Training quick C7/C8
- Titre dossier: "Fine-tuning local - Execution quick mode CPU"
- Montrer: terminal avec fin d'entrainement, metrics `eval_accuracy`, `eval_f1`, runtime.

### Capture 3 - Predict API C8
- Titre dossier: "API IA integree - endpoint predict operationnel"
- Montrer: requete `POST /api/v1/ai/predict` + reponse JSON.

### Capture 4 - Documentation API C8
- Titre dossier: "Documentation technique - ReDoc/OpenAPI"
- Montrer: `http://localhost:8001/redoc` et endpoint IA visible.

### Capture 5 - Prometheus C8
- Titre dossier: "Monitorage API - Metriques Prometheus"
- Montrer: metriques `datasens_drift_*` et/ou requete API latence/erreurs.

### Capture 6 - Grafana (si actif)
- Titre dossier: "Dashboard MLOps - Vue globale"
- Montrer: panneau charge avec periode temporelle visible.

### Capture 7 - Uptime Kuma
- Titre dossier: "Disponibilite service - Uptime Kuma"
- Montrer: sonde API en statut `UP` + historique checks.

## Procedure rapide (10-15 min)

1. Lancer monitoring + API E2.
2. Executer `scripts\run_training_loop_e2.bat` (ou rejouer logs recents valides).
3. Executer/afficher benchmark.
4. Faire un appel predict et un appel drift.
5. Capturer ReDoc, OpenAPI, Prometheus, Grafana, Uptime Kuma.

## Note

Si certains panneaux drift Grafana sont vides en local (contexte Spark/Java), conserver la preuve endpoint drift + /metrics + observabilite API, qui reste recevable pour E2.

