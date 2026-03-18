# E5 — Maintien en Condition Opérationnelle (MCO)

## Organisation

- `DOSSIER_E5_A9_C20_C21.md` : dossier principal E5 (A9, C20, C21).
- `ANNEXE_1_PREUVES_EXECUTION_E5.md` : preuves d'exécution (monitoring, alertes).
- `ANNEXE_2_CAPTURES_E5.md` : checklist des captures visuelles à fournir.
- `ANNEXE_3_PLAN_DEMO_E5.md` : script de démonstration orale (15 min).
- `ANNEXE_4_EXTRAITS_CODE_E5.md` : extraits de code (Prometheus, logging, procédure incidents).
- `PROCEDURE_INSTALLATION_MONITORING.md` : procédure d'installation et de configuration du monitoring.

## Compétences couvertes

| Compétence | Description |
|------------|-------------|
| **C20** | Surveillance et monitorage de l'application |
| **C21** | Résolution d'incidents techniques |

## Preuves techniques

- Métriques : `src/e2/api/middleware/prometheus.py`
- Règles d'alerte : `monitoring/prometheus_rules.yml`
- Journalisation : `src/logging_config.py`, `run_e2_api.py` (setup_logging), `LOGGING.md`
- Procédure incidents : `docs/PROCEDURE_INCIDENTS.md`
- Métriques et seuils : `docs/METRIQUES_SEUILS_ALERTES.md`

## Script de vérification

```bash
python scripts/run_e5_verification.py
```

Vérifie la présence des fichiers E5 et, si l'API est démarrée, l'accessibilité de `/health` et `/metrics`.

## Plan de lancement global

Pour lancer tous les composants (Docker, API, MLflow, monitoring) dans le bon ordre : **`PLANCHE_LANCEMENT.md`** (à la racine du projet).
