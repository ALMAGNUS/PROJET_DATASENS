# 📚 INDEX DOCUMENTATION

## 🗂️ Structure des docs/

```
docs/
├── README.md (INDEX - ce fichier)
├── ARCHITECTURE.md (Guide complet architecture + code)
├── PROJECT_STRUCTURE.md (Structure dossiers/fichiers)
├── (CHANGELOG.md à la racine du projet)
├── CONTRIBUTING.md (Guide contributeurs)
├── LOGGING.md (Configuration logging)
├── SCHEMA_DESIGN.md (Design base données)
├── AGILE_ROADMAP.md (Roadmap produit)
├── AUDIT_E1_COMPETENCES.md … AUDIT_E5_COMPETENCES.md (Grilles E1–E5)
├── AUDIT_E4_ECART.md (Écarts E4 + plan d'action)
├── REGISTRE_TRAITEMENTS_RGPD.md (Art. 30 RGPD)
├── PROCEDURE_TRI_DONNEES_PERSONNELLES.md (Tri/suppression DP)
├── METRIQUES_SEUILS_ALERTES.md (Monitoring)
├── PROCEDURE_INCIDENTS.md (Gestion incidents)
├── MONITORING_E2_API.md (Prometheus, Grafana)
├── ACCESSIBILITE_DOCUMENTATION.md (AVH, Microsoft)
├── VEILLE_PLANIFICATION.md (Planification veille)
└── e2/
    ├── AI_BENCHMARK.md
    └── AI_REQUIREMENTS.md
```

---

## 📖 Guide Lecture

### Pour **Démarrer**
1. Lire [`../README.md`](../README.md ) (racine) → Vue d'ensemble
2. Lire [`ARCHITECTURE.md`](ARCHITECTURE.md ) → Comment ça marche
3. Lancer `python main.py` → Tester

### Pour **Développer**
1. Lire [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md ) → Structure fichiers
2. Lire [`ARCHITECTURE.md`](ARCHITECTURE.md ) → Principes SOLID
3. Lire [`CONTRIBUTING.md`](CONTRIBUTING.md ) → Ajouter features
4. Tester et itérer

### Pour **Maintenir**
1. Consulter [`SCHEMA_DESIGN.md`](SCHEMA_DESIGN.md ) → BD schema
2. Consulter [`LOGGING.md`](LOGGING.md ) → Logs
3. Consulter [`CHANGELOG.md`](../CHANGELOG.md) → Historique
4. Consulter [`METRIQUES_SEUILS_ALERTES.md`](METRIQUES_SEUILS_ALERTES.md ) → Monitoring
5. Consulter [`PROCEDURE_INCIDENTS.md`](PROCEDURE_INCIDENTS.md ) → Incidents

### Pour **Planifier**
1. Consulter [`AGILE_ROADMAP.md`](AGILE_ROADMAP.md ) → Next steps

---

## 📄 Fichiers Détail

### 🔗 [ARCHITECTURE.md](ARCHITECTURE.md) — Le Guide Principal ⭐

**Contient :**
- Structure du projet
- Modules principaux expliqués
- Dépendances décryptées
- Flow de données
- Principes SOLID
- Exemples pratiques

**À lire :** En premier pour comprendre le code

**Sections :**
1. Structure du projet
2. Modules principaux (models, extractors, core)
3. Dépendances (feedparser, requests, beautifulsoup4, sqlite3)
4. Flow de données (ETL complet)
5. Principes SOLID (Single Responsibility, Open/Closed, etc.)
6. Exemples (lancer pipeline, ajouter source)

---

### 📁 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) — Vue d'Ensemble Fichiers

**Contient :**
- Arborescence complète
- Description chaque fichier/dossier
- Contenu fichiers racine (main.py, requirements.txt, pyrightconfig.json, sources_config.json)
- Détail src/ (models.py, extractors.py, core.py)
- Détail data/ (raw, silver, gold)
- Détail notebooks/
- Dépendances décryptées

**À lire :** Pour comprendre organisation dossiers

**Sections :**
1. Vue d'ensemble arborescente
2. Fichiers racine expliqués
3. Code source src/ détaillé
4. Données data/ partitionnement
5. Notebooks Jupyter
6. Dépendances (feedparser, requests, beautifulsoup4, sqlite3)

---

