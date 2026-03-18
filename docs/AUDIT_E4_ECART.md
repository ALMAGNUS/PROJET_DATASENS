# 🔍 Audit E4 — Écarts et plan d’action (anticipation)

**Date**: 2026-02-12  
**Projet**: DataSens

---

## A6. Concevoir une application intégrant un service IA

### C14. Analyser le besoin d’application

| Critère | Statut | Preuve existante | Écart / action |
|---------|--------|------------------|----------------|
| Modélisation des données (Merise, entités-relations) | ✅ TRUE | `docs/EXPLICATION_RELATIONS_MERISE.md`, `docs/ER_DIAGRAM_*.md`, `docs/ARCHITECTURE_DB.md` | Conforme |
| Modélisation des parcours utilisateurs (schéma fonctionnel, wireframes) | ❌ FALSE | Pas de doc parcours / wireframes / UX flow | **À créer** : `docs/PARCOURS_UTILISATEUR.md` ou wireframes (flux login → dashboard → prédiction, etc.) |
| Spécifications fonctionnelles (contexte, scénarios, critères validation) | ⚠️ PARTIEL | `docs/AGILE_ROADMAP.md` : user stories avec critères de succès | Manque souvent le **contexte** explicite et le formalisme "spécification fonctionnelle" standard |
| Objectifs accessibilité dans critères d’acceptation des user stories | ❌ FALSE | Aucune mention WCAG/RG2AA/accessibilité | **À ajouter** : critères d’accessibilité dans au moins quelques US prioritaires |
| Objectifs accessibilité basés sur WCAG, RG2AA, etc. | ❌ FALSE | Aucune référence | **À créer** : section accessibilité dans doc projet (ex. objectifs WCAG 2.1 niveau AA pour cockpit Streamlit) |

---

### C15. Concevoir le cadre technique

| Critère | Statut | Preuve existante | Écart / action |
|---------|--------|------------------|----------------|
| Spécifications techniques (architecture, dépendances, environnement) | ✅ TRUE | `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DB.md`, `docs/README_E2_API.md`, `requirements.txt` | Conforme |
| Services éco-responsables favorisés | ❌ FALSE | Pas de mention éco-responsabilité dans les choix | **À ajouter** : court paragraphe dans `docs/ARCHITECTURE.md` ou `README.md` (ex. hébergement, choix tech, Mistral/Local HF) |
| Diagramme de flux de données | ✅ TRUE | `docs/DATA_FLOW.md`, `FLOW_DONNEES.md`, `docs/CHEMIN_DONNEE.md` | Conforme |
| POC accessible et fonctionnelle en pré-production | ⚠️ PARTIEL | Docker, CI/CD, API/cockpit déployables | Manque une doc explicite type "POC en pré-production : URL, conditions" |
| Conclusion POC avec avis pour décision | ❌ FALSE | Pas de doc "conclusion POC" | **À créer** : `docs/CONCLUSION_POC.md` (avis, recommandations, décision de poursuite) |

---

## A7. Développer les interfaces et fonctionnalités

### C16. Coordonner la réalisation technique

| Critère | Statut | Preuve existante | Écart / action |
|---------|--------|------------------|----------------|
| POC accessible en pré-production | ⚠️ PARTIEL | Voir C15 | Idem |
| Outils de pilotage (kanban, burndown, backlog) | ⚠️ PARTIEL | `docs/GITHUB_PROJECTS_SETUP.md` (Kanban), `docs/AGILE_ROADMAP.md` (backlog US) | Pas de burndown ; Kanban GitHub Projects à activer/utiliser |
| Objectifs et modalités des rituels partagés | ❌ FALSE | Pas de doc rituels (daily, sprint review, etc.) | **À créer** : courte section dans doc Agile (rituels, fréquence, participants) |
| Éléments de pilotage accessibles à toutes les parties | ⚠️ PARTIEL | Docs en dépôt Git | Manque une page "Pilotage" centralisée (liens kanban, roadmap, rituels) |

---

### C17. Développer les composants techniques et interfaces

| Critère | Statut | Preuve existante | Écart / action |
|---------|--------|------------------|----------------|
| Environnement de dev conforme aux specs | ✅ TRUE | `requirements.txt`, `README.md`, `setup_with_sql.py`, `.env.example` | Conforme |
| Interfaces intégrées et respectent les maquettes | ⚠️ PARTIEL | Streamlit cockpit fonctionnel | Pas de maquettes formelles à respecter → **documenter** ou créer maquettes de référence |
| Comportements et navigation conformes aux specs | ✅ TRUE | Streamlit + API cohérents avec AGILE_ROADMAP | Conforme |
| Composants métier développés et fonctionnels | ✅ TRUE | Pipeline E1, API E2, Mistral, ML inference | Conforme |
| Gestion des droits d’accès | ✅ TRUE | RBAC, JWT, `create_test_user.py`, table `profils` | Conforme |
| Flux de données intégrés | ✅ TRUE | E1→E2→E3, Parquet, GoldAI | Conforme |
| Éco-conception (éco-index, Green IT) | ❌ FALSE | Pas de référence | **À ajouter** : section dans doc (ex. optimisations CPU, batch size, réduction requêtes) |
| OWASP Top 10 | ✅ TRUE | Section OWASP dans `docs/README_E2_API.md` | Conforme |
| Tests unitaires/intégration (composants métier, accès) | ✅ TRUE | `tests/test_e1_isolation.py`, `tests/test_e2_api.py`, pytest | Conforme |
| Sources versionnées (Git distant) | ✅ TRUE | GitHub, dépôt distant | Conforme |
| Documentation technique (installation, architecture, tests) | ✅ TRUE | README, ARCHITECTURE, BUILD_AND_DEPLOY, README_E2_API | Conforme |
| Documentation format accessible (Valentin Haüy, Microsoft) | ❌ FALSE | Markdown uniquement | **À vérifier** : recommandations (structure titres, alt images, contraste) → exporter en PDF accessible si exigé |

