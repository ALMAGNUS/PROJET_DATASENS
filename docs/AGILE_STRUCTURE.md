# 🎯 Structure Agile - DataSens E1

## 👥 PERSONAS

### Persona 1: **Décideur Politique** 🏛️
- **Besoin** : Comprendre les sentiments français en temps réel
- **Valeur** : Prendre des décisions politiques éclairées
- **Actions** : Consulter dashboards, comparer sources, exporter rapports
- **Outils** : Dashboard, Rapports, Exports CSV

### Persona 2: **Investisseur Financier** 💰
- **Besoin** : Intelligence stratégique sur le sentiment du marché
- **Valeur** : Identifier tendances avant la concurrence
- **Actions** : API real-time, alertes, tracking tendances
- **Outils** : API, Métriques, Alertes

### Persona 3: **Chercheur/Analyste** 📊
- **Besoin** : Accès aux données brutes et traitées
- **Valeur** : Conduire analyses approfondies
- **Actions** : Télécharger datasets, interroger DB, reproduire analyses
- **Outils** : SQL, Python, Exports CSV/Parquet, ZZDB (données synthétiques)

---

## 📦 EPICS

### **EPIC 1 : Collecte Omnicanale** 📡
**Valeur métier** : Aggréger 10 sources hétérogènes en 1 dataset unifié

**User Stories** :
- **US-1.1** : En tant que **Décideur politique/Journaliste**, je veux recevoir automatiquement tous les articles presse du jour, afin de rester informé sans passer 2h à chercher manuellement
- **US-1.2** : En tant que **Analyste politique/Investisseur**, je veux corréler sentiment français + événements majeurs (élections, crises), afin de comprendre POURQUOI le sentiment change
- **US-1.3** : En tant que **Économiste/Think Tank**, je veux croiser sentiment + données officielles INSEE, afin de valider mes hypothèses avec source de vérité gouvernement
- **US-1.4** : En tant que **Chercheur/Analyste**, je veux accéder à des datasets statiques (Kaggle), afin d'enrichir mes analyses avec données historiques
- **US-1.5** : En tant que **Chercheur/Analyste**, je veux utiliser des données synthétiques académiques (ZZDB), afin de tester mes modèles sans données réelles

**Définition de Fait** :
- ✅ Pipeline fonctionnel end-to-end
- ✅ 6 tables E1 (source, raw_data, sync_log, topic, document_topic, model_output)
- ✅ Support multi-sources (RSS, API, Scraping, CSV, SQLite)
- ✅ Déduplication par fingerprint
- ✅ ~5000 articles/jour (objectif)

---

### **EPIC 2 : Qualité & Nettoyage** ✨
**Valeur métier** : Assurer fiabilité des données pour IA

**User Stories** :
- **US-2.1** : En tant que **Chercheur/Analyste**, je veux que chaque article ait un score de qualité (0-1), afin de filtrer les données fiables pour mes analyses
- **US-2.2** : En tant que **Chercheur/Analyste**, je veux que les doublons soient automatiquement supprimés, afin d'éviter les biais dans mes analyses
- **US-2.3** : En tant que **Chercheur/Analyste**, je veux que tous les formats soient normalisés, afin de pouvoir analyser uniformément toutes les sources
- **US-2.4** : En tant que **Décideur politique**, je veux être alerté des anomalies dans les données, afin de prendre des décisions basées sur des données fiables

**Définition de Fait** :
- ✅ Quality score calculé (0.3 pour ZZDB, 0.5 pour autres)
- ✅ Déduplication fonctionnelle
- ✅ Formats normalisés
- ✅ Dataset clean, qualité ≥ 0.5

---

### **EPIC 3 : Intelligence de Sentiment** 🧠
**Valeur métier** : Transformer texte brut en insights actionnables

**User Stories** :
- **US-3.1** : En tant que **Décideur politique**, je veux voir le sentiment (positif/négatif/neutre) de chaque article, afin de comprendre l'état d'esprit des français
- **US-3.2** : En tant que **Investisseur financier**, je veux que les articles soient taggés par topic (politique, économie, etc.), afin d'identifier rapidement les tendances par domaine
- **US-3.3** : En tant que **Chercheur/Analyste**, je veux connaître le score de confiance de chaque analyse, afin d'évaluer la fiabilité de mes conclusions
- **US-3.4** : En tant que **Chercheur/Analyste**, je veux pouvoir enrichir rétroactivement les articles existants, afin d'avoir un dataset complet même pour les anciennes données

