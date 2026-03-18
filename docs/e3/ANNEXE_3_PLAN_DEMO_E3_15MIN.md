# Annexe 3 - Plan demo E3 (15 min)

## Objectif demo

Montrer, en 15 minutes, que l'integration IA E3 est:
- exploitable via API REST,
- integree dans un flux applicatif,
- monitorable avec des metriques,
- securisee par des tests automatises et une CI.

## Preparation (avant passage de soutenance)

### Services a lancer

- API E2/E3 (port 8001)
- Prometheus (port 9090)
- (Optionnel) Grafana

### URLs utiles

- ReDoc: `http://localhost:8001/redoc`
- OpenAPI JSON: `http://localhost:8001/openapi.json`
- Predict IA: `http://localhost:8001/api/v1/ai/predict`
- Drift metrics: `http://localhost:8001/api/v1/analytics/drift-metrics?target_date=YYYY-MM-DD`
- Metrics Prometheus: `http://localhost:8001/metrics`
- Prometheus UI: `http://localhost:9090/graph`

### Commande de verification rapide

```bash
python scripts/run_e3_quality_gate.py
```

Attendu: `4 passed`.

---

## Deroule minute par minute (script oral)

## 0:00 - 1:30 | Introduction

### Ce que je fais
- Presenter le contexte E3 (A4/A5, C9 a C13).

### Ce que je dis (exemple)
"Dans E3, mon objectif est d'industrialiser l'integration du service IA: exposition REST, integration applicative, monitorage et quality gate CI/CD."

### Preuve visuelle
- Ouvrir `docs/e3/DOSSIER_E3_A4_A5_C9_C10_C11_C12_C13.md` (table de couverture).

---

## 1:30 - 4:00 | C9 - API IA exposee

### Ce que je fais
- Ouvrir ReDoc.
- Montrer endpoint `POST /api/v1/ai/predict`.
- Montrer schema request/response.

### Ce que je dis
"Le modele est expose par une API REST standard. Le contrat est stable: `text`, `model`, `task` en entree, et un resultat structure en sortie."

### Preuve visuelle
- Capture OpenAPI/ReDoc.

---

## 4:00 - 6:30 | C10 - Integration applicative

### Ce que je fais
- Executer un appel `POST /api/v1/ai/predict` (Swagger/ReDoc/Postman).
- Montrer la reponse JSON.

### Ce que je dis
"Cette reponse est directement consommable par un front ou un cockpit. Le format standardise simplifie l'integration et limite les regressions de contrat."

### Preuve visuelle
- Capture requete + reponse.

---

## 6:30 - 9:00 | C11 - Monitorage drift

### Ce que je fais
- Appeler `GET /api/v1/analytics/drift-metrics`.
- Montrer `drift_score` et `articles_total`.
- Ouvrir `/metrics` et filtrer `datasens_drift`.

### Ce que je dis
"Je calcule des indicateurs de drift pour piloter le modele dans le temps. Meme sans Spark/Java disponible, un fallback pandas garantit la disponibilite du service."

### Preuve visuelle
- Capture drift endpoint.
- Capture metrics Prometheus.

---

## 9:00 - 11:30 | C12 - Tests automatises

### Ce que je fais
- Lancer `python scripts/run_e3_quality_gate.py`.
- Montrer les 4 tests passes.

### Ce que je dis
"Le quality gate couvre les risques critiques: RAW vide sans crash, fallback drift, contrat predict, et exposition des gauges monitorage."

### Preuve visuelle
- Capture terminal avec `4 passed`.

---

## 11:30 - 13:30 | C13 - CI/CD

### Ce que je fais
- Ouvrir `.github/workflows/e3-quality-gate.yml`.
- Montrer le run GitHub Actions vert si disponible.

### Ce que je dis
"Le quality gate est automatise en CI sur push et pull request, ce qui bloque les regressions avant livraison."

### Preuve visuelle
- Capture workflow `E3 Quality Gate`.

---

## 13:30 - 15:00 | Conclusion

### Ce que je dis
"Le module E3 est operationnel: API IA exposee et integrable, monitorage actif, et controles qualite automatises localement et en CI. Cela permet une evolution iterative avec maitrise du risque."

### Cloture
- Rappeler emplacement preuves:
  - `docs/e3/ANNEXE_1_PREUVES_EXECUTION_QUALITY_GATE.md`
  - `docs/e3/ANNEXE_2_CAPTURES_E3.md`

---

## Questions probables (et reponses courtes)

### "Que se passe-t-il si Spark est indisponible ?"
"Le endpoint drift bascule automatiquement en calcul pandas, donc le service reste disponible."

### "Comment evitez-vous les regressions ?"
"Par un quality gate de tests cibles execute localement et en CI sur chaque push/PR."

### "Comment prouvez-vous l'integration reellement utilisable ?"
"Par le contrat OpenAPI, la reponse JSON du predict, et les captures d'execution avec metriques."