---

## A8. Développer les fonctions de tests et de contrôle

### C18. Automatiser les phases de tests

| Critère | Statut | Preuve existante | Écart / action |
|---------|--------|------------------|----------------|
| Documentation chaîne CI (outils, étapes, tâches, déclencheurs) | ⚠️ PARTIEL | `docs/BUILD_AND_DEPLOY.md`, `docs/PHASE_1_DOCKER_CI_CD_COMPLETE.md` | Manque une doc dédiée type `docs/CI_CHAINE_TESTS.md` (détail étapes, déclencheurs) |
| Outil CI sélectionné | ✅ TRUE | GitHub Actions (`.github/workflows/test.yml`, `ci-cd.yml`) | Conforme |
| Chaîne intègre build, config, étapes préalables | ✅ TRUE | install deps, ruff, pytest | Conforme |
| Chaîne exécute les tests au déclenchement | ✅ TRUE | `pytest tests/` | Conforme |
| Config versionnée avec sources | ✅ TRUE | workflows dans dépôt Git | Conforme |
| Documentation chaîne CI (installation, config, test) | ⚠️ PARTIEL | BUILD_AND_DEPLOY, PHASE_1 | Centraliser dans `docs/CI_CHAINE_TESTS.md` |
| Documentation format accessible | ❌ FALSE | Idem C17 | Idem |

---

### C19. Créer un processus de livraison continue

| Critère | Statut | Preuve existante | Écart / action |
|---------|--------|------------------|----------------|
| Documentation chaîne livraison (étapes, tâches, déclencheurs) | ⚠️ PARTIEL | ci-cd.yml : build Docker, deploy | Manque doc dédiée `docs/CD_CHAINE_LIVRAISON.md` |
| Fichiers de config reconnus et exécutés | ✅ TRUE | GitHub Actions exécute les workflows | Conforme |
| Packaging intégré (build, containers) | ✅ TRUE | Docker build dans ci-cd.yml | Conforme |
| Livraison (PR, deploy) après packaging | ⚠️ PARTIEL | Deploy sur main (placeholder) | Déploy réel optionnel ; PR déclenche build → ok |
| Sources chaîne versionnées | ✅ TRUE | `.github/workflows/` dans dépôt | Conforme |
| Documentation chaîne livraison | ⚠️ PARTIEL | BUILD_AND_DEPLOY | Créer `docs/CD_CHAINE_LIVRAISON.md` |
| Documentation format accessible | ❌ FALSE | Idem | Idem |

---

## Synthèse des écarts E4

| Catégorie | Manquants à créer/modifier |
|-----------|---------------------------|
| **C14** | Parcours utilisateur / wireframes ; critères accessibilité dans US ; objectifs WCAG/RG2AA |
| **C15** | Paragraphe éco-responsable ; doc POC pré-production ; conclusion POC |
| **C16** | Doc rituels Agile ; page centralisée pilotage |
| **C17** | Maquettes ou doc de référence ; section éco-conception ; doc format accessible |
| **C18** | `docs/CI_CHAINE_TESTS.md` complet ; doc format accessible |
| **C19** | `docs/CD_CHAINE_LIVRAISON.md` ; doc format accessible |

---

## Plan d’action prioritaire

1. **`docs/PARCOURS_UTILISATEUR.md`** : schéma fonctionnel / wireframes (flux login → dashboard → prédiction IA).
2. **`docs/OBJECTIFS_ACCESSIBILITE.md`** : objectifs WCAG 2.1 niveau AA, critères à intégrer dans les US.
3. **`docs/CONCLUSION_POC.md`** : avis, recommandations, décision de poursuite du projet.
4. **`docs/CI_CHAINE_TESTS.md`** : description détaillée de la chaîne CI (étapes, déclencheurs, outils).
5. **`docs/CD_CHAINE_LIVRAISON.md`** : description de la chaîne CD (build, packaging, livraison).
6. Sections courtes dans docs existants : éco-responsable (ARCHITECTURE), éco-conception (README ou doc dédiée), rituels (AGILE).
7. **Documentation accessible** : appliquer recommandations (titres, structure, PDF si besoin) ; à clarifier selon exigence du référentiel.