**Définition de Fait** :
- ✅ 100% des articles enrichis (sentiment + topics)
- ✅ 18 topics fonctionnels
- ✅ Sentiment négatif détecté correctement (61 articles)
- ✅ Scores de confiance calculés

---

### **EPIC 4 : Dashboards & Visualisation** 📈
**Valeur métier** : Voir patterns au coup d'œil

**User Stories** :
- **US-4.1** : En tant que **Décideur politique**, je veux voir un dashboard synthétique avec les KPIs principaux, afin de prendre des décisions rapidement
- **US-4.2** : En tant que **Investisseur financier**, je veux voir des graphiques par source, afin de comparer la fiabilité des différentes sources
- **US-4.3** : En tant que **Décideur politique**, je veux voir une timeline du sentiment, afin de comprendre l'évolution dans le temps
- **US-4.4** : En tant que **Chercheur/Analyste**, je veux voir des rapports détaillés de chaque session de collecte, afin de comprendre d'où viennent les données

**Définition de Fait** :
- ✅ Dashboard d'enrichissement global
- ✅ Rapports terminal complets
- ✅ Distribution sentiment visible
- ✅ Décisions 10x plus rapides

---

### **EPIC 5 : Exports et Partitionnement**
**Valeur métier** : Fournir les données dans des formats exploitables

**User Stories** :
- **US-5.1** : En tant que **Chercheur/Analyste**, je veux exporter les données en CSV (RAW, SILVER, GOLD), afin de les analyser dans Excel/Python
- **US-5.2** : En tant que **Chercheur/Analyste**, je veux exporter en Parquet partitionné par date, afin d'optimiser mes requêtes par période
- **US-5.3** : En tant que **Chercheur/Analyste**, je veux que les données soient partitionnées par source, afin d'isoler facilement les données synthétiques (ZZDB)
- **US-5.4** : En tant que **Chercheur/Analyste**, je veux exporter spécifiquement les données ZZDB, afin de les utiliser séparément dans mes tests académiques

**Définition de Fait** :
- ✅ Exports CSV fonctionnels
- ✅ Partitionnement par date : `data/gold/date=YYYY-MM-DD/`
- ✅ Partitionnement par source : `data/gold/date=YYYY-MM-DD/source=zzdb_*/`
- ✅ Export CSV global ZZDB : `exports/gold_zzdb.csv`

---

### **EPIC 6 : Monitoring & Observabilité** 🔍
**Valeur métier** : Garantir uptime 99.9% + trust

**User Stories** :
- **US-6.1** : En tant que **Investisseur financier**, je veux voir les métriques en temps réel (articles, erreurs, durée), afin de m'assurer que le système fonctionne correctement
- **US-6.2** : En tant que **Décideur politique**, je veux accéder à un dashboard Grafana pré-configuré, afin de visualiser les tendances sans configuration technique
- **US-6.3** : En tant que **Décideur politique**, je veux être alerté en cas d'erreur d'ingestion, afin de garantir la continuité de l'information
- **US-6.4** : En tant que **Investisseur financier**, je veux que le système vérifie automatiquement la santé (DB, APIs), afin d'avoir confiance dans la disponibilité des données

**Définition de Fait** :
- ✅ Serveur Prometheus sur port 8000
- ✅ Dashboard Grafana fonctionnel
- ✅ Health checks Docker
- ✅ Transparence totale

---

### **EPIC 7 : Containerisation (Docker)**
**Valeur métier** : Déploiement reproductible et scalable

**User Stories** :
- **US-7.1** : En tant que **Investisseur financier**, je veux que le système soit déployable via Docker, afin de garantir la reproductibilité et la scalabilité
- **US-7.2** : En tant que **Investisseur financier**, je veux que tous les services (Pipeline + Prometheus + Grafana) soient orchestrés ensemble, afin de simplifier le déploiement
- **US-7.3** : En tant que **Décideur politique**, je veux que le système vérifie automatiquement sa santé, afin d'être alerté en cas de problème
- **US-7.4** : En tant que **Chercheur/Analyste**, je veux une documentation Docker complète, afin de pouvoir déployer le système facilement

**Définition de Fait** :
- ✅ Image Docker buildable
- ✅ docker-compose.yml fonctionnel
- ✅ 3 services (Pipeline, Prometheus, Grafana)
- ✅ README_DOCKER.md complet

---

### **EPIC 8 : Données Synthétiques (ZZDB)**
**Valeur métier** : Enrichir le dataset avec des données de test académiques