### 📝 [CHANGELOG.md](../CHANGELOG.md) — Historique Versions

**Contient :**
- v2.0.0 (2025-12-16) — Refactoring SOLID/OOP/DRY
  - Architecture refactorisée
  - Structure modulaire
  - Type hints complets
  - Gestion d'erreurs robuste
  - Performances

- v1.0.0 (2025-12-15) — Version initiale

**À lire :** Pour suivre évolution du projet

**Utilité :** Voir différences entre versions, comprendre améliorations

---

### 👥 [CONTRIBUTING.md](CONTRIBUTING.md) — Guide Contributeurs

**Contient :**
- Comment ajouter une nouvelle source
- Normes de code (type hints, docstrings, logging)
- Guide tests

**À lire :** Avant de contribuer

**Processus :**
1. Créer Extractor
2. Enregistrer dans Factory
3. Ajouter config JSON
4. Tester

---

### 🔍 [LOGGING.md](LOGGING.md) — Configuration Logging

**Contient :**
- Setup logging
- Formats log
- Fichiers log
- Troubleshooting

**À lire :** Pour déboguer

---

### 🗄️ [SCHEMA_DESIGN.md](SCHEMA_DESIGN.md) — Base de Données

**Contient :**
- Tables (source, raw_data, sync_log, topic, etc.)
- Relations
- Schéma ER
- Queries utiles

**À lire :** Pour comprendre BD

---

### 🛣️ [AGILE_ROADMAP.md](AGILE_ROADMAP.md) — Roadmap Produit

**Contient :**
- Phase E1 (Extraction) ✅ DONE
- Phase E2 (Topics & Tagging)
- Phase E3 (ML Models)
- Phase E4 (API REST)
- Backlog

**À lire :** Pour connaître prochaines étapes

---

## 📋 Conformité & Audits (E1 → E5)

| Document | Contenu | Statut |
|----------|---------|--------|
| [AUDIT_E1_COMPETENCES.md](AUDIT_E1_COMPETENCES.md) | Grille E1 (collecte, BDD, API, RGPD, OWASP) | ✅ 100 % |
| [AUDIT_E2_COMPETENCES.md](AUDIT_E2_COMPETENCES.md) | Grille E2 (veille, benchmark IA, paramétrage) | ✅ 100 % |
| [AUDIT_E3_COMPETENCES.md](AUDIT_E3_COMPETENCES.md) | Grille E3 (cockpit Streamlit) | ✅ 100 % |
| [AUDIT_E4_ECART.md](AUDIT_E4_ECART.md) | Écarts E4 (conception, développement) | Plan d'action |
| [AUDIT_E5_COMPETENCES.md](AUDIT_E5_COMPETENCES.md) | Grille E5 (monitoring, incidents) | ✅ 100 % |

### RGPD & Sécurité

| Document | Contenu |
|----------|---------|
| [REGISTRE_TRAITEMENTS_RGPD.md](REGISTRE_TRAITEMENTS_RGPD.md) | Registre des traitements (Art. 30 RGPD) |
| [PROCEDURE_TRI_DONNEES_PERSONNELLES.md](PROCEDURE_TRI_DONNEES_PERSONNELLES.md) | Procédure tri/suppression données personnelles |
| [README_E2_API.md](README_E2_API.md) | Section OWASP Top 10 |

### Monitoring & Maintien

| Document | Contenu |
|----------|---------|
| [METRIQUES_SEUILS_ALERTES.md](METRIQUES_SEUILS_ALERTES.md) | Métriques, seuils, alertes |
| [PROCEDURE_INCIDENTS.md](PROCEDURE_INCIDENTS.md) | Résolution incidents techniques |
| [MONITORING_E2_API.md](MONITORING_E2_API.md) | Prometheus, Grafana, choix techniques |
| [ACCESSIBILITE_DOCUMENTATION.md](ACCESSIBILITE_DOCUMENTATION.md) | Accessibilité (AVH, Microsoft) |

### Veille & IA

| Document | Contenu |
|----------|---------|
| [VEILLE_PLANIFICATION.md](VEILLE_PLANIFICATION.md) | Planification temps veille |
| [e2/AI_BENCHMARK.md](e2/AI_BENCHMARK.md) | Benchmark services IA |
| [e2/AI_REQUIREMENTS.md](e2/AI_REQUIREMENTS.md) | Exigences IA |

