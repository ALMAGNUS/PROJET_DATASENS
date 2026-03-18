# Annexe 3 — Plan de soutenance E5 (15 min)

## Structure

| Durée | Séquence | Compétences |
|-------|----------|-------------|
| 0:00 - 1:30 | Contexte E5, périmètre A9 (MCO) | — |
| 1:30 - 5:00 | C20 Surveillance : métriques, seuils, outils | C20 |
| 5:00 - 8:00 | C20 Suite : journalisation, alertes, documentation | C20 |
| 8:00 - 11:00 | C21 Résolution incidents : procédure, exemple | C21 |
| 11:00 - 13:00 | Démo live : Prometheus, Grafana, Uptime Kuma | C20 |
| 13:00 - 15:00 | Conclusion, annexes, Q&A | — |

---

## Séquence 1 : Contexte (0:00 - 1:30)

- Présenter le bloc E5 (MCO après E2/E3/E4)
- Rappeler les compétences C20 et C21
- Montrer le dossier principal et le tableau de couverture

---

## Séquence 2 : C20 Surveillance — métriques et outils (1:30 - 5:00)

- **Métriques** : docs/METRIQUES_SEUILS_ALERTES.md — API E2 (requests, errors, drift), Pipeline E1
- **Seuils** : Tableau des seuils, niveaux warning/critical
- **Outils** : Prometheus (collecte), Grafana (visualisation), Uptime Kuma (disponibilité)
- **Configuration** : monitoring/prometheus_rules.yml, monitoring/grafana/

---

## Séquence 3 : C20 Suite — journalisation et alertes (5:00 - 8:00)

- **Journalisation** : src/logging_config.py (Loguru), logs/datasens.log, LOGGING.md
- **Alertes** : Règles Prometheus (PipelineHighErrorRate, NoArticlesCollected, etc.)
- **Documentation** : MONITORING_E2_API.md, PROCEDURE_INSTALLATION_MONITORING.md

---

## Séquence 4 : C21 Résolution incidents (8:00 - 11:00)

- **Procédure** : docs/PROCEDURE_INCIDENTS.md — 8 étapes (Identification → Documentation)
- **Exemple** : Incident 1.4.1 (encodage GDELT) — contexte, cause, solution, versionnement
- **Outils** : GitHub Issues, CHANGELOG, labels bug/incident/monitoring

---

## Séquence 5 : Démo live (11:00 - 13:00)

1. Ouvrir Prometheus (9090) → Targets, Graph avec datasens_*
2. Ouvrir Grafana (3000) → Dashboard DataSens
3. Ouvrir Uptime Kuma (3001) → Monitors
4. Montrer /metrics sur l'API (8001)
5. Montrer PROCEDURE_INCIDENTS.md et CHANGELOG

---

## Séquence 6 : Conclusion (13:00 - 15:00)

- Synthèse : MCO opérationnel, métriques + alertes + journalisation + procédure incidents
- Renvoi aux annexes (preuves, captures, extraits code)
- Q&A
