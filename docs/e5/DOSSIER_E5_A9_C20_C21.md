# BLOC E5 — Maintien en Condition Opérationnelle (MCO) d'une application d'IA

Projet : DATASENS  
Candidat : Alan Jaffre

## Introduction

Le bloc E5 prolonge les blocs E2, E3 et E4 en se concentrant sur le maintien en condition opérationnelle (MCO) de l'application DataSens. Une fois l'application déployée et intégrée, il s'agit de la surveiller, de détecter les anomalies, de réagir aux incidents et de documenter les procédures pour garantir une exploitation durable.

Le livrable E5 démontre la capacité à définir des métriques de monitorage, à configurer des seuils d'alerte, à choisir et configurer des outils de consolidation (Prometheus, Grafana, Uptime Kuma), à intégrer la journalisation dans l'application, à mettre en place des alertes, et à résoudre des incidents techniques en suivant une procédure documentée et versionnée.

---

## A9. Maintien en Condition Opérationnelle (MCO) d'une application d'IA

### C20. Surveillance et Monitorage de l'Application

#### Définir les métriques pour le monitorage de l'application.

Les métriques de DataSens sont organisées en deux catégories : API E2/E3 et pipeline E1. Pour l'API, le middleware Prometheus (`src/e2/api/middleware/prometheus.py`) expose des compteurs, des histogrammes et des gauges. Les métriques principales sont : `datasens_e2_api_requests_total` (nombre de requêtes par méthode, endpoint et code HTTP), `datasens_e2_api_errors_total` (erreurs 4xx et 5xx), `datasens_e2_api_request_duration_seconds` (latence avec buckets de 0,01 à 10 s), `datasens_e2_api_authentications_total` (tentatives d'authentification réussies ou échouées), `datasens_e2_api_active_connections` (connexions actives). Les métriques de drift incluent `datasens_drift_sentiment_entropy`, `datasens_drift_topic_dominance`, `datasens_drift_score` et `datasens_drift_articles_total`, qui permettent de suivre la dérive de la distribution des prédictions et de déclencher un réentraînement si nécessaire.

Pour le pipeline E1, les métriques sont exposées via un serveur dédié (`scripts/run_e1_metrics.py` sur le port 8000) lorsque celui-ci est lancé. Elles incluent `datasens_pipeline_errors_total`, `datasens_source_errors_total` (erreurs par source), `datasens_enrichment_rate`, `datasens_articles_extracted_total` et `datasens_articles_in_database`. Ces indicateurs permettent de suivre la santé de la collecte, la qualité de l'enrichissement et la croissance de la base. L'ensemble des métriques est documenté dans `docs/METRIQUES_SEUILS_ALERTES.md`.

#### Définir les seuils ou valeurs d'alerte.

Les seuils sont définis dans `docs/METRIQUES_SEUILS_ALERTES.md` et implémentés dans `monitoring/prometheus_rules.yml`. Pour l'API E2, les alertes couvrent : un taux d'erreur supérieur à 5 % des requêtes par minute (warning), une latence p95 supérieure à 5 secondes pendant 5 minutes (warning), plus de 10 échecs d'authentification par minute (warning, suspicion de brute-force), plus de 100 connexions actives (warning, saturation possible), et un score de drift supérieur à 0,7 (warning, envisager un réentraînement).

