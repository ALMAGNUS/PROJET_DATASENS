# Annexe 2 — Captures E5 (checklist)

## But

Fournir des preuves visuelles pour valider C20 et C21.

---

## Règle de nommage

`E5_ANNEXE2_<NUMERO>_<SUJET>.png`

---

## Checklist captures

### Capture 1 — Prometheus Targets (C20)

- **Titre** : "Prometheus — Cibles de collecte"
- **Écran** : http://localhost:9090 → Status → Targets
- **Contenu** : Cible API E2 (localhost:8001) en UP

### Capture 2 — Prometheus métriques (C20)

- **Titre** : "Prometheus — Requête métriques DataSens"
- **Écran** : http://localhost:9090 → Graph
- **Requête** : `datasens_e2_api_requests_total` ou `datasens_drift_score`
- **Contenu** : Courbe ou valeur affichée

### Capture 3 — Grafana Dashboard (C20)

- **Titre** : "Grafana — Dashboard DataSens"
- **Écran** : http://localhost:3000 → Dashboards → DataSens
- **Contenu** : Toutes les routes API, métriques drift, latence, surveillance des logs

### Capture 4 — Uptime Kuma (C20)

- **Titre** : "Uptime Kuma — Surveillance disponibilité"
- **Écran** : http://localhost:3001 (Docker Compose) ou http://localhost:3002 (standalone)
- **Contenu** : Monitors API, Prometheus, Grafana (statut UP)

### Capture 5 — Endpoint /metrics (C20)

- **Titre** : "API E2 — Métriques Prometheus"
- **Écran** : http://localhost:8001/metrics (ou capture curl)
- **Contenu** : Extrait montrant datasens_*

### Capture 6 — Logs (C20)

- **Titre** : "Journalisation — logs/datasens.log"
- **Écran** : Contenu de `logs/datasens.log` ou configuration `src/logging_config.py`
- **Contenu** : Format, rotation, niveau

### Capture 7 — Procédure incidents (C21)

- **Titre** : "Procédure résolution incidents — PROCEDURE_INCIDENTS.md"
- **Écran** : Ouverture de `docs/PROCEDURE_INCIDENTS.md`
- **Contenu** : Modèle 8 étapes, exemple Incident 1.4.1

---

## Procédure rapide

1. Lancer API : `python run_e2_api.py`
2. Lancer Prometheus : `start_prometheus.bat`
3. Lancer Grafana : `start_grafana.bat`
4. Lancer Uptime Kuma : `docker-compose up -d uptime-kuma`
5. Appeler `/api/v1/analytics/drift-metrics` pour alimenter les gauges
6. Prendre les 7 captures avec le nommage indiqué
