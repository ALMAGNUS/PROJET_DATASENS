# Annexe 9 - Preuves visuelles MLOps et API (E1/E2/E5)

Objectif: fournir des captures d'ecran auditable montrant que l'observabilite et l'API sont bien operationnelles.

## 1) Captures obligatoires

- `capture_01_prometheus_targets_up.png`
- `capture_02_prometheus_metrics_query.png`
- `capture_03_grafana_dashboard_global.png`
- `capture_04_grafana_panel_latency_errors.png`
- `capture_05_uptime_kuma_status.png`
- `capture_06_uptime_kuma_incident_history.png`
- `capture_07_redoc_openapi_ui.png`
- `capture_08_openapi_json_raw.png`

## 2) URL / points de verification

- Prometheus UI: `http://localhost:9090`
- Grafana UI: `http://localhost:3000`
- Uptime Kuma UI: `http://localhost:3001`
- ReDoc API: `http://localhost:8001/redoc`
- OpenAPI JSON: `http://localhost:8001/openapi.json`
- Swagger docs (optionnel): `http://localhost:8001/docs`

## 3) Contenu minimum attendu sur chaque capture

### Prometheus

- Cible API en statut `UP` (menu `Status -> Targets`).
- Une requete metrique avec resultat visible (ex. requete de debit ou latence HTTP).
- Horodatage visible dans l'interface.

### Grafana

- Dashboard complet charge (titre lisible).
- Au moins un panel latence/erreurs avec donnees recentes.
- Time range visible (ex. `Last 15 minutes`).

### Uptime Kuma

- Sonde API en statut `UP`.
- Historique des checks / incidents visible.
- Heure et duree de disponibilite visibles.

### ReDoc et OpenAPI

- ReDoc affiche les endpoints IA (`/api/v1/ai/...`).
- OpenAPI JSON brut accessible (reponse JSON visible).
- Endpoint de prediction present dans la specification.

## 4) Procedure rapide de collecte des preuves

1. Lancer les services de monitoring (Prometheus, Grafana, Uptime Kuma).
2. Lancer l'API (`python run_e2_api.py`).
3. Generer un peu d'activite API (quelques appels sur `/api/v1/ai/predict`).
4. Capturer Prometheus, Grafana, Uptime Kuma, ReDoc, OpenAPI JSON.
5. Stocker les captures dans un dossier versionne, par exemple `docs/e2/captures/`.
6. Verifier que chaque capture montre date/heure + statut + metrique.

## 5) Critere de validation

Cette annexe est consideree complete si:

- toutes les captures obligatoires existent;
- chaque outil montre des donnees reelles (pas un ecran vide);
- la date d'execution est coherente avec les runs techniques du dossier;
- les endpoints API documentes dans ReDoc/OpenAPI correspondent aux endpoints effectivement testes.

## 6) Note de contexte (session locale)

Dans la session de demonstration locale, les panneaux Grafana lies au drift avance peuvent rester vides ou a zero si le calcul Spark n'est pas actif (`JAVA_GATEWAY_EXITED`). Cela n'invalide pas la preuve d'observabilite API: les panneaux trafic, erreurs, latence, authentification et acces par zone restent pleinement valides pour la verification.
