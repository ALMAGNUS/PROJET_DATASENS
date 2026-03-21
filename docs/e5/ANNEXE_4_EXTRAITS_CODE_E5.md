# Annexe 4 — Extraits de code E5 (illustration livrable)

Cette annexe regroupe **trois extraits de code** représentatifs du bloc E5. Ils illustrent respectivement l'exposition des métriques (C20), la configuration des alertes (C20) et la procédure de résolution d'incidents (C21).

---

## Extrait 1 — Exposition des métriques Prometheus (C20)

**Fichier** : `src/e2/api/middleware/prometheus.py`

**Compétence** : C20 — Définir les métriques pour le monitorage

**Contexte** : Le middleware Prometheus expose des counters, histograms et gauges. Les gauges de drift sont alimentées par l'endpoint `/api/v1/analytics/drift-metrics`. L'endpoint `/metrics` retourne le format texte Prometheus.

```python
# Gauges - Drift (mis à jour par l'endpoint /api/v1/analytics/drift-metrics)
drift_sentiment_entropy = Gauge(
    "datasens_drift_sentiment_entropy",
    "Entropy of sentiment distribution (higher = more balanced)",
    registry=e2_registry,
)
drift_topic_dominance = Gauge(
    "datasens_drift_topic_dominance",
    "Fraction of articles in the dominant topic (0-1, high = possible drift)",
    registry=e2_registry,
)
drift_score = Gauge(
    "datasens_drift_score",
    "Composite drift score (0=stable, 1=high drift)",
    registry=e2_registry,
)
drift_articles_total = Gauge(
    "datasens_drift_articles_total",
    "Number of articles used for drift computation",
    registry=e2_registry,
)
```

**Lien** : [src/e2/api/middleware/prometheus.py](../../src/e2/api/middleware/prometheus.py)

---

## Extrait 2 — Règles d'alerte Prometheus (C20)

**Fichier** : `monitoring/prometheus_rules.yml`

**Compétence** : C20 — Intégrer des alertes en fonction des indicateurs

**Contexte** : Les règles sont évaluées par Prometheus à intervalle régulier. En cas de dépassement du seuil pendant la durée indiquée, une alerte est déclenchée.

```yaml
groups:
  - name: datasens_alerts
    interval: 30s
    rules:
      - alert: PipelineHighErrorRate
        expr: rate(datasens_pipeline_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High pipeline error rate detected"
          description: "Pipeline error rate is {{ $value }} errors/sec"

      - alert: NoArticlesCollected
        expr: rate(datasens_articles_extracted_total[1h]) == 0
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "No articles collected in the last hour"
          description: "Pipeline has not collected any articles for 1 hour"
```

**Lien** : [monitoring/prometheus_rules.yml](../../monitoring/prometheus_rules.yml)

---

## Extrait 3 — Procédure de résolution d'incidents (C21)

**Fichier** : `docs/PROCEDURE_INCIDENTS.md`

**Compétence** : C21 — Documenter l'erreur et la solution implémentée

**Contexte** : Chaque incident suit un modèle en 8 étapes. L'exemple Incident 1.4.1 montre la traçabilité complète : contexte, cause, solution, fichiers modifiés, versionnement.

```markdown
## 3. Exemple documenté : Incident 1.4.1 (encodage GDELT)

### Contexte
- **Problème** : Plantage du pipeline lors du chargement de fichiers JSON GDELT
- **Symptôme** : UnicodeDecodeError ou crash silencieux

### Cause identifiée
- Null bytes, caractères de contrôle dans title et content
- Lecture JSON sans gestion d'erreur d'encodage

### Solution implémentée
1. sanitize_text() : Suppression des null bytes et caractères invalides
2. ContentTransformer : Application sur title et content
3. Lecture JSON : encoding='utf-8', errors='replace'

### Fichiers modifiés
- src/e1/core.py
- src/e1/aggregator.py

### Versionnement
- Commit : CHANGELOG [1.4.1]
- Dépôt : Git, branche main
```

**Lien** : [docs/PROCEDURE_INCIDENTS.md](../PROCEDURE_INCIDENTS.md)
