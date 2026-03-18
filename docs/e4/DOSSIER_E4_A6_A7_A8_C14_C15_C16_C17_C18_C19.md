# BLOC E4 — Conception, développement et livraison de l'application intégrant l'IA

Projet : DATASENS  
Candidat : Alan Jaffre

## Introduction

Le bloc E4 couvre la conception, le développement et la livraison de l'application DataSens intégrant les services IA (E2/E3). Il s'articule autour de trois axes : la conception (A6), le développement des interfaces et fonctionnalités (A7), et les fonctions de tests et de livraison continue (A8).

L'application DataSens comprend un cockpit Streamlit (interface de pilotage), une API REST FastAPI (exposition des services IA et analytics), et une chaîne de données (RAW → SILVER → GOLD → GoldAI). Le bloc E4 démontre la capacité à modéliser les besoins, concevoir l'architecture, développer les composants, gérer les droits d'accès, sécuriser l'application, et automatiser les tests et la livraison.

---

## A6. Conception d'une application intégrant un service d'IA

### C14. Analyse du Besoin et Spécifications Fonctionnelles

#### Modéliser les données de l'application.

La modélisation des données repose sur une architecture multi-zones et multi-bases. Les zones de données suivent un flux Merise : RAW (données brutes extraites, CSV/JSON dans `data/raw/sources_YYYY-MM-DD/`), SILVER (données nettoyées et dédupliquées, Parquet dans `data/silver/v_YYYY-MM-DD/`), GOLD (données agrégées et enrichies, Parquet dans `data/gold/date=YYYY-MM-DD/`), et GoldAI (fusion pour l'IA, splits train/val/test dans `data/goldai/ia/`). La base SQLite DataSens contient les entités principales : `source` (métadonnées des sources), `raw_data` (articles ingérés), `sync_log` (historique de synchronisation), `topic` et `document_topic` (association articles-topics), `model_output` (prédictions ML), et `profils` (utilisateurs et rôles RBAC). Les schémas détaillés sont documentés dans `docs/SCHEMA_DESIGN.md`, `docs/ARCHITECTURE_DB.md` et `docs/EXPLICATION_RELATIONS_MERISE.md`. Cette modélisation assure la traçabilité des données de la collecte jusqu'à l'inférence IA.

#### Modéliser les parcours utilisateurs.

Les parcours utilisateurs sont décrits dans `docs/e4/PARCOURS_UTILISATEUR.md`. Cinq flux principaux sont identifiés. Le parcours d'authentification : accès au cockpit, formulaire de login, appel API `POST /api/v1/auth/login`, réception du JWT, accès aux pages protégées. Le parcours de pilotage des données : accès à l'onglet Pilotage, visualisation du flux Parquet, fusion GoldAI, création de la copie IA (splits train/val/test). Le parcours de pilotage IA : accès au Benchmark, affichage des résultats, filtres topics, option de fine-tuning. Le parcours de prédiction sentiment : saisie de texte, appel `POST /api/v1/ai/predict`, affichage du label et de la confiance. Le parcours Assistant IA : sélection du thème (politique, financier, utilisateurs), saisie d'une question, appel `POST /api/v1/ai/insight`, affichage de la réponse Mistral enrichie. Les diagrammes de flux et le schéma fonctionnel global sont fournis dans le document. Le flux de données est également visualisé dans `docs/PLAN_STREAMLIT_E2.md` et `docs/DATA_FLOW.md`.

#### Rédiger les spécifications fonctionnelles sous forme de user stories.

Les spécifications fonctionnelles sont formalisées dans `docs/AGILE_ROADMAP.md` sous forme de user stories. La structure distingue trois personas (Décideur politique, Investisseur financier, Chercheur/Analyste), des Epics (Collecte omnicanale, Qualité et nettoyage, Intelligence de sentiment, Dashboards, API et intégration, Monitoring, Fine-tuning IA, Gouvernance), et des user stories au format « En tant que… Je veux… Afin de… » avec critères de succès et définition de fait. Par exemple, la US 1.1 précise qu'en tant que Décideur politique ou Journaliste, l'utilisateur veut recevoir automatiquement tous les articles presse du jour afin de rester informé, avec des critères mesurables (au moins 500 articles par jour, apparition dans les 30 minutes, alerte en cas de source indisponible). Cette formalisation permet de prioriser les développements et de valider les livraisons par des critères objectifs.

#### Définir les objectifs techniques d'accessibilité des interfaces.

Les objectifs d'accessibilité sont documentés dans `docs/e4/OBJECTIFS_ACCESSIBILITE.md` et `docs/ACCESSIBILITE_DOCUMENTATION.md`. Les référentiels retenus sont WCAG 2.1 niveau AA, RG2AA, et les recommandations de l'Association Valentin Haüy et de Microsoft. Les critères appliqués incluent : titres hiérarchiques (structure H1/H2/H3 dans Markdown et interfaces), contraste (texte lisible selon le thème), texte alternatif pour les images (descriptions en légende), listes et tableaux avec en-têtes explicites et structure sémantique, format accessible pour l'export (Markdown vers Word/PDF via Pandoc). Les user stories prioritaires intègrent des critères d'accessibilité dans leur définition de fait, par exemple la structure de titres pour l'interface cockpit ou les en-têtes explicites pour les tableaux de documentation. L'export accessible est privilégié pour les lecteurs d'écran.

---

### C15. Conception du Cadre Technique

#### Concevoir l'architecture de l'application.

L'architecture est décrite dans `docs/ARCHITECTURE.md` et `docs/ARCHITECTURE_DB.md`. La vue d'ensemble place les sources (RSS, API) en entrée du pipeline E1 (extraction, nettoyage, chargement), qui alimente les Parquet GOLD et GoldAI. L'API E2/E3 FastAPI expose les endpoints et consomme ces données. Le cockpit Streamlit s'authentifie via JWT/RBAC et communique avec l'API. Les composants principaux sont : le pipeline E1 (`main.py`, `src/e1/`), l'API E2/E3 (`run_e2_api.py`, `src/e2/api/`), le cockpit (`src/streamlit/app.py`), l'inférence (`src/ml/inference/`), et le monitoring (Prometheus, Grafana, Uptime Kuma, middleware Prometheus). Cette architecture assure une séparation claire des responsabilités et permet d'évoluer chaque couche indépendamment.

#### Choisir les langages de programmation et les outils de développement.

Le choix technique repose sur Python 3.10+ pour l'écosystème data (pandas, PySpark), ML (transformers) et API (FastAPI). FastAPI est retenu pour l'API en raison de ses performances, de sa documentation OpenAPI native et du typage Pydantic. Streamlit est choisi pour l'interface en raison du prototypage rapide et de l'intégration Python native. SQLite assure le stockage léger sans serveur, adapté au MVP. PySpark gère les agrégations sur Parquet avec fallback pandas. Docker assure la reproductibilité et le déploiement. GitHub Actions fournit l'intégration continue. Ces choix sont cohérents avec les contraintes projet (CPU-first, maîtrise des coûts) et documentés dans `requirements.txt` et les guides d'architecture.

#### Identifier les flux de données et les zones de stockage.

Les flux sont documentés dans `docs/DATA_FLOW.md`, `docs/CHEMIN_DONNEE.md` et `docs/PLAN_STREAMLIT_E2.md`. Le flux principal suit la séquence : SOURCES → COLLECT → CLEAN → LOAD → TAG → ANALYZE → AGGREGATE → GOLD. En aval, le script `merge_parquet_goldai.py` fusionne les partitions GOLD en GoldAI, puis `create_ia_copy.py` génère les splits train/val/test. Les zones de stockage sont : `data/raw/` (CSV/JSON bruts), `data/silver/` (Parquet nettoyés), `data/gold/` (Parquet agrégés par date), `data/goldai/` (fusion et splits IA), `data/datasens.db` (SQLite pour buffer, profils, logs), et `models/` (modèles fine-tunés Hugging Face). Cette cartographie permet de tracer la provenance des données et de garantir la cohérence des traitements.

#### Choisir les services externes complémentaires.

Les services externes retenus sont Mistral (chat, résumé, assistant insights, configuré via `MISTRAL_API_KEY`, optionnel), Hugging Face (modèles sentiment téléchargés à la demande), MongoDB (archivage Parquet via GridFS, `MONGODB_URI` optionnel), Prometheus (métriques, `monitoring/prometheus.yml`), et Grafana (dashboards, provisioning automatique). Mistral et MongoDB sont optionnels pour permettre un fonctionnement en environnement contraint. L'API et le cockpit restent opérationnels sans ces services, avec des réponses 503 ou des fonctionnalités désactivées lorsque nécessaire.

#### Rédiger les spécifications techniques.

Les spécifications techniques sont regroupées dans plusieurs documents. `docs/ARCHITECTURE.md` décrit la structure du projet, les modules et les dépendances. `docs/ARCHITECTURE_DB.md` détaille les schémas des bases et les relations. `docs/README_E2_API.md` documente les endpoints, l'authentification et la couverture OWASP. `docs/SCHEMA_DESIGN.md` précise les tables et les schémas Parquet. `requirements.txt` liste les dépendances Python. `.env.example` fournit les variables d'environnement attendues. Cet ensemble constitue une base technique complète pour le développement et la maintenance.

---

## A7. Développement des interfaces et fonctionnalités

### C16. Coordination de la Réalisation Technique

#### Mettre en place les outils et supports de pilotage de la production.

Les outils de pilotage sont décrits dans `docs/GITHUB_PROJECTS_SETUP.md` et `docs/AGILE_ROADMAP.md`. Un Kanban GitHub Projects structure le travail avec les colonnes Backlog, To Do, In Progress, Review et Done. Des labels permettent de catégoriser les issues par epic (collecte, enrichissement, etc.), statut et priorité. Un template d'issues formalise les user stories avec critères d'acceptation et définition de fait. Le backlog est maintenu dans `docs/AGILE_ROADMAP.md` avec les Epics, les user stories et leurs critères. Ces supports assurent une visibilité sur l'avancement et une traçabilité des décisions.

#### Faciliter les rituels agiles et le respect du cadre.

Le cadre Agile est défini dans `docs/AGILE_STRUCTURE.md` et `docs/AGILE_ROADMAP.md`. Pour un projet MVP en solo, les rituels sont adaptés au contexte : revues de backlog pour prioriser les user stories, validation des US par critères de succès, démonstrations incrémentales via le cockpit. Le respect du cadre est assuré par la discipline de mise à jour des documents et par l'alignement des commits et des livraisons sur les user stories. Cette approche pragmatique maintient la rigueur méthodologique sans surcharger un projet à effectif réduit.

#### Communiquer l'avancement des productions techniques.

L'avancement est tracé via plusieurs canaux. Les commits Git utilisent des messages structurés (feat, fix, docs) pour faciliter la lecture de l'historique. Le fichier `CHANGELOG.md` consolide l'historique des versions et des modifications notables. Le dépôt GitHub organise les branches `main` et `develop` et les pull requests pour valider les intégrations. La documentation (README, BUILD_AND_DEPLOY, guides techniques) est mise à jour au fil des livraisons. Cette communication assure la transparence et permet aux parties prenantes de suivre l'évolution du projet.

#### Communiquer les imprévus et les changements.

Les imprévus et changements sont documentés dans `docs/PROCEDURE_INCIDENTS.md`, `CHANGELOG.md` et les issues GitHub. La procédure d'incidents couvre l'analyse des erreurs, la recherche de solutions, les tests de validation et la documentation des corrections. Chaque incident résolu est versionné et relié à une entrée du CHANGELOG. Les issues GitHub permettent de tracer les bugs et les évolutions avec des labels appropriés. Cette pratique garantit une traçabilité complète des imprévus et des changements de périmètre ou de conception.

---

### C17. Développement des Composants et Interfaces

#### Installer l'environnement de développement.

L'environnement de développement est décrit dans `README.md` et `requirements.txt`. La procédure standard consiste à cloner le dépôt, créer un environnement virtuel (`python -m venv .venv`), l'activer, installer les dépendances (`pip install -r requirements.txt`), copier `.env.example` vers `.env` et configurer les variables (DB_PATH, MISTRAL_API_KEY, etc.). Le lancement de l'API s'effectue via `python run_e2_api.py` et celui du cockpit via `streamlit run src/streamlit/app.py`. Cette procédure est reproductible et documentée pour Windows et Linux.

#### Intégrer la mise en page et les contenus des interfaces.

Le cockpit Streamlit (`src/streamlit/app.py`) intègre une mise en page personnalisée via des classes CSS (`.ds-hero`, `.ds-card`, `.ds-flow`), des colonnes et des onglets. Les contenus incluent la visualisation du flux Parquet, des bases SQLite et MongoDB, des graphiques chronologiques et des métriques IA. La navigation est assurée par une sidebar avec les sections Pilotage, Benchmark et Assistant IA, et par l'authentification en amont. Les contenus sont adaptés aux contrats API et aux données disponibles.

#### Développer les fonctionnalités front-end.

Les fonctionnalités front-end du cockpit couvrent plusieurs domaines. L'onglet Pilotage propose une vue du flux Parquet, les boutons de fusion GoldAI et de création de la copie IA, et la mise à jour des graphiques et compteurs. L'onglet Benchmark affiche les résultats (F1 macro, accuracy, latence par modèle), les filtres topics (finance, politique) et l'option de lancer un cycle de fine-tuning. L'onglet Assistant IA permet la sélection du thème, la consultation des exemples, la saisie de questions et l'affichage des réponses Mistral enrichies. L'interface de prédiction permet la saisie de texte et l'affichage du label et de la confiance. Ces fonctionnalités sont implémentées dans `src/streamlit/app.py`.

#### Développer les composants métiers.

Les composants métiers sont répartis dans plusieurs modules. Le pipeline E1 (`src/e1/`) gère l'extraction, le nettoyage et le chargement. Les routes API (`src/e2/api/routes/`) exposent les endpoints IA, analytics et auth. L'inférence (`src/ml/inference/`) fournit le LocalHFService, le sentiment et l'intégration Mistral. Le module Spark (`src/spark/`) assure la lecture Parquet et le traitement des agrégations. Les scripts (`scripts/`) incluent create_ia_copy, finetune_sentiment, ai_benchmark et merge_parquet_goldai. Cette répartition assure une séparation claire des responsabilités et une maintenabilité du code.

#### Gérer les droits et accès à l'application.

La gestion des droits repose sur JWT et RBAC, implémentés dans `src/e2/auth/security.py`. Les rôles sont définis dans la table `profils` : reader, writer, admin. Les zones (raw, silver, gold) sont accessibles selon les permissions associées aux rôles. Les routes API utilisent les dépendances `require_reader` et `require_writer` pour contrôler l'accès. Le script `scripts/create_test_user.py` permet de créer des utilisateurs de test. Cette gestion centralisée assure une cohérence des droits sur l'ensemble de l'application.

#### Intégrer les composants d'accès aux données.

Les accès aux données sont assurés par plusieurs composants. L'E1DataReaderImpl assure la lecture des zones RAW, SILVER et GOLD en respectant l'isolation E1. Le GoldParquetReader lit les Parquet GOLD via PySpark ou pandas en fallback. Les routes API (`/raw/`, `/silver/`, `/gold/`) exposent ces données avec un contrôle RBAC. L'intégration garantit que les composants métier accèdent aux données via des interfaces stables et que les modifications de stockage n'impactent pas les consommateurs.

#### Sécuriser l'application.

La sécurité est documentée dans `docs/README_E2_API.md` (section OWASP). L'authentification repose sur JWT avec expiration et mécanisme de refresh. L'autorisation est gérée par RBAC par zone et par rôle. La validation des entrées utilise les schémas Pydantic et des limites de taille pour éviter les abus. Les en-têtes CORS et le rate limiting sont configurés au niveau du middleware. Les secrets sont stockés dans des variables d'environnement, jamais en dur dans le code. Cette approche couvre les principaux risques identifiés par OWASP.

#### Intégrer des tests automatisés.

Les tests sont regroupés dans `tests/`. Le fichier `tests/test_e1_isolation.py` valide l'isolation E1 et le pipeline. Le fichier `tests/test_e2_api.py` teste les endpoints API et l'authentification. Le fichier `tests/test_e3_quality_gate.py` couvre les cas critiques : RAW vide, fallback drift, contrat predict, métriques Prometheus. L'exécution utilise pytest avec des marqueurs (slow, not slow) pour adapter la durée des runs. Les tests sont intégrés aux workflows CI et exécutables localement via `python scripts/run_e3_quality_gate.py`.

#### Versionner les sources avec Git.

Le dépôt est versionné avec Git. La structure des branches inclut `main` pour la production et `develop` pour l'intégration. Les branches feature sont utilisées pour les développements isolés. Les pull requests permettent de valider les modifications avant intégration. Les workflows GitHub Actions sont dans `.github/workflows/` (test, ci-cd, e3-quality-gate). Cette organisation assure une traçabilité complète et une validation systématique des changements.

#### Prendre en compte les enjeux d'accessibilité.

Les enjeux d'accessibilité sont documentés dans `docs/ACCESSIBILITE_DOCUMENTATION.md` et `docs/e4/OBJECTIFS_ACCESSIBILITE.md`. L'application respecte une structure de titres cohérente, un contraste suffisant, un texte alternatif pour les images et des tableaux avec en-têtes explicites. L'export Markdown vers Word/PDF via Pandoc est privilégié pour les documents accessibles aux lecteurs d'écran. Les user stories intègrent des critères d'accessibilité dans leur définition de fait. La navigation au clavier est supportée nativement par Streamlit.

#### Rédiger la documentation technique.

La documentation technique couvre plusieurs niveaux. Le `README.md` constitue le guide principal avec l'installation et le lancement. Le fichier `docs/ARCHITECTURE.md` décrit la structure et les modules. Le fichier `docs/README_E2_API.md` documente l'API, l'authentification et les exemples. Le fichier `docs/BUILD_AND_DEPLOY.md` explique le build Docker et le déploiement. Le fichier `docs/QUICK_START.md` fournit un démarrage rapide. Cette documentation permet une prise en main rapide et une maintenance efficace.

---

## A8. Développement des fonctions de tests et de contrôle

### C18. Automatisation des Tests avec Intégration Continue

#### Choisir l'outil d'intégration continue.

L'outil retenu est GitHub Actions, dont les workflows sont définis dans `.github/workflows/`. Ce choix est justifié par l'intégration native avec le dépôt GitHub, la gratuité pour les dépôts publics et privés (dans les limites des minutes), et la facilité de configuration via des fichiers YAML versionnés. GitHub Actions permet d'exécuter des tests, des builds Docker et des déploiements de manière reproductible et traçable.

#### Définir les étapes, tâches et déclencheurs.

Les étapes et déclencheurs sont définis dans les workflows. Le workflow `test.yml` s'exécute sur push et pull_request, avec les jobs test-e1-isolation et test-e1-complete (ce dernier sur main uniquement, marqué slow). Le workflow `ci-cd.yml` enchaîne test, build et deploy sur push et pull_request vers main et develop. Le workflow `e3-quality-gate.yml` exécute le quality gate E3 sur push et pull_request vers main et develop. Les étapes incluent checkout, setup Python 3.10, installation des dépendances, configuration du PYTHONPATH et exécution des tests. La description détaillée est dans `docs/e4/CI_CHAINE_TESTS.md`.

#### Produire les fichiers de configuration.

Les fichiers de configuration sont produits dans `.github/workflows/` au format YAML. Chaque workflow définit les événements de déclenchement, les jobs, les étapes et les variables d'environnement. Les fichiers sont versionnés avec le code et modifiables par revue de code. La structure est documentée dans `docs/e4/CI_CHAINE_TESTS.md` avec un tableau récapitulatif des workflows et de leurs paramètres.

#### Configurer l'automatisation.

La configuration inclut l'action setup-python avec cache pip pour accélérer les builds, la variable PYTHONPATH pour l'import des modules, l'exécution de pytest avec les marqueurs appropriés, et l'action docker/build-push-action pour le build et le push des images. Les secrets (GITHUB_TOKEN) sont gérés automatiquement par GitHub. Les permissions sont configurées pour permettre le checkout, l'écriture des packages (ghcr.io) et l'accès aux artefacts.

#### Tester et valider le bon fonctionnement de la chaîne.

La chaîne est validée par l'exécution des workflows sur chaque push et pull request. Le statut vert des jobs dans l'interface GitHub atteste du bon fonctionnement. En local, la commande `python scripts/run_e3_quality_gate.py` permet de reproduire les tests du quality gate E3 avant un push. Les logs GitHub Actions fournissent le détail des étapes en cas d'échec. Cette validation assure que les modifications ne dégradent pas la chaîne.

#### Versionner les sources de configuration.

Les workflows sont versionnés dans le dépôt Git sous `.github/workflows/*.yml`. Toute modification de la chaîne CI est tracée et peut être revue. La versionisation assure la reproductibilité de la configuration et permet de revenir à un état stable en cas de régression.

#### Documenter les procédures d'installation et de test.

Les procédures sont documentées dans `docs/BUILD_AND_DEPLOY.md`, `docs/PHASE_1_DOCKER_CI_CD_COMPLETE.md` et `docs/e4/CI_CHAINE_TESTS.md`. La procédure d'installation inclut le clonage, l'installation des dépendances, la configuration du PYTHONPATH et l'exécution des tests E1 et du quality gate E3. La procédure de test local est reproductible et permet de valider l'environnement avant intégration.

#### Documenter l'utilisation de la chaîne.

L'utilisation de la chaîne est documentée dans le README, BUILD_AND_DEPLOY et les annexes E4. Les développeurs peuvent comprendre comment déclencher les workflows (push, pull request), interpréter les statuts (vert, rouge) et consulter les logs. La documentation est intégrée au dépôt pour une accessibilité immédiate.

---

### C19. Création d'un Processus de Livraison Continue

#### Définir les étapes, tâches et déclencheurs de la chaîne de livraison continue.

La chaîne de livraison continue est définie dans `.github/workflows/ci-cd.yml`. Les étapes sont : test (lint, pytest, validation structure), build (construction de l'image Docker, push vers ghcr.io), et deploy (placeholder pour le déploiement, exécuté uniquement sur main). Les déclencheurs sont le push et le pull_request sur main et develop. Le déploiement ne s'exécute que sur main après un push réussi. La description détaillée est dans `docs/e4/CD_CHAINE_LIVRAISON.md`.

#### Paramétrer la chaîne de livraison continue.

Le paramétrage utilise les actions docker/build-push-action, docker/metadata-action et docker/login-action. Les permissions incluent `packages: write` pour le push vers ghcr.io. Les tags de l'image incluent la branche, le numéro de PR, la version sémantique et le SHA du commit. Le contexte de build est la racine du projet et le Dockerfile est à la racine. Ce paramétrage assure une livraison reproductible et traçable.

#### Configurer les étapes automatisées à partir de la chaîne d'intégration continue.

Le job build dépend du job test (`needs: test`). Le job deploy dépend du job build et ne s'exécute que sur main. En cas d'échec des tests, le build n'est pas exécuté. En cas d'échec du build, le deploy n'est pas exécuté. Cette chaîne garantit que seules les modifications validées par les tests sont livrées. L'étape deploy est actuellement un placeholder (echo) et peut être remplacée par un déploiement effectif (docker-compose, Kubernetes, etc.).

#### Versionner les configurations de la chaîne.

Les configurations sont dans `.github/workflows/ci-cd.yml` et versionnées avec le dépôt. Toute évolution de la chaîne CD est tracée et peut être revue. La versionisation assure la reproductibilité et la traçabilité des changements de processus de livraison.

#### Tester la chaîne de livraison continue.

La chaîne est testée par un push sur main : les jobs s'exécutent successivement (test, build, deploy), le build Docker produit une image, le push vers ghcr.io est effectué si le contexte n'est pas une pull request. La vérification du statut vert des jobs et des artefacts produits (image Docker) constitue la preuve de bon fonctionnement. En cas d'échec, les logs permettent d'identifier la cause.

#### Documenter la procédure de livraison continue.

La procédure est documentée dans `docs/e4/CD_CHAINE_LIVRAISON.md` et `docs/BUILD_AND_DEPLOY.md`. Le document CD décrit les étapes, les déclencheurs, la configuration du build Docker, le packaging de l'image et la procédure de livraison (développement sur develop, PR vers main, validation CI, merge, exécution du deploy). La documentation permet de comprendre et de reproduire le processus de livraison.

---

## Tableau de couverture des compétences

| Compétence | Couverture | Preuve |
|------------|------------|--------|
| **C14** | Modélisation données, parcours, user stories, accessibilité | SCHEMA_DESIGN, PARCOURS_UTILISATEUR, AGILE_ROADMAP, OBJECTIFS_ACCESSIBILITE |
| **C15** | Architecture, langages, flux, services externes, specs techniques | ARCHITECTURE, ARCHITECTURE_DB, DATA_FLOW, README_E2_API |
| **C16** | Outils pilotage, rituels, communication avancement | GITHUB_PROJECTS_SETUP, AGILE_ROADMAP, CHANGELOG |
| **C17** | Env dev, interfaces, composants, droits, données, sécurité, tests, Git, accessibilité, doc | README, streamlit/app.py, src/e2/, tests/, requirements.txt |
| **C18** | Outil CI, étapes, config, automatisation, versionnement, doc | .github/workflows/, CI_CHAINE_TESTS |
| **C19** | Étapes CD, paramétrage, config, versionnement, tests, doc | ci-cd.yml, CD_CHAINE_LIVRAISON |

---

## Conclusion

Le bloc E4 de DataSens démontre une chaîne complète de conception, développement et livraison. Les spécifications fonctionnelles (user stories) et techniques (architecture, schémas) sont documentées. Le cockpit Streamlit et l'API FastAPI intègrent les services IA et respectent les droits d'accès. Les tests automatisés et les workflows CI/CD garantissent la qualité et la reproductibilité des livraisons.

---

## Annexes

### Annexe 1 : Preuves d'exécution E4

[docs/e4/ANNEXE_1_PREUVES_E4.md](ANNEXE_1_PREUVES_E4.md) — Commandes de lancement, vérifications, captures d'écran.

### Annexe 2 : Captures E4

[docs/e4/ANNEXE_2_CAPTURES_E4.md](ANNEXE_2_CAPTURES_E4.md) — Checklist des captures (cockpit, API, CI/CD, monitoring).

### Annexe 3 : Plan de soutenance E4

[docs/e4/ANNEXE_3_PLAN_DEMO_E4.md](ANNEXE_3_PLAN_DEMO_E4.md) — Script de démonstration (15 min).

### Annexe 4 : Extraits de code E4

[docs/e4/ANNEXE_4_EXTRAITS_CODE_E4.md](ANNEXE_4_EXTRAITS_CODE_E4.md) — Extraits représentatifs (Streamlit, auth, CI/CD).
