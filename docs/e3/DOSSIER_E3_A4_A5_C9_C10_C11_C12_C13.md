# BLOC E3 — Exposition, intégration et pilotage MLOps des services IA

Projet : DATASENS  
Candidat : Alan Jaffre

## Introduction

Le bloc E3 prolonge le bloc E2 en industrialisant l'exposition du service IA, son intégration dans des applications consommatrices et son pilotage opérationnel. L'enjeu n'est plus seulement d'intégrer un modèle de sentiment ou un service génératif, mais de le rendre exploitable, observable et maintenable dans une chaîne de production.

Sur le plan technique, le socle est déjà en place : l'API REST FastAPI expose les endpoints IA et analytics, la sécurisation JWT/RBAC protège les accès, le middleware Prometheus instrumente les requêtes, et le cockpit Streamlit consomme l'API pour offrir une interface utilisateur métier. Le bloc E3 consolide cette base en ajoutant un quality gate ciblé (C9 à C13), exécutable localement et en CI, ainsi que des mécanismes de résilience pour garantir la stabilité du service en environnement contraint.

Le livrable E3 démontre la capacité à exposer un modèle IA via une API documentée, à l'intégrer dans une application, à le monitorer via des métriques de drift et de performance, puis à sécuriser cette chaîne par des tests automatisés et une intégration continue. Chaque compétence est reliée à une preuve d'implémentation concrète dans le code.

---

## A4. Compétence : Intégration d'un modèle ou service d'IA

### C9. Développement d'une API REST pour un Modèle d'IA

#### Analyser les spécifications fonctionnelles et techniques.

Les spécifications définissent un périmètre clair : exposition de l'inférence sentiment (Hugging Face local et Mistral) via des endpoints REST, exposition des analytics (distribution, drift, statistiques), authentification JWT et RBAC, et documentation OpenAPI. Les contrats de requête et de réponse sont formalisés dans `src/e2/api/schemas/ai.py` avec les modèles Pydantic AIPredictRequest, AIPredictResponse, InsightRequest et InsightResponse. Le cadrage fonctionnel est détaillé dans `docs/README_E2_API.md` et `docs/e2/AI_REQUIREMENTS.md`, qui précisent les attendus métier et les critères de qualité attendus pour la classification de sentiment.

Cette analyse préalable évite les dérives de périmètre. Elle fixe les frontières entre ce qui relève de l'API (exposition, validation, sécurité) et ce qui relève des services sous-jacents (inférence, accès données). La traçabilité entre spécifications et implémentation est assurée par la cohérence des schémas et des descriptions d'endpoints.

#### Concevoir l'architecture de l'API.

