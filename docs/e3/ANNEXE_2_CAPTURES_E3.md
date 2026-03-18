# Annexe 2 - Captures E3 (checklist)

## But

Fournir des preuves visuelles claires et nommees pour valider C9 a C13 sans ambiguite.

## Regle de nommage (obligatoire)

Nommer les fichiers de capture avec ce format:

`E3_ANNEXE2_<NUMERO>_<SUJET>.png`

Exemples:
- `E3_ANNEXE2_01_CI_QUALITY_GATE_OK.png`
- `E3_ANNEXE2_02_API_PREDICT_RESPONSE.png`
- `E3_ANNEXE2_03_DRIFT_METRICS_RESPONSE.png`
- `E3_ANNEXE2_04_PROMETHEUS_DRIFT_GAUGES.png`
- `E3_ANNEXE2_05_OPENAPI_REDOC.png`

## Checklist captures a produire

### Capture 1 - CI Quality Gate (C13)
- **Titre a afficher dans le dossier**: "CI - Workflow E3 Quality Gate valide"
- **Ecran cible**: GitHub Actions, workflow `E3 Quality Gate`
- **Contenu minimum visible**:
  - statut vert (success),
  - job `E3 targeted tests`,
  - etape `Run E3 quality gate`.

### Capture 2 - API Predict (C9/C10)
- **Titre a afficher dans le dossier**: "API REST IA - Contrat predict fonctionnel"
- **Ecran cible**: ReDoc/Swagger ou client API
- **Requete**: `POST /api/v1/ai/predict`
- **Contenu minimum visible**:
  - payload (`text`, `model`, `task`),
  - reponse JSON (`model`, `task`, `result`).

### Capture 3 - Drift Metrics (C11)
- **Titre a afficher dans le dossier**: "Monitoring IA - Endpoint drift-metrics operationnel"
- **Ecran cible**: endpoint `GET /api/v1/analytics/drift-metrics`
- **Contenu minimum visible**:
  - HTTP 200,
  - `drift_score`,
  - `articles_total`.

### Capture 4 - Prometheus Gauges (C11)
- **Titre a afficher dans le dossier**: "Prometheus - Gauges de drift exposees"
- **Ecran cible**: `http://localhost:9090/graph` ou `/metrics` API E2
- **Contenu minimum visible**:
  - `datasens_drift_score`,
  - `datasens_drift_articles_total`,
  - au moins une valeur numerique.

### Capture 5 - Documentation API (C10)
- **Titre a afficher dans le dossier**: "Documentation technique API - OpenAPI/ReDoc"
- **Ecran cible**: `http://localhost:8001/redoc` (ou `/docs`)
- **Contenu minimum visible**:
  - titre API,
  - section endpoint IA ou analytics,
  - schema de requete/reponse.

## Procedure rapide de collecte (10-15 min)

1. Lancer API E2 et stack monitoring.
2. Executer:
   - `python scripts/run_e3_quality_gate.py`
3. Ouvrir les URLs:
   - API docs: `http://localhost:8001/redoc`
   - Drift: `http://localhost:8001/api/v1/analytics/drift-metrics?target_date=YYYY-MM-DD`
   - Metrics: `http://localhost:8001/metrics`
   - Prometheus: `http://localhost:9090/graph`
4. Prendre les 5 captures en respectant le nommage.
5. Referencer chaque capture dans le dossier E3 avec son titre exact.

## Texte de reference pour le dossier (copier/coller)

"Les captures E3 montrent la validation complete de la chaine d'integration IA: exposition API REST, consommation documentee, monitorage des metriques de drift, et controle qualite automatise via un workflow CI dedie. Ces preuves confirment la conformite operationnelle des competences C9 a C13."