**User Stories** :
- **US-8.1** : En tant que **Chercheur/Analyste**, je veux générer des données synthétiques avec Faker, afin de tester mes modèles sans données réelles
- **US-8.2** : En tant que **Chercheur/Analyste**, je veux une base SQLite ZZDB isolée, afin de séparer clairement les données synthétiques des données réelles
- **US-8.3** : En tant que **Chercheur/Analyste**, je veux exporter les données ZZDB en CSV, afin de les intégrer facilement dans le pipeline
- **US-8.4** : En tant que **Chercheur/Analyste**, je veux que les données ZZDB soient intégrées comme source statique (fondation), afin qu'elles soient disponibles une fois pour toutes
- **US-8.5** : En tant que **Chercheur/Analyste**, je veux que les données ZZDB soient partitionnées séparément, afin de les isoler facilement dans mes analyses

**Définition de Fait** :
- ✅ Base `zzdb/synthetic_data.db` fonctionnelle
- ✅ Export CSV `zzdb/zzdb_dataset.csv`
- ✅ Intégration dans pipeline E1
- ✅ Partitionnement par source ZZDB
- ✅ 95 articles ZZDB dans datasens.db

---

## 📋 BACKLOG (Priorisé)

### **Sprint 0 (Fondations) - ✅ COMPLÉTÉ**
- [x] US-1.1 : Surveiller actualité presse (RSS)
- [x] US-1.2 : Contextualiser avec événements (GDELT)
- [x] US-1.3 : Valider avec données officielles (INSEE)
- [x] US-1.4 : Intégrer datasets statiques (Kaggle)
- [x] US-1.5 : Intégrer données synthétiques (ZZDB)

### **Sprint 1 (Qualité) - ✅ COMPLÉTÉ**
- [x] US-2.1 : Scorer qualité (0-1)
- [x] US-2.2 : Dédupliquer (fingerprint)
- [x] US-2.3 : Normaliser formats
- [x] US-2.4 : Détecter anomalies

### **Sprint 2 (Enrichissement) - ✅ COMPLÉTÉ**
- [x] US-3.1 : Analyse sentiment (positif/négatif/neutre)
- [x] US-3.2 : Détecter topics (18 topics)
- [x] US-3.3 : Scores de confiance
- [x] US-3.4 : Enrichissement rétroactif

### **Sprint 3 (Dashboards) - ✅ COMPLÉTÉ**
- [x] US-4.1 : Dashboard synthétique (KPIs)
- [x] US-4.2 : Graphiques par source
- [x] US-4.3 : Timeline sentiment
- [x] US-4.4 : Rapports de collecte

### **Sprint 4 (Exports) - ✅ COMPLÉTÉ**
- [x] US-5.1 : Exports CSV (RAW/SILVER/GOLD)
- [x] US-5.2 : Exports Parquet par date
- [x] US-5.3 : Partitionnement par source
- [x] US-5.4 : Export spécifique ZZDB

### **Sprint 5 (Monitoring) - ✅ COMPLÉTÉ**
- [x] US-6.1 : Métriques Prometheus
- [x] US-6.2 : Dashboard Grafana
- [x] US-6.3 : Alertes ingestion
- [x] US-6.4 : Health checks

### **Sprint 6 (Docker) - ✅ COMPLÉTÉ**
- [x] US-7.1 : Dockerfile production
- [x] US-7.2 : Docker Compose
- [x] US-7.3 : Health checks
- [x] US-7.4 : Documentation Docker

### **Sprint 7 (ZZDB) - ✅ COMPLÉTÉ**
- [x] US-8.1 : Génération données synthétiques
- [x] US-8.2 : Base SQLite ZZDB
- [x] US-8.3 : Export CSV
- [x] US-8.4 : Intégration pipeline
- [x] US-8.5 : Partitionnement ZZDB

---

## 🏃 SPRINTS / RUNS

### **Sprint 0 : Collecte Omnicanale (Semaine 1)**
**Objectif** : Aggréger 10 sources hétérogènes
- ✅ RSS feeds (presse)
- ✅ APIs (GDELT, INSEE, OpenWeather)
- ✅ Web scraping (sondages, avis)
- ✅ Datasets CSV/Parquet
- ✅ Données synthétiques (ZZDB)

**Vélocité** : 5 US complétées

---

### **Sprint 1 : Qualité & Nettoyage (Semaine 2)**
**Objectif** : Assurer fiabilité des données
- ✅ Scorer qualité (0-1)
- ✅ Dédupliquer (fingerprinting)
- ✅ Normaliser formats
- ✅ Détecter anomalies

