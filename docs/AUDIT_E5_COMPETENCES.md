# 🔍 Audit E5 — Grille de compétences (A9 : Maintien en condition opérationnelle)

**Date**: 2026-02-12  
**Projet**: DataSens

---

## A9. Assurer le maintien en condition opérationnelle d'une application IA

### C20. Surveiller une application d'intelligence artificielle

| Critère | Statut | Justification |
|---------|--------|---------------|
| Documentation liste les métriques et les seuils/valeurs d'alerte | ✅ TRUE | `docs/METRIQUES_SEUILS_ALERTES.md` : tableau complet E1 + E2, seuils, niveaux, actions |
| Documentation explicite les arguments des choix techniques (outillage) | ✅ TRUE | Section "Choix techniques" dans `docs/MONITORING_E2_API.md` : Prometheus, Grafana, architecture |
| Outils installés et opérationnels en local | ✅ TRUE | Prometheus (scrape /metrics), Grafana (dashboards), PrometheusMiddleware, `start_grafana.bat`, `prometheus.local.yml` |
| Règles de journalisation intégrées aux sources | ✅ TRUE | `sync_log`, `user_action_log`, `AuditMiddleware`, loguru ; `docs/LOGGING.md` documente les tables et flux |
| Alertes configurées et en état de marche | ✅ TRUE | `prometheus_rules.yml` + `rule_files` dans `prometheus.local.yml` ; alertes actives en local |
| Documentation procédure installation/config monitoring | ✅ TRUE | `monitoring/README_GRAFANA.md`, `docs/MONITORING_E2_API.md`, `LANCER_TOUT.md`, `DEPLOY.md` |
| Documentation format accessible | ✅ TRUE | `docs/ACCESSIBILITE_DOCUMENTATION.md` : références AVH/Microsoft, structure Markdown, procédure export |

### C21. Résoudre les incidents techniques

| Critère | Statut | Justification |
|---------|--------|---------------|
| La ou les causes du problème sont identifiées correctement | ✅ TRUE | `docs/PROCEDURE_INCIDENTS.md` : modèle RCA + exemple 1.4.1 (null bytes, encodage) |
| Le problème est reproduit en environnement de développement | ✅ TRUE | Procédure : pytest, script minimal ; exemple documenté |
| La procédure de débogage est documentée depuis l'outil de suivi | ✅ TRUE | Procédure dans PROCEDURE_INCIDENTS.md ; section "Suivi" (GitHub Issues) |
| La solution documentée explicite chaque étape de résolution | ✅ TRUE | Modèle 8 étapes + exemple complet (contexte, cause, solution, fichiers, versionnement) |
| La solution est versionnée dans le dépôt Git | ✅ TRUE | Git, commits, merge/push ; workflow CI/CD |

---

## Synthèse E5

| Compétence | OK | Partiel | KO |
|------------|-----|---------|-----|
| C20 | 7 | 0 | 0 |
| C21 | 5 | 0 | 0 |

---

### Statut : ✅ 100 % conforme

**Réalisé** :
- `docs/METRIQUES_SEUILS_ALERTES.md`
- `docs/PROCEDURE_INCIDENTS.md`
- `docs/ACCESSIBILITE_DOCUMENTATION.md`
- Section "Choix techniques" dans `MONITORING_E2_API.md`
- `rule_files` activés dans `prometheus.local.yml`

---

## Références des artefacts

| Critère | Fichiers |
|---------|----------|
| C20 | `docs/MONITORING_E2_API.md`, `monitoring/README_GRAFANA.md`, `monitoring/prometheus_rules.yml`, `monitoring/prometheus.local.yml`, `docs/LOGGING.md`, `src/e2/api/middleware/prometheus.py` |
| C21 | `CHANGELOG.md`, dépôt Git, `.github/workflows/` |