L'architecture retenue suit une séparation en couches. Les routes FastAPI (`/api/v1/ai/*` et `/api/v1/analytics/*`) constituent la couche d'exposition. Elles délèguent la logique métier aux services (LocalHFService pour l'inférence locale, MistralService pour le chat et le résumé) et l'accès aux données aux lecteurs (E1DataReader, GoldParquetReader). Le middleware Prometheus intercepte les requêtes HTTP pour alimenter les métriques sans modifier le flux applicatif.

Cette conception permet d'évoluer chaque couche indépendamment. Le remplacement d'un modèle ou l'ajout d'un endpoint n'impacte pas la structure globale. Les points d'entrée sont documentés dans `src/e2/api/main.py`, les routes IA dans `src/e2/api/routes/ai.py` et les routes analytics dans `src/e2/api/routes/analytics.py`. La cohérence architecturale est maintenue par des dépendances explicites et des contrats stables.

#### Choisir les outils et langages de programmation.

Le choix technique repose sur Python 3.10+, FastAPI, Pydantic et Uvicorn. FastAPI offre une génération automatique de la documentation OpenAPI, une validation des entrées native et des performances adaptées à un service d'inférence. Hugging Face fournit l'inférence locale pour le sentiment, Mistral AI le chat et le résumé. Prometheus est retenu pour la collecte des métriques, en cohérence avec les pratiques MLOps courantes.

Ces choix sont documentés dans `requirements.txt` et justifiés par la compatibilité avec la stack existante du projet, la maturité des bibliothèques et la facilité de déploiement en environnement CPU-first.

#### Installer et configurer l'environnement de développement.

L'environnement de développement est configuré via un venv Python et l'installation des dépendances. La séquence standard consiste à créer le venv (`python -m venv .venv`), l'activer, puis installer les paquets (`pip install -r requirements.txt`). Les variables d'environnement sont centralisées dans un fichier `.env` (non versionné) avec des exemples fournis dans `.env.example`. Les variables critiques incluent MISTRAL_API_KEY pour le service génératif, SENTIMENT_FINETUNED_MODEL_PATH pour le modèle local, et DB_PATH pour la base de données.

Cette configuration est décrite dans le README et permet une reproductibilité complète entre postes de développement. La séparation entre code et configuration évite les secrets dans le dépôt et facilite l'adaptation aux différents contextes d'exécution.

#### Développer la vérification et la transformation des paramètres.

La vérification des paramètres est assurée par les schémas Pydantic. AIPredictRequest impose la présence de text, model et task. InsightRequest impose theme et message. Les requêtes Mistral (ChatRequest, SummarizeRequest, SentimentRequest) ajoutent des contraintes de longueur (min_length, max_length) pour éviter les abus et les erreurs de traitement. FastAPI applique automatiquement cette validation avant l'exécution du handler ; en cas d'erreur, une réponse 422 est retournée avec le détail des champs invalides.

Cette approche réduit la surface d'attaque et garantit que les services sous-jacents ne reçoivent jamais de données mal formées. Les schémas sont définis dans `src/e2/api/schemas/ai.py` et réutilisés dans les routes pour assurer la cohérence entre documentation et implémentation.

#### Développer l'exécution du modèle à partir de la requête client.

L'exécution du modèle suit un flux linéaire. Le endpoint `POST /api/v1/ai/predict` reçoit une AIPredictRequest, extrait le texte, appelle `LocalHFService.predict(payload.text)` et retourne les scores de sentiment dans une AIPredictResponse. Les endpoints Mistral (chat, summarize, sentiment) vérifient d'abord la disponibilité du service via `get_mistral_service().is_available()`, puis appellent les méthodes correspondantes. En cas d'indisponibilité, une erreur 503 est retournée avec un message explicite.

La logique d'inférence locale est encapsulée dans `src/ml/inference/local_hf_service.py`, qui charge le modèle configuré et applique le pipeline de tokenisation et de prédiction. Cette séparation permet de tester les routes avec des mocks sans charger de modèle réel.

#### Développer la réponse de l'API avec le résultat du modèle.

Les réponses sont typées et conformes aux schémas OpenAPI. AIPredictResponse contient model, task et result (liste de dictionnaires avec label, confidence, sentiment_score). ChatResponse et SummarizeResponse contiennent respectivement response et summary. InsightResponse contient reply et theme. Le format JSON est généré automatiquement par FastAPI et documenté dans l'interface Swagger et ReDoc.

Cette standardisation facilite l'intégration par les clients et permet une validation automatique des contrats. Les schémas sont définis dans `src/e2/api/schemas/ai.py` et utilisés via le paramètre `response_model` des décorateurs de route.

#### Développer les règles d'autorisation et d'accès.

Tous les endpoints IA et analytics sont protégés par la dépendance `require_reader`, définie dans `src/e2/api/dependencies/permissions.py`. Cette dépendance vérifie que l'utilisateur authentifié possède l'un des rôles reader, writer, deleter ou admin. En l'absence de token valide ou de rôle suffisant, une erreur 401 ou 403 est retournée.

Les règles sont appliquées de manière uniforme via `Depends(require_reader)` sur chaque route. Cette approche centralise la logique d'autorisation et évite les oublis. La granularité des rôles permet d'étendre facilement les permissions si de nouveaux profils sont nécessaires.

#### Sécuriser l'API.

La sécurisation repose sur plusieurs couches. L'authentification JWT (python-jose) garantit l'identité des utilisateurs. Le hachage des mots de passe (passlib/bcrypt) protège les données sensibles. La validation des entrées (Pydantic) limite les injections et les données malformées. La gestion des erreurs (HTTPException avec codes 503, 404, 500) évite les fuites d'information et fournit des messages adaptés aux clients.

Les bonnes pratiques OWASP sont documentées dans `README_E2_API.md`. La configuration de sécurité est centralisée dans `src/e2/auth/security.py`, qui gère la création et la vérification des tokens, ainsi que le hachage des mots de passe.

#### Développer des tests d'intégration.

Les tests d'intégration couvrent les points critiques de la chaîne d'exposition. Les tests `tests/test_e2_api.py` valident les contrats des endpoints généraux. Les tests `tests/test_e3_quality_gate.py` ciblent spécifiquement : le contrat predict avec un modèle mocké (test_ai_predict_endpoint_contract_with_stubbed_local_model), le fallback drift lorsque Spark échoue (test_drift_metrics_endpoint_uses_pandas_fallback_when_spark_fails), l'exposition des métriques Prometheus après appel à drift (test_metrics_expose_drift_gauge_after_drift_call), et la robustesse aux données RAW vides (test_read_raw_data_empty_csv_returns_empty_dataframe).

Ces tests utilisent pytest, TestClient FastAPI et monkeypatch pour isoler les dépendances. Aucun modèle réel n'est chargé, ce qui garantit une exécution rapide et reproductible. Le script `scripts/run_e3_quality_gate.py` encapsule l'exécution des tests E3 pour une validation locale ou en CI.

#### Versionner les sources avec Git.

Les sources sont versionnées dans un dépôt Git. Les commits suivent une convention de message (fix, feat, docs) pour faciliter la traçabilité. Les workflows GitHub Actions s'exécutent sur chaque push et pull request vers les branches main et develop, garantissant que les modifications sont validées avant intégration.

Cette pratique assure une historisation complète des évolutions et permet de revenir à un état stable en cas de régression. Le dépôt Git et les workflows sont présents dans `.git/` et `.github/workflows/`.

#### Rédiger et/ou générer la documentation de l'API.

La documentation de l'API est générée automatiquement par FastAPI à partir des schémas Pydantic et des docstrings des routes. Swagger UI est accessible via `/docs` et permet d'exécuter des requêtes de test directement depuis le navigateur. ReDoc est accessible via `/redoc` et offre une lecture structurée de la documentation. Le schéma OpenAPI brut est disponible via `/openapi.json` pour une intégration machine ou des outils tiers.

Les descriptions des endpoints, les exemples de requête et de réponse, et les schémas de données sont inclus dans cette documentation. Un export statique peut être conservé pour archivage. La documentation est accessible à l'adresse `http://localhost:8001/docs` lorsque l'API est démarrée.

---

### C10. Intégration de l'API dans une Application

#### Installer l'environnement de développement de l'application.

L'application consommatrice principale est le cockpit Streamlit. Elle partage le même environnement que l'API : le venv `.venv`, les dépendances installées via `pip install -r requirements.txt`, et les variables d'environnement définies dans `.env`. Cette configuration commune évite les incompatibilités de versions et simplifie le déploiement.

Le cockpit est lancé via `streamlit run src/streamlit/app.py`. La configuration est documentée dans le README. L'application consommatrice et l'API peuvent être exécutées sur le même poste ou sur des machines distinctes, selon la configuration réseau.

#### Programmer les étapes d'authentification et d'autorisation.

Le cockpit gère l'authentification via l'endpoint `/api/v1/auth/login`. L'utilisateur saisit ses identifiants, le cockpit envoie une requête POST et reçoit un token JWT. Ce token est stocké dans la session Streamlit et transmis dans l'en-tête `Authorization: Bearer <token>` pour chaque appel API ultérieur.

Les étapes d'autorisation sont implicites : si le token est valide et que l'utilisateur possède le rôle reader ou supérieur, les endpoints répondent. En cas d'échec d'authentification, le cockpit redirige vers l'écran de connexion. Cette logique est implémentée dans `src/streamlit/app.py` via la gestion du session_state et des appels HTTP authentifiés.

#### Programmer la communication avec l'API.

La communication avec l'API s'effectue via des appels HTTP (httpx ou requests) vers l'URL de base configurée (par défaut `http://localhost:8001`). Les endpoints consommés incluent `GET /api/v1/ai/status` pour vérifier la disponibilité, `POST /api/v1/ai/predict` pour l'inférence sentiment, `POST /api/v1/ai/insight` pour l'assistant IA, et `GET /api/v1/analytics/drift-metrics` pour les métriques de dérive.

Les requêtes incluent l'en-tête d'autorisation et les corps JSON conformes aux schémas API. Les réponses sont parsées et affichées dans l'interface. La gestion des erreurs (timeout, 401, 503) est implémentée pour offrir un retour utilisateur clair. Le code de communication est centralisé dans `src/streamlit/app.py`.

#### Intégrer les adaptations d'interface.

Le cockpit Streamlit propose des vues adaptées aux contrats API. Les vues par thème (politique, financier, utilisateurs) correspondent aux thèmes supportés par l'endpoint insight. Les formulaires de prédiction et d'assistant sont alignés sur les champs requis (text, theme, message). L'affichage des réponses (labels, scores, réponses texte) est structuré pour faciliter la lecture.

Les adaptations d'interface incluent également la gestion des états de chargement, des messages d'erreur et des cas où le service n'est pas disponible. L'interface est conçue pour être utilisable sans connaissance technique de l'API. Les composants sont définis dans `src/streamlit/app.py`.

#### Tester et valider l'accessibilité des interfaces.

L'accessibilité des interfaces est validée par des tests manuels et automatisés. Les tests automatisés utilisent le TestClient FastAPI pour simuler les requêtes et vérifier les réponses. Les endpoints critiques (`/health`, `/docs`, `/api/v1/ai/status`) sont accessibles lorsque l'API est démarrée.

Le script `python scripts/run_e5_verification.py` vérifie la présence des fichiers de configuration et l'accessibilité de `/health` et `/metrics` lorsque l'API est démarrée. Cette validation est une preuve d'accessibilité pour la soutenance.

#### Développer des tests d'intégration.

Les tests d'intégration couvrent à la fois l'API et le flux consommateurs. Les tests `tests/test_e2_api.py` et `tests/test_e3_quality_gate.py` valident les contrats en conditions contrôlées. Les tests utilisent des mocks pour isoler les dépendances externes (modèles, Mistral) et garantir une exécution rapide.

La validation des flux inclut les cas nominaux : requête predict, réponse conforme au schéma, erreur 503 lorsque Mistral absent. Les tests du cockpit peuvent être exécutés manuellement ou via des outils de test end-to-end si nécessaire. Le périmètre de test est documenté dans `tests/test_e3_quality_gate.py`.

#### Versionner les sources avec Git.

Les sources du cockpit et de l'API sont versionnées dans le même dépôt Git. Cette cohérence permet de tracer les évolutions conjointes et de garantir la compatibilité des versions. Les modifications sont commitées avec des messages explicites et suivent la convention du projet.

---

## A5. Compétence : Facilitation du déploiement avec une approche MLOps

### C11. Monitorage d'un Modèle d'IA

#### Lister les métriques du modèle à monitorer.

Les métriques à monitorer sont définies et documentées dans `docs/METRIQUES_SEUILS_ALERTES.md`. Elles couvrent le volume de requêtes (`datasens_e2_api_requests_total`), les erreurs (`datasens_e2_api_errors_total`), la latence (`datasens_e2_api_request_duration_seconds`), les authentifications (`datasens_e2_api_authentications_total`), et les indicateurs de drift (`datasens_drift_sentiment_entropy`, `datasens_drift_topic_dominance`, `datasens_drift_score`, `datasens_drift_articles_total`).

Ces métriques permettent de piloter la qualité de service, de détecter les anomalies, de suivre la dérive des données et d'objectiver les décisions de réentraînement. La liste est exhaustive et alignée aux besoins opérationnels du projet.

#### Choisir une solution ou un outil pour le monitorage.

La solution retenue repose sur Prometheus pour la collecte des métriques, Grafana pour la restitution visuelle, et Uptime Kuma pour la surveillance de disponibilité. Prometheus est le standard pour les métriques time-series, Grafana offre des dashboards riches et un provisioning automatique, Uptime Kuma assure la surveillance de disponibilité sans dépendance à un service externe payant.

Cette stack est cohérente avec les pratiques MLOps courantes et documentée dans `monitoring/prometheus.yml` et `monitoring/grafana/`. La configuration est versionnée et reproductible.

#### Intégrer la solution ou l'outil de monitorage.

L'intégration est réalisée via le middleware Prometheus dans `src/e2/api/middleware/prometheus.py`, qui expose l'endpoint `/metrics` au format texte Prometheus. Prometheus scrape cet endpoint à intervalle régulier (configuré dans `monitoring/prometheus.yml`). Les règles d'alerte sont définies dans `monitoring/prometheus_rules.yml` et évaluées par Prometheus.

Les gauges de drift sont alimentées par l'endpoint `/api/v1/analytics/drift-metrics`, appelé périodiquement ou par le cockpit. Cette chaîne garantit que les métriques sont à jour et exploitables pour le pilotage.

#### Sélectionner un outil de restitution des métriques.

Grafana est retenu pour la restitution des métriques. La datasource Prometheus est provisionnée automatiquement dans `monitoring/grafana/provisioning/datasources/prometheus.yml`. Les dashboards sont provisionnés depuis `monitoring/grafana/dashboards/` et couvrent les routes API, le drift, la latence et la surveillance des logs.

Le dashboard principal `datasens-full.json` regroupe les indicateurs essentiels pour la soutenance et l'exploitation. L'import manuel est possible si nécessaire via l'interface Grafana.

#### Intégrer l'outil de restitution et les alertes.

Les dashboards Grafana sont intégrés au flux de provisionnement et s'affichent automatiquement au démarrage. Les alertes sont configurées dans `monitoring/prometheus_rules.yml` et évaluées par Prometheus. Les alertes incluent PipelineHighErrorRate, NoArticlesCollected, SourceExtractionFailure, LowEnrichmentRate, DatabaseGrowthStalled, ainsi que les alertes API (drift, latence, erreurs, auth).

En production, un Alertmanager peut être configuré pour router les alertes (email, Slack, PagerDuty). La documentation des seuils et des actions recommandées est dans `docs/METRIQUES_SEUILS_ALERTES.md`.

#### Tester et valider le bon fonctionnement de la chaîne de monitorage.

La validation est effectuée en vérifiant que `GET /metrics` retourne les gauges attendues, que les cibles Prometheus sont UP dans l'interface Status → Targets, et que Grafana affiche les courbes correctement. Le script `python scripts/run_e5_verification.py` vérifie l'accessibilité de `/health` et `/metrics` lorsque l'API est démarrée.

Les preuves d'exécution sont documentées dans `docs/e5/ANNEXE_1_PREUVES_EXECUTION_E5.md`. Une capture d'écran de Prometheus Targets et de Grafana constitue une preuve visuelle pour la soutenance.

#### Versionner les sources avec Git.

Les fichiers de configuration Prometheus, Grafana et les règles d'alerte sont versionnés dans le dépôt. Le dossier `monitoring/` contient l'ensemble des configurations nécessaires. Cette versionisation permet de reproduire la chaîne de monitorage sur tout environnement et de tracer les évolutions.

#### Rédiger la documentation technique et utilisateur.

La documentation technique couvre les métriques, les seuils, les alertes et les procédures d'installation. Les documents de référence sont `docs/METRIQUES_SEUILS_ALERTES.md`, `docs/MONITORING_E2_API.md`, `docs/e5/PROCEDURE_INSTALLATION_MONITORING.md` et `monitoring/README_GRAFANA.md`. La documentation utilisateur est intégrée dans les annexes E5 et dans le guide de lancement `PLANCHE_LANCEMENT.md`.

---

### C12. Tests Automatisés d'un Modèle d'IA

#### Définir le périmètre des tests pour chaque composante du modèle.

Le périmètre des tests E3 cible quatre composantes critiques. La robustesse des données : le cas d'un fichier RAW vide ne doit pas provoquer d'erreur 500. La résilience du drift : l'endpoint drift-metrics doit fonctionner même si Spark/Java est indisponible, via un fallback pandas. Le contrat API : l'endpoint predict doit retourner une réponse JSON conforme au schéma. L'exposition des métriques : les gauges Prometheus doivent être visibles après un appel à drift-metrics.

Ce périmètre est documenté dans `tests/test_e3_quality_gate.py` et aligné avec les risques identifiés en production (environnement contraint, données manquantes, défaillance Spark).

#### Choisir les outils de test.

Les outils retenus sont pytest pour l'exécution des tests, pytest-asyncio pour les tests asynchrones, et le TestClient FastAPI pour simuler les requêtes HTTP. Le monkeypatch de pytest permet d'isoler les dépendances (modèles, services externes) et de garantir une exécution rapide sans chargement de ressources lourdes.

Ces outils sont présents dans `requirements.txt` et configurés dans `pytest.ini`. Le choix est cohérent avec la stack Python du projet et les pratiques de test courantes.

#### Installer et configurer l'environnement d'exécution des tests.

L'environnement d'exécution des tests est identique à l'environnement de développement. L'installation des dépendances via `pip install -r requirements.txt` suffit. Le PYTHONPATH est configuré pour permettre l'import des modules du projet (défini dans le workflow CI et dans les instructions du README).

Le workflow `.github/workflows/e3-quality-gate.yml` exécute les tests sur un environnement Ubuntu avec Python 3.10. La configuration est reproductible localement et en CI.

#### Intégrer les tests.

Les tests sont intégrés dans le dépôt sous `tests/test_e3_quality_gate.py`. Le script `scripts/run_e3_quality_gate.py` encapsule l'exécution des tests E3 et retourne un code de sortie conforme au résultat du pytest. Ce script est invoqué par le workflow CI et peut être exécuté localement avant un commit.

L'intégration garantit que les tests sont exécutés systématiquement et que les régressions sont détectées avant intégration. Les quatre tests du quality gate passent en conditions normales.

#### Versionner les sources et les données avec Git.

Les sources des tests et les données de test (fichiers CSV vides, mocks) sont versionnées dans le dépôt. Cette pratique assure la reproductibilité des tests et permet de tracer les évolutions du périmètre de test.

#### Rédiger la documentation technique.

La documentation technique des tests est fournie dans `docs/e3/ANNEXE_1_PREUVES_EXECUTION_QUALITY_GATE.md` (description des cas, commandes, résultats attendus) et `docs/e3/ANNEXE_4_EXTRAITS_CODE_E3.md` (extraits de code illustratifs). Les annexes facilitent la compréhension par le jury et la reprise par un autre développeur.

---

### C13. Création d'une Chaîne de Livraison Continue

#### Définir les étapes, tâches et déclencheurs de la chaîne de livraison continue.

La chaîne de livraison continue est définie dans `.github/workflows/e3-quality-gate.yml`. Les étapes sont : checkout du code, configuration de Python, installation des dépendances, exécution du quality gate. Les déclencheurs sont les événements push et pull_request sur les branches main et develop.

Cette définition assure que toute modification proposée est validée avant intégration. La chaîne est légère et ciblée : elle valide la stabilité de l'exposition et du monitorage sans inclure de déploiement automatique dans l'état actuel.

#### Paramétrer la chaîne de livraison continue.

Le paramétrage est réalisé dans le fichier YAML du workflow. Le job utilise l'image ubuntu-latest, Python 3.10, et le cache pip pour accélérer le build. La variable PYTHONPATH est configurée pour importer les modules. La commande finale exécute `python scripts/run_e3_quality_gate.py`.

Le paramétrage est déclaratif et versionné. Toute modification peut être tracée et validée par revue de code.

#### Intégrer l'exécution des tests du modèle et des données.

Le quality gate exécute `pytest tests/test_e3_quality_gate.py`. Les tests couvrent le modèle (contrat predict, métriques) et les données (RAW vide, fallback drift). L'intégration de ces tests dans la chaîne garantit que les modifications ne dégradent pas la chaîne d'exposition et de monitorage.

En cas d'échec, le pipeline est rouge et signale une régression. Cette intégration est essentielle pour la confiance dans les livraisons.

#### Intégrer les étapes d'entraînement et d'évaluation du modèle.

L'entraînement et l'évaluation du modèle sont réalisés hors CI, via les scripts `scripts/run_training_loop_e2.bat` et `scripts/finetune_sentiment.py`. La CI ne déclenche pas d'entraînement car celui-ci est long et coûteux en ressources. La CI valide en revanche que l'exposition du modèle (API, métriques) reste fonctionnelle après une modification de code.

Cette séparation est un choix pragmatique : la CI assure la stabilité du socle, tandis que l'entraînement est déclenché manuellement ou par un pipeline dédié si nécessaire.

#### Intégrer la génération des rapports d'évaluation.

Les rapports d'évaluation (TRAINING_RESULTS.json, AI_BENCHMARK_RESULTS.json) sont générés par les scripts d'entraînement et de benchmark. La CI ne génère pas ces rapports ; elle valide que la chaîne d'exposition et de monitorage reste opérationnelle. Les rapports sont conservés dans `docs/e2/` pour traçabilité et exploitation manuelle.

#### Intégrer l'étape de livraison.

L'étape de livraison est réalisée manuellement ou via Docker. La commande `docker-compose up -d` déploie l'API, Prometheus, Grafana, Uptime Kuma et le service E1-metrics. Il n'y a pas de déploiement automatique dans la CI actuelle. La procédure de livraison est documentée dans `docker-compose.yml` et `PLANCHE_LANCEMENT.md`.

Ce choix est adapté au contexte projet (démo, école) où un déploiement manuel ou semi-automatisé est suffisant. Une extension vers un déploiement automatique (ex. Kubernetes, cloud) est possible sans modifier la structure CI.

#### Versionner les sources de la chaîne avec Git.

Le workflow et les scripts de la chaîne sont versionnés : `.github/workflows/e3-quality-gate.yml`, `scripts/run_e3_quality_gate.py`, `tests/test_e3_quality_gate.py`. Toute évolution est tracée et reproductible.

#### Documenter les procédures d'installation et de test de la chaîne.

Les procédures sont documentées dans `PLANCHE_LANCEMENT.md` (ordre de démarrage, Docker, local), `docs/e5/PROCEDURE_INSTALLATION_MONITORING.md` (monitoring), et `README.md` (installation générale). Les procédures sont reproductibles et permettent à un nouvel intervenant de mettre en place l'environnement sans ambiguïté.

#### Documenter l'utilisation de la chaîne.

L'utilisation de la chaîne est documentée dans `LANCER_TOUT.md` (lancement simplifié), `PLANCHE_LANCEMENT.md` (scénarios complets), et les annexes E3 (preuves, captures, plan de démonstration). Ces documents fournissent les instructions pour lancer l'API, le cockpit, le monitoring, et pour valider le bon fonctionnement.

---

## Conclusion

Le bloc E3 de DATASENS présente une chaîne d'exposition et de pilotage IA opérationnelle, testée et intégrée en CI. L'API REST expose les modèles de sentiment et les capacités Mistral via des contrats documentés. Le cockpit Streamlit consomme ces contrats pour offrir une interface utilisateur métier. Le monitorage Prometheus et l'endpoint drift-metrics permettent de suivre la performance et la dérive des données. Les tests automatisés et le workflow CI garantissent que cette chaîne reste stable et reproductible.

La résilience introduite (fallback pandas, gestion RAW vide) assure que le service reste exploitable en environnement contraint, ce qui est essentiel pour les démonstrations et les livraisons. En synthèse, le bloc E3 démontre une compétence d'industrialisation complète : exposition, intégration, monitorage, tests et CI/CD pour un service IA.

---

## Annexes

### Annexe 1 : Preuves d'exécution du quality gate E3

Les preuves d'exécution sont consolidées dans [docs/e3/ANNEXE_1_PREUVES_EXECUTION_QUALITY_GATE.md](ANNEXE_1_PREUVES_EXECUTION_QUALITY_GATE.md). Ce document décrit la commande d'exécution, le résultat attendu (4 tests passés), les cas vérifiés (RAW vide, fallback drift, contrat predict, métriques Prometheus) et l'interprétation pour la soutenance.

### Annexe 2 : Captures E3 (checklist)

La checklist des captures à produire est fournie dans [docs/e3/ANNEXE_2_CAPTURES_E3.md](ANNEXE_2_CAPTURES_E3.md). Elle précise le nommage des fichiers, les écrans obligatoires (CI Quality Gate, API Predict, Drift Metrics, Prometheus Gauges, Documentation API) et la procédure de collecte.

### Annexe 3 : Plan de soutenance E3 (15 min)

Le script de démonstration minute par minute est disponible dans [docs/e3/ANNEXE_3_PLAN_DEMO_E3_15MIN.md](ANNEXE_3_PLAN_DEMO_E3_15MIN.md). Il structure la soutenance en séquences alignées sur les compétences C9 à C13 et sur les preuves visuelles correspondantes.

### Annexe 4 : Extraits de code E3 (illustration jury)

Trois extraits de code représentatifs sont regroupés dans [docs/e3/ANNEXE_4_EXTRAITS_CODE_E3.md](ANNEXE_4_EXTRAITS_CODE_E3.md) : exposition API predict (C9), résilience drift-metrics (C11), test automatisé du fallback (C12). Chaque extrait est accompagné du contexte, du lien vers le fichier complet et d'une synthèse pour le jury.