**Vélocité** : 4 US complétées

---

### **Sprint 2 : Intelligence de Sentiment (Semaine 3)**
**Objectif** : Transformer texte en insights
- ✅ Sentiment analysis (100+ mots-clés)
- ✅ Topic tagging (18 topics)
- ✅ Scores de confiance

**Vélocité** : 4 US complétées

---

### **Sprint 3 : Dashboards & Visualisation (Semaine 4)**
**Objectif** : Voir patterns au coup d'œil
- ✅ Dashboard synthétique (KPIs)
- ✅ Graphiques par source
- ✅ Timeline sentiment
- ✅ Rapports de collecte

**Vélocité** : 4 US complétées

---

### **Sprint 4 : Exports (Semaine 5)**
**Objectif** : Formats exploitables
- ✅ Exports CSV/Parquet
- ✅ Partitionnement date/source
- ✅ Isolation ZZDB

**Vélocité** : 4 US complétées

---

### **Sprint 5 : Monitoring (Semaine 6)**
**Objectif** : Garantir uptime 99.9%
- ✅ Prometheus metrics
- ✅ Grafana dashboard
- ✅ Alertes ingestion
- ✅ Health checks

**Vélocité** : 4 US complétées

---

### **Sprint 6 : Docker (Semaine 7)**
**Objectif** : Containerisation
- ✅ Dockerfile
- ✅ docker-compose.yml
- ✅ Documentation

**Vélocité** : 4 US complétées

---

### **Sprint 7 : ZZDB (Semaine 8)**
**Objectif** : Données synthétiques académiques
- ✅ Génération Faker
- ✅ Intégration pipeline
- ✅ Partitionnement

**Vélocité** : 5 US complétées

---

## 📊 MÉTRIQUES SPRINT

### **Vélocité Totale**
- **Total US complétées** : 34
- **Sprints complétés** : 8
- **Vélocité moyenne** : 4.25 US/sprint

### **État Actuel**
- **Version** : v1.0.0-stable (FREEZE)
- **Articles** : 2,704
- **Enrichissement** : 100%
- **Topics** : 18
- **Sentiments** : Positif (157), Négatif (61), Neutre (2,486)
- **ZZDB** : 95 articles

---

## 🛠️ OUTILS RECOMMANDÉS

### **GitHub Projects** (Recommandé pour solo)
**Avantages** :
- Intégré à GitHub
- Automatisation via Issues/PR
- Gratuit
- Vue Kanban + Tableau

**Setup** :
1. Créer un Project : `Settings > Projects > New Project`
2. Template : "Board" (Kanban)
3. Connecter Issues aux User Stories
4. Colonnes : Backlog → To Do → In Progress → Done

---

### **Taïga** (Recommandé pour backlog détaillé)
**Avantages** :
- Backlog structuré (Epics → User Stories → Tasks)
- Sprints/Runs planifiés
- Burndown charts
- Gratuit (open source)

**Setup** :
1. Créer projet : `taiga.io`
2. Importer Epics ci-dessus
3. Créer User Stories
4. Planifier Sprints

---

### **Miro** (Pour brainstorming)
**Avantages** :
- Post-it visuels
- Mapping Epics/User Stories
- Collaboration
- Gratuit (limité)

**Usage** :
- Créer board "DataSens E1"
- Colonnes : Epics → User Stories → Backlog
- Post-it colorés par Epic

---

### **Trello** (Pour Kanban simple)
**Avantages** :
- Simple et visuel
- Power-ups (GitHub, etc.)
- Gratuit

**Setup** :
1. Créer board "DataSens E1"
2. Colonnes : Backlog | To Do | In Progress | Review | Done
3. Cartes = User Stories
4. Labels = Epics

---

## 🎯 RECOMMANDATION POUR SOLO

### **Stack Recommandée** :
1. **GitHub Projects** (principal)
   - Issues = User Stories
   - Projects = Kanban
   - Milestones = Sprints

2. **Miro** (planning visuel)
   - Mapping Epics
   - Brainstorming

3. **Taïga** (optionnel, si besoin de backlog détaillé)

### **Workflow** :
1. **Planning** : Miro (Epics/User Stories)
2. **Tracking** : GitHub Projects (Kanban)
3. **Exécution** : Code + Commits
4. **Review** : GitHub Issues/PR

---

## 📝 TEMPLATE USER STORY

