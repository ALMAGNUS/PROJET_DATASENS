# Annexe 1 — Preuves d'exécution E5

## Objectif

Prouver que le bloc E5 (MCO) est opérationnel : métriques exposées, alertes configurées, journalisation intégrée, procédure d'incidents documentée.

---

## C20 — Surveillance et monitorage

### 1. Métriques API exposées

**Commande** :
```bash
python run_e2_api.py
# Dans un autre terminal :
curl http://localhost:8001/metrics
```

**Résultat attendu** : Texte au format Prometheus avec `datasens_e2_api_requests_total`, `datasens_drift_*`, etc.

### 2. Prometheus collecte les métriques

**Commande** :
```bash
start_prometheus.bat
# ou : docker-compose up -d prometheus
```

**Vérification** : http://localhost:9090 → Status → Targets → cible API E2 en UP.

### 3. Grafana affiche les dashboards

**Commande** :
```bash
start_grafana.bat
# ou : docker-compose up -d grafana
```

**Vérification** : http://localhost:3000 → Dashboards → DataSens (datasens-full.json).
Les dashboards couvrent toutes les routes API, drift, latence et surveillance des logs.

### 4. Uptime Kuma surveille les services

**Commande** :
```bash
docker-compose up -d uptime-kuma
# ou : start_uptime_kuma.bat
```

**Vérification** : http://localhost:3001 → Monitors API, Prometheus, Grafana.

### 5. Règles d'alerte configurées

**Fichier** : `monitoring/prometheus_rules.yml`

**Contenu** : PipelineHighErrorRate, SourceExtractionFailure, LowEnrichmentRate, NoArticlesCollected, DatabaseGrowthStalled.

### 6. Vérification E5 (script)

**Commande** :
```bash
python scripts/run_e5_verification.py
```

**Résultat attendu** : Fichiers E5 présents, et si l'API est démarrée, /health et /metrics accessibles.

---

## C21 — Résolution d'incidents

### 1. Procédure documentée

**Fichier** : `docs/PROCEDURE_INCIDENTS.md`

**Contenu** : Modèle de gestion d'incident (8 étapes), procédure de débogage, exemple Incident 1.4.1 (encodage GDELT).

### 2. Exemple d'incident résolu et versionné

- **Problème** : UnicodeDecodeError sur fichiers GDELT (null bytes, caractères invalides).
- **Solution** : sanitize_text(), ContentTransformer, encoding='utf-8', errors='replace'.
- **Fichiers** : src/e1/core.py, src/e1/aggregator.py.
- **Versionnement** : CHANGELOG, commit Git, issue GitHub.

---

## Interprétation pour la soutenance

Cette annexe démontre que le MCO n'est pas seulement documenté : les métriques sont exposées et collectées, les alertes sont configurées, la journalisation est intégrée, et une procédure de résolution d'incidents est en place avec un exemple concret versionné.
