# Audit — Améliorations MCO, Docker et MLOps

**Date** : 2026-03  
**Objectif** : Identifier les pistes d'amélioration pour un MLOps et une surveillance parfaits.

---

## 1. État actuel (ce qui est déjà solide)

| Élément | Statut |
|--------|--------|
| Métriques API E2 (Prometheus) | ✅ Complet (requests, errors, latence, drift) |
| Grafana dashboards | ✅ Routes API, drift, logs |
| Uptime Kuma | ✅ Surveillance disponibilité |
| Journalisation Loguru | ✅ API + pipeline |
| Procédure incidents | ✅ Documentée + exemple |
| Drift-metrics endpoint | ✅ Avec fallback pandas |
| Quality gate E3 | ✅ Tests automatisés |
| Docker Compose | ✅ E1, E2 API, Prometheus, Grafana, Uptime Kuma |
| Healthchecks | ✅ E1, E2 API |

---

## 2. Améliorations recommandées

### 2.1 Alertes API E2 et drift (priorité haute)

**Constat** : `monitoring/prometheus_rules.yml` ne contient que des alertes E1 (pipeline). Les seuils API E2 et drift documentés dans `docs/METRIQUES_SEUILS_ALERTES.md` ne sont pas configurés dans Prometheus.

**Action** : Ajouter les règles d'alerte API E2 et drift dans `prometheus_rules.yml` :

- Taux d'erreur API > 5 %
- Latence p95 > 5 s
- Drift score > 0.7
- Échecs auth > 10/min

### 2.2 Docker — Volume models/ pour le modèle fine-tuné

**Constat** : Le service `datasens-e2-api` ne monte pas `./models/`. En production, le modèle fine-tuné (`SENTIMENT_FINETUNED_MODEL_PATH`) ne serait pas disponible dans le conteneur.

**Action** : Ajouter un volume `./models:/app/models` au service `datasens-e2-api` et documenter que le modèle doit être présent avant `docker-compose up`.

### 2.3 Docker — Ordre de démarrage (depends_on)

**Constat** : Prometheus scrape `datasens-e2-api` mais n'a pas de `depends_on`. Au démarrage, les premières scrapes peuvent échouer (API pas encore prête).

**Action** : Ajouter `depends_on: [datasens-e2-api]` à Prometheus (optionnel, Prometheus réessaie automatiquement).

### 2.4 E1 — Métriques en mode Docker

**Constat** : Le conteneur `datasens-e1` exécute `python main.py` qui termine après le pipeline. Les métriques E1 (port 8000) ne sont jamais exposées car le processus sort.

**Options** :
- **A** : Lancer E1 en cron/scheduler (exécution périodique) — les métriques E1 ne sont pas disponibles en continu (acceptable si focus sur API E2).
- **B** : Ajouter un service `datasens-e1-metrics` qui exécute `run_e1_metrics.py` pour exposer les métriques E1 en continu.
- **C** : Utiliser `METRICS_KEEP_ALIVE=1` dans la commande E1 pour garder le processus vivant après le run (mais le pipeline ne tourne qu'une fois).

### 2.5 MLOps — Alerte drift → recommandation réentraînement

**Constat** : Le drift est mesuré et exposé, mais aucune alerte Prometheus ne signale un drift élevé.

**Action** : Règle `DriftScoreHigh` dans `prometheus_rules.yml` : si `datasens_drift_score > 0.7` pendant 15 min → alerte "Envisager réentraînement".

### 2.6 MLOps — Versioning modèle (optionnel)

**Constat** : `trainer_state.json` et `TRAINING_RESULTS.json` assurent la traçabilité. **MLflow est désormais intégré** dans `finetune_sentiment.py` (params, metrics, config.json → `mlruns/`).

---

## 3. Synthèse des actions

| Priorité | Action | Effort |
|----------|--------|--------|
| **Haute** | Alertes API E2 + drift dans prometheus_rules.yml | Faible |
| **Haute** | Volume models/ dans docker-compose | Faible |
| **Moyenne** | Alerte DriftScoreHigh | Faible |
| **Moyenne** | depends_on Prometheus | Très faible |
| **Basse** | Service E1 metrics (si besoin métriques pipeline en continu) | Moyen |

---

## 4. Améliorations implémentées (2026-03)

| Action | Statut |
|--------|--------|
| Alertes API E2 + drift dans prometheus_rules.yml | ✅ Fait (DriftScoreHigh, APIHighErrorRate, APIHighLatency, APIAuthFailuresHigh) |
| Volume models/ dans docker-compose | ✅ Fait |
| depends_on Prometheus → datasens-e2-api | ✅ Fait |

---

## 5. Conclusion

Le projet est **solide** : surveillance complète (Grafana, Prometheus, Uptime Kuma, logs), drift-metrics, procédure incidents, Docker opérationnel. Les alertes API E2 et drift sont maintenant configurées, le volume models/ permet d'utiliser le modèle fine-tuné en Docker, et l'ordre de démarrage est optimisé.
