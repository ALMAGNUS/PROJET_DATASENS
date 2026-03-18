# Annexe 1 — Preuves d'exécution E4

## Objectif

Prouver que l'application DataSens (cockpit Streamlit, API, pipeline) est exécutable, testable et livrable.

---

## Commandes de lancement

### API E2

```bash
python run_e2_api.py
```

- URL : http://localhost:8001
- Docs : http://localhost:8001/docs
- Health : http://localhost:8001/health

### Cockpit Streamlit

```bash
streamlit run src/streamlit/app.py
```

- URL : http://localhost:8501
- Prérequis : API E2 démarrée (pour auth et appels)

### Stack complète (Docker)

```bash
docker-compose up -d
```

- API : 8001
- Prometheus : 9090
- Grafana : 3000
- Uptime Kuma : 3001

---

## Vérifications

| Vérification | Commande / Action |
|--------------|-------------------|
| Tests E1 | `pytest tests/test_e1_isolation.py -v -m "not slow"` |
| Tests E2/E3 | `pytest tests/test_e2_api.py tests/test_e3_quality_gate.py -v` |
| Quality gate E3 | `python scripts/run_e3_quality_gate.py` |
| Build Docker | `docker build -t datasens:latest .` |
| Config docker-compose | `docker-compose config` |

---

## Résultats attendus

- Tests : tous passent (ou continue-on-error pour tests lents)
- API : `/health` retourne `{"status": "ok"}`
- Cockpit : page de login puis accès aux onglets après authentification
- CI : workflow GitHub Actions vert sur push/PR
