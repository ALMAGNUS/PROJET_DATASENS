# Annexe 12 - Plan demo E2 (15 min)

## Objectif

Demontrer C6, C7, C8 en 15 minutes avec des preuves concretes: veille, benchmark IA, parametrage/integration API, monitorage.

## 0:00 - 1:30 | Introduction

### Ce que je dis
"E2 couvre l'accompagnement du choix IA et son integration operationnelle. Je montre la chaine complete: veille, benchmark, integration API, supervision."

### Preuve
- Ouvrir `docs/Dossier_E2_A3_C6_C7_C8_FINAL.md`.

## 1:30 - 4:00 | C6 Veille outillee

### Ce que je montre
- `scripts/veille_sources.json`
- `scripts/veille_digest.py`
- une sortie `docs/veille/veille_YYYY-MM-DD.md`

### Ce que je dis
"La veille est industrialisee (config + script + livrables dates), puis integree aux decisions techniques."

## 4:00 - 8:00 | C7 Benchmark IA

### Ce que je montre
- `docs/e2/AI_BENCHMARK.md`
- `docs/e2/AI_BENCHMARK_RESULTS.json`
- annexe execution benchmark

### Ce que je dis
"Les modeles sont compares avec un protocole identique et des metriques explicites. La decision finale est justifiee par F1 macro, robustesse par classe et latence."

## 8:00 - 11:30 | C8 Integration API IA

### Ce que je montre
- `http://localhost:8001/redoc`
- endpoint `POST /api/v1/ai/predict`
- reponse JSON type (`label`, `confidence`, `sentiment_score`)

### Ce que je dis
"L'IA n'est pas isolee: elle est exposee via API REST documentee, securisee et exploitable par un front/cockpit."

## 11:30 - 13:30 | C8 Monitorage

### Ce que je montre
- `http://localhost:8001/metrics`
- `http://localhost:9090` (Prometheus)
- (optionnel) Grafana/Uptime Kuma

### Ce que je dis
"Le service est pilotable en production: metriques trafic/erreurs/latence et drift pour detecter les regressions."

## 13:30 - 15:00 | Conclusion

### Ce que je dis
"Le bloc E2 est operationnel et gouvernable: veille active, benchmark reproductible, integration API stable et supervision metrique."

## Questions probables

### "Pourquoi ce modele en prod?"
"Parce qu'il offre le meilleur compromis qualite globale / robustesse par classe dans nos contraintes CPU et metier."

### "Comment gerez-vous la derive?"
"Suivi des metriques drift + seuils d'alerte + relance benchmark/reentrainement quand seuils franchis."

### "Comment prouvez-vous que ce n'est pas theorique?"
"Par les executions scriptes, les logs, les rapports benchmark et les endpoints monitorage visibles."