Pour le pipeline E1, les alertes incluent : PipelineHighErrorRate (taux d'erreur > 0,1/s pendant 5 min), SourceExtractionFailure (taux d'erreur par source > 0,05/s pendant 5 min), LowEnrichmentRate (taux d'enrichissement < 0,5 pendant 10 min), NoArticlesCollected (aucun article collecté sur 1 heure, critical), et DatabaseGrowthStalled (croissance de la base < 1 article/heure pendant 2 heures). Ces seuils sont calibrés pour détecter les dégradations sans générer de faux positifs excessifs.

#### Choisir une solution ou un outil de consolidation et de suivi des indicateurs.

La stack de monitorage DataSens repose sur trois outils complémentaires. Prometheus assure la collecte et le stockage des métriques time-series, ainsi que l'évaluation des règles d'alerte ; il est accessible sur le port 9090. Grafana fournit la visualisation et la consolidation des indicateurs via des dashboards provisionnés automatiquement ; il est accessible sur le port 3000. Uptime Kuma assure la surveillance de disponibilité des services (API, Prometheus, Grafana) via des checks HTTP périodiques ; il est accessible sur le port 3001 (Docker Compose) ou 3002 (standalone).

Le choix de Prometheus est justifié par son adoption large pour les métriques, son modèle pull et son intégration native avec les règles d'alerte. Grafana offre des dashboards riches, un provisioning par fichiers et une connexion directe à Prometheus. Uptime Kuma permet de surveiller la disponibilité sans dépendre d'un service externe payant et offre une interface simple pour les alertes de type « service down ». Cette combinaison couvre les besoins de MCO pour un projet de taille MVP.

#### Configurer l'outil ou la solution de monitorage.

La configuration Prometheus distingue le mode local (`monitoring/prometheus.local.yml`, scrape de localhost:8001 et localhost:8000) et le mode Docker (`monitoring/prometheus.yml`, scrape des services dans le réseau Docker). Les règles d'alerte sont chargées depuis `monitoring/prometheus_rules.yml`. Le démarrage s'effectue via `start_prometheus.bat` ou `docker-compose up -d prometheus`.

Grafana est configuré par provisioning : la datasource Prometheus est définie dans `monitoring/grafana/provisioning/datasources/prometheus.yml`, et les dashboards sont provisionnés depuis `monitoring/grafana/provisioning/dashboards/dashboard.yml`. Les fichiers JSON des dashboards (`datasens-full.json`, `datasens-e1-dashboard.json`) couvrent toutes les routes de l'API E2, les métriques de drift, la latence et la surveillance des logs. Uptime Kuma est configuré manuellement au premier accès : création d'un compte admin, puis ajout des monitors pour l'API (http://localhost:8001/health), Prometheus (http://localhost:9090/-/healthy) et Grafana (http://localhost:3000/api/health). La procédure complète est documentée dans `docs/e5/PROCEDURE_INSTALLATION_MONITORING.md`.

#### Intégrer la journalisation nécessaire dans l'application.

La journalisation est centralisée via Loguru dans `src/logging_config.py`. La fonction `setup_logging()` configure un handler console (niveau configurable via `log_level`) et un handler fichier (`logs/datasens.log`) avec rotation à 10 Mo et rétention de 7 jours. Le format est uniforme : `{time} | {level} | {name}:{function} | {message}`. La configuration est appelée au démarrage de l'API E2 (`run_e2_api.py`) et du pipeline E1 (`main.py`).

Les modules applicatifs (API, pipeline, services) utilisent `loguru` pour tracer les erreurs, les opérations critiques et les événements de sécurité. Les tables SQLite `sync_log`, `cleaning_audit` et `data_quality_metrics` complètent la traçabilité métier pour les opérations de collecte et de nettoyage. Cette intégration assure une cohérence des logs sur l'ensemble de l'application et facilite le diagnostic en cas d'incident. La documentation détaillée figure dans `LOGGING.md`.

#### Intégrer des alertes en fonction des indicateurs.

Les alertes sont définies dans `monitoring/prometheus_rules.yml` et évaluées par Prometheus à chaque intervalle d'évaluation (30 secondes). Les groupes `datasens_alerts` et `datasens_api_drift_alerts` regroupent les règles par domaine. Chaque alerte spécifie une expression PromQL, une durée de persistance (`for`) et un niveau de sévérité (warning ou critical). Les annotations `summary` et `description` fournissent un contexte exploitable pour l'opérateur.

En production, un Alertmanager peut être configuré pour router les alertes vers des canaux de notification (email, Slack, PagerDuty). Les actions recommandées en cas d'alerte sont documentées dans `docs/METRIQUES_SEUILS_ALERTES.md` (section 4) : vérifier les logs, identifier la source en échec, tester la connectivité, vérifier les quotas API, etc. Cette intégration permet une réaction rapide aux anomalies sans surveillance manuelle continue.

#### Documenter le monitorage et les procédures d'installation et de configuration.

La documentation du monitorage couvre plusieurs niveaux. Le fichier `docs/METRIQUES_SEUILS_ALERTES.md` décrit les métriques, les seuils et les actions recommandées. Le fichier `docs/MONITORING_E2_API.md` présente l'architecture du monitoring de l'API E2 et l'endpoint `/metrics`. Le fichier `monitoring/README_GRAFANA.md` explique le démarrage de Prometheus et Grafana et la structure des dashboards. Le fichier `docs/e5/PROCEDURE_INSTALLATION_MONITORING.md` fournit une procédure pas à pas : prérequis, installation de Prometheus (script batch, ligne de commande, Docker), installation de Grafana, installation d'Uptime Kuma, ordre de démarrage recommandé, et liste des fichiers de configuration. Le fichier `docs/DEPLOYMENT.md` et `LANCER_TOUT.md` complètent la documentation pour le déploiement et le lancement complet. Les captures à produire sont listées dans `docs/E1_CAPTURES_MONITORING.md`.

---

### C21. Résolution d'Incidents Techniques

#### Analyser un message d'erreur.

La procédure de débogage définie dans `docs/PROCEDURE_INCIDENTS.md` prévoit une phase de localisation systématique. Les logs applicatifs (`logs/datasens.log`), les tables de traçabilité (`sync_log`, `user_action_log`) et la stack trace Python permettent d'identifier le fichier et la ligne à l'origine de l'exception. Les métriques Prometheus et Grafana fournissent le contexte temporel : pic d'erreurs, latence anormale, drift détecté. Le contexte opérationnel (source de données, moment de l'incident, environnement local ou CI) est essentiel pour distinguer une erreur de configuration d'une erreur de données.

La reproduction en local est une étape clé. Un script minimal ou un cas de test permet de valider l'hypothèse de cause et d'éviter les corrections hasardeuses. La procédure recommande d'exécuter les tests concernés (`pytest tests/test_e1_isolation.py`, `pytest tests/test_e2_api.py`) et, si nécessaire, de reproduire via un script Python ciblé. Cette approche assure que la solution proposée adresse bien la cause racine.

#### Rechercher une solution à l'aide de ressources externes.

La recherche de solution s'appuie sur plusieurs types de ressources. La documentation officielle des dépendances (FastAPI, Hugging Face, PySpark) fournit les bonnes pratiques et les limitations connues. Les issues GitHub des bibliothèques permettent de vérifier si l'erreur est déjà signalée et si une correction ou un contournement existe. Les forums spécialisés (Stack Overflow, communautés Python) offrent des retours d'expérience sur des erreurs similaires. Le CHANGELOG du projet et les commits récents permettent de détecter des régressions introduites par une modification récente.

Cette recherche est documentée dans la procédure d'incidents et peut être consignée dans l'issue GitHub associée. La traçabilité des sources consultées facilite la reproductibilité du raisonnement et la capitalisation des connaissances pour les incidents futurs.

#### Tester et valider la solution.

La validation de la solution suit une séquence structurée. La modification du code doit être ciblée et minimale pour limiter les effets de bord. Les tests unitaires et d'intégration sont exécutés localement via `pytest tests/ -v`. Le push sur une branche déclenche les workflows GitHub Actions ; le statut vert des jobs CI atteste que la correction n'introduit pas de régression. Enfin, la reproduction du scénario d'incident (données, commandes, environnement) permet de confirmer que le problème est résolu.

Cette validation en plusieurs étapes assure que la solution est correcte, qu'elle ne dégrade pas le reste de l'application et qu'elle est reproductible en conditions réelles. La procédure est décrite dans `docs/PROCEDURE_INCIDENTS.md` (section 2.3).

#### Versionner la solution depuis le dépôt Git.

La solution est versionnée selon les pratiques du projet. Le commit utilise un message structuré au format conventionnel : `fix: description courte` pour une correction de bug. Le lien vers l'issue est ajouté dans le message (`fixes #XX`) pour associer automatiquement le commit à l'issue et la fermer au merge. La modification est intégrée via une pull request, permettant une revue de code et une validation CI avant fusion sur la branche principale.

Cette pratique assure la traçabilité complète : chaque correction est reliée à un commit, une issue et éventuellement une entrée du CHANGELOG. L'exemple documenté (Incident 1.4.1, encodage GDELT) illustre ce processus dans `docs/PROCEDURE_INCIDENTS.md` (section 3).

#### Documenter l'erreur et la solution implémentée.

Chaque incident résolu est documenté à plusieurs endroits. Le fichier `CHANGELOG.md` reçoit une entrée avec la version, la date et une description synthétique de la correction. Le fichier `docs/PROCEDURE_INCIDENTS.md` peut inclure un exemple détaillé avec le contexte, la cause identifiée, la solution implémentée et la liste des fichiers modifiés. L'issue GitHub est mise à jour avec les étiquettes appropriées (`bug`, `incident`, `monitoring`) et le lien vers le commit de correction.

L'incident 1.4.1 (encodage GDELT) sert d'exemple de référence. Le problème (plantage du pipeline sur des fichiers JSON GDELT avec caractères invalides et null bytes) est décrit avec le symptôme (`UnicodeDecodeError` ou crash silencieux). La cause (null bytes, caractères de contrôle, caractère de remplacement Unicode dans les champs `title` et `content`) et la solution (fonction `sanitize_text()`, `ContentTransformer`, lecture JSON avec `errors='replace'`) sont documentées. Les fichiers modifiés (`src/e1/core.py`, `src/e1/aggregator.py`, `src/aggregator.py`) et le versionnement (commit CHANGELOG [1.4.1], 2025-02-10) complètent la traçabilité. Cette documentation permet de capitaliser les connaissances et d'accélérer la résolution d'incidents similaires.

---

## Tableau de couverture des compétences

| Compétence | Couverture | Preuve |
|------------|------------|--------|
| **C20** | Métriques, seuils, outils, configuration, journalisation, alertes, documentation | prometheus.py, METRIQUES_SEUILS_ALERTES, prometheus_rules.yml, logging_config.py, PROCEDURE_INSTALLATION_MONITORING |
| **C21** | Analyse d'erreur, recherche de solution, test, versionnement, documentation | PROCEDURE_INCIDENTS, CHANGELOG, exemple Incident 1.4.1 |

---

## Conclusion

Le bloc E5 démontre que DataSens dispose d'une chaîne de MCO opérationnelle. Les métriques sont définies et exposées via le middleware Prometheus et le serveur E1. Les seuils d'alerte sont configurés dans les règles Prometheus. La stack Prometheus, Grafana et Uptime Kuma est en place et documentée. La journalisation Loguru est intégrée dans l'application. Les alertes sont évaluées automatiquement et les actions recommandées sont documentées. La procédure de résolution d'incidents couvre l'analyse, la recherche, la validation, le versionnement et la documentation, avec un exemple concret (Incident 1.4.1) illustrant l'ensemble du processus.

Cette base permet de maintenir l'application en condition opérationnelle, de détecter les anomalies rapidement et de résoudre les incidents de manière traçable et reproductible.

---

## Annexes

### Annexe 1 : Preuves d'exécution E5

[docs/e5/ANNEXE_1_PREUVES_EXECUTION_E5.md](ANNEXE_1_PREUVES_EXECUTION_E5.md) — Commandes de lancement, vérifications, captures.

### Annexe 2 : Captures E5

[docs/e5/ANNEXE_2_CAPTURES_E5.md](ANNEXE_2_CAPTURES_E5.md) — Checklist des captures (Prometheus, Grafana, Uptime Kuma).

### Annexe 3 : Plan de soutenance E5

[docs/e5/ANNEXE_3_PLAN_DEMO_E5.md](ANNEXE_3_PLAN_DEMO_E5.md) — Script de démonstration.

### Annexe 4 : Extraits de code E5

[docs/e5/ANNEXE_4_EXTRAITS_CODE_E5.md](ANNEXE_4_EXTRAITS_CODE_E5.md) — Extraits représentatifs (Prometheus, Loguru, règles d'alerte).