---

## 🎯 Cas d'Usage

### ❓ Je veux **lancer l'application**
```
1. Lire README.md (racine)
2. python main.py
3. Consulter SCHEMA_DESIGN.md pour BD
```

### ❓ Je veux **ajouter une nouvelle source**
```
1. Lire ARCHITECTURE.md (section Modules Principaux → extractors.py)
2. Lire CONTRIBUTING.md (Ajouter une nouvelle source)
3. Créer classe Extractor
4. Enregistrer Factory
5. Test
```

### ❓ Je veux **comprendre le code**
```
1. Lire ARCHITECTURE.md (tout)
2. Lire PROJECT_STRUCTURE.md
3. Consulter code dans src/
```

### ❓ Je veux **déboguer**
```
1. Lire LOGGING.md
2. Consulter logs
3. Lire SCHEMA_DESIGN.md pour BD
```

### ❓ Je veux **suivre l'évolution**
```
1. Lire CHANGELOG.md (historique)
2. Lire AGILE_ROADMAP.md (future)
```

### ❓ Je veux **vérifier la conformité / auditer**
```
1. Audits E1–E5 : AUDIT_E1_COMPETENCES.md … AUDIT_E5_COMPETENCES.md
2. RGPD : REGISTRE_TRAITEMENTS_RGPD.md, PROCEDURE_TRI_DONNEES_PERSONNELLES.md
3. Monitoring : METRIQUES_SEUILS_ALERTES.md, PROCEDURE_INCIDENTS.md
4. Index complet : section « Conformité & Audits » ci-dessus
```

---

## 🔗 Liens Rapides

| Document | Utilité | Lire Quand |
|----------|---------|-----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Comprendre code | Démarrage |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Voir organisation | Organisation |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribuer | Avant modification |
| [SCHEMA_DESIGN.md](SCHEMA_DESIGN.md) | BD schema | Debug DB |
| [LOGGING.md](LOGGING.md) | Logs | Troubleshooting |
| [CHANGELOG.md](../CHANGELOG.md) | Versions | Suivi projet |
| [AGILE_ROADMAP.md](AGILE_ROADMAP.md) | Future | Planification |
| [AUDIT_E1_COMPETENCES.md](AUDIT_E1_COMPETENCES.md) | Conformité E1 | Audit |
| [AUDIT_E5_COMPETENCES.md](AUDIT_E5_COMPETENCES.md) | Conformité E5 | Audit |
| [METRIQUES_SEUILS_ALERTES.md](METRIQUES_SEUILS_ALERTES.md) | Monitoring | Maintien |
| [PROCEDURE_INCIDENTS.md](PROCEDURE_INCIDENTS.md) | Incidents | Résolution bug |

---

## 📊 Statistics

```
Total lignes code:     ~495
  - models.py:        45
  - extractors.py:    280
  - core.py:          150
  - main.py:          20

Total documentation:  ~2000+ lignes
  - Ce README:        ~200 lignes
  - ARCHITECTURE.md:  ~400 lignes
  - PROJECT_STRUCTURE.md: ~600 lignes
  - Autres docs:      ~800+ lignes

Coverage:
  - Code SOLID:       ✅ 100%
  - Type hints:       ✅ 100%
  - Docstrings:       ✅ 85%
  - Tests:            ❌ 0% (À faire)
```

---

## 🚀 Quick Start

```bash
# 1. Installation
pip install -r ../requirements.txt

# 2. Configuration
# Éditer sources_config.json

# 3. Lancer
cd ..
python main.py

# 4. Voir résultats
# BD: ~/datasens_project/datasens.db
```

---

## 💡 Tips

- **Tous les .md sauf README.md sont dans ce dossier** (docs/)
- **Chaque module a sa responsabilité** (SOLID)
- **Architecture extensible** (Factory pattern)
- **Code < 500 lignes** mais powerful
- **Type hints partout** (type-safe)
- **Logging robuste** (errors, not silent)

---

## 📞 Support

Pour questions :
1. Lire la doc appropriée
2. Consulter SCHEMA_DESIGN.md (BD)
3. Consulter LOGGING.md (Logs)
4. Consulter CONTRIBUTING.md (Code)

---

**Dernière mise à jour :** 2026-02-12
**Version :** 1.5.0 (Documentation E1–E5 complète)