```
**US-XX.X : [Titre]**

**En tant que** [Persona]
**Je veux** [Action]
**Afin de** [Bénéfice]

**Critères d'acceptation** :
- [ ] Critère 1
- [ ] Critère 2
- [ ] Critère 3

**Définition de Fait** :
- [ ] Code review
- [ ] Tests passent
- [ ] Documentation à jour
- [ ] Déployé en production

**Estimation** : [X] points (Fibonacci)
**Epic** : [EPIC X]
**Sprint** : [Sprint X]
```

---

## 🚀 PROCHAINES USER STORIES (Backlog Future)

### **EPIC 9 : API & Intégration** 🔌
- **US-9.1** : En tant que **Investisseur financier**, je veux accéder aux données via REST API, afin d'intégrer DataSens dans mes systèmes existants
- **US-9.2** : En tant que **Investisseur financier**, je veux recevoir des webhooks en temps réel, afin d'être alerté immédiatement des changements de sentiment
- **US-9.3** : En tant que **Chercheur/Analyste**, je veux interroger les données via GraphQL, afin d'avoir des requêtes flexibles et optimisées
- **US-9.4** : En tant que **Chercheur/Analyste**, je veux un Python SDK, afin d'intégrer facilement DataSens dans mes scripts Python

### **EPIC 10 : Fine-tuning IA** 🤖
- **US-10.1** : En tant que **Chercheur/Analyste**, je veux entraîner des modèles FlauBERT/CamemBERT, afin d'améliorer la précision de l'analyse de sentiment
- **US-10.2** : En tant que **Chercheur/Analyste**, je veux évaluer les modèles (F1/Precision/Recall), afin de mesurer leur performance
- **US-10.3** : En tant que **Chercheur/Analyste**, je veux versionner les modèles (MLflow), afin de pouvoir comparer différentes versions
- **US-10.4** : En tant que **Décideur politique**, je veux que les modèles soient testés en A/B, afin de garantir la meilleure qualité d'analyse

### **EPIC 11 : Gouvernance & Conformité** ⚖️
- **US-11.1** : En tant que **Décideur politique**, je veux que les données soient anonymisées, afin de respecter le RGPD
- **US-11.2** : En tant que **Décideur politique**, je veux des politiques de rétention des données, afin de gérer le cycle de vie des données
- **US-11.3** : En tant que **Décideur politique**, je veux un contrôle d'accès par rôles, afin de sécuriser l'accès aux données sensibles
- **US-11.4** : En tant que **Décideur politique**, je veux des rapports de conformité, afin de démontrer la conformité RGPD

---

## ✅ CHECKLIST SPRINT

### **Avant le Sprint**
- [ ] Backlog priorisé
- [ ] User Stories estimées
- [ ] Sprint goal défini
- [ ] Capacité déterminée

### **Pendant le Sprint**
- [ ] Daily standup (même solo, noter blocages)
- [ ] Code commits réguliers
- [ ] Tests au fur et à mesure

### **Fin de Sprint**
- [ ] Review (démo fonctionnelle)
- [ ] Retrospective (ce qui a bien marché, améliorations)
- [ ] Mise à jour backlog
- [ ] Tag release si stable

---

## 📈 BURNDOWN CHART (Exemple)

```
Sprint 1 (Enrichissement)
Points restants
26 |████████████████████████████
24 |████████████████████████
22 |████████████████████
20 |████████████████
18 |████████████
16 |████████
14 |████
12 |
10 |
 8 |
 6 |
 4 |
 2 |
 0 |_____________________________
   J1 J2 J3 J4 J5 J6 J7 J8 J9 J10
```

---

## 🎯 SPRINT GOAL (Exemple)

**Sprint 0** : "Collecte omnicanale opérationnelle"
**Sprint 1** : "Qualité et fiabilité des données"
**Sprint 2** : "Intelligence de sentiment fonctionnelle"
**Sprint 3** : "Dashboards pour décisions rapides"
**Sprint 4** : "Exports exploitables pour analyse"
**Sprint 5** : "Monitoring et observabilité"
**Sprint 6** : "Déploiement containerisé"
**Sprint 7** : "Données synthétiques académiques intégrées"

---

## 📚 RESSOURCES

- **Scrum Guide** : https://scrumguides.org/
- **GitHub Projects** : https://docs.github.com/en/issues/planning-and-tracking-work-with-project-boards
- **Taïga** : https://taiga.io/
- **Miro** : https://miro.com/
- **Trello** : https://trello.com/
