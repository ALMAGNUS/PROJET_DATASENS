# 🔍 Audit E3 — Grille de compétences (A3 : Services IA)

**Date**: 2026-02-12  
**Projet**: DataSens  
**Contexte E3** : Cockpit Streamlit + intégration Mistral/CamemBERT + analytics PySpark

---

## A3. Accompagner le choix et l'intégration d'un service d'intelligence artificielle préexistant

*Les critères A3 C6, C7, C8 sont partagés avec E2. E3 apporte l'interface utilisateur (Streamlit) et l'intégration opérationnelle des services IA.*

---

### C6. Veille technique et réglementaire

| Critère | Statut | Justification (angle E3) |
|---------|--------|---------------------------|
| Définition de la ou des thématiques de veille | ✅ TRUE | Thématiques IA + réglementaire (veille_sources.json) ; cockpit E3 expose le bouton « Veille IA » |
| Planification des temps dédiés à la veille | ✅ TRUE | `docs/VEILLE_PLANIFICATION.md` |
| Choix d'un outil d'agrégation des flux | ✅ TRUE | feedparser + `veille_digest.py` ; lancement depuis le cockpit E3 (onglet Pilotage) |
| Choix d'un outil de partage des synthèses | ✅ TRUE | Markdown → `docs/veille/` ; Streamlit permet de lancer la génération et consulter les synthèses |
| Identification des sources et flux | ✅ TRUE | `scripts/veille_sources.json` (5 sources, url, catégorie) |
| Qualification de la fiabilité des sources | ✅ TRUE | Champ `reliability` dans veille_sources.json |
| Configuration des outils selon flux/thématiques | ✅ TRUE | veille_digest.py configuré via veille_sources.json |
| Rédaction des synthèses | ✅ TRUE | `build_digest()` → `docs/veille/veille_YYYY-MM-DD.md` |
| Communication des synthèses aux parties prenantes | ✅ TRUE | Fichiers partagés via dépôt ; accès via cockpit E3 (Pilotage → Veille IA) |

---

### C7. Identification des services IA préexistants

| Critère | Statut | Justification (angle E3) |
|---------|--------|---------------------------|
| Définition de la problématique IA | ✅ TRUE | AI_REQUIREMENTS.md : « Classer et enrichir les textes (sentiment/topics) en local » |
| Identification des contraintes | ✅ TRUE | Données sensibles, coût, compatibilité CPU |
| Benchmark des outils/services IA | ✅ TRUE | AI_BENCHMARK.md ; bouton « Benchmark IA » dans cockpit E3 (Pilotage) |
| Rédaction des conclusions et recommandations | ✅ TRUE | Recommandation CamemBERT/FlauBERT + Mistral ; implémentation dans E3 (Streamlit + API) |

---

### C8. Paramétrage du service IA

| Critère | Statut | Justification (angle E3) |
|---------|--------|---------------------------|
| Création de l'environnement d'exécution | ✅ TRUE | Mistral SaaS (MISTRAL_API_KEY) ; env local Python (.venv) ; Streamlit sur port 8501 |
| Installation et configuration des dépendances | ✅ TRUE | requirements.txt (mistralai, transformers, torch) ; config dans `src/config.py` ; CamemBERT/FlauBERT pour sentiment |
| Création des accès (comptes, groupes, droits) | ✅ TRUE | create_test_user.py ; authentification JWT via API ; cockpit E3 consomme l'API avec token |
| Installation et configuration du monitorage | ✅ TRUE | Prometheus `/metrics` ; Grafana ; dashboard datasens-full.json ; drift-metrics |
| Rédaction de la documentation | ✅ TRUE | MISTRAL_IA_INSIGHTS.md ; DASHBOARD_GUIDE.md ; README_E2_API.md ; .env.example |

---

## Synthèse E3

| Compétence | Critères OK | Partiel | KO |
|------------|-------------|---------|-----|
| A3 C6 | 9 | 0 | 0 |
| A3 C7 | 4 | 0 | 0 |
| A3 C8 | 5 | 0 | 0 |

### Statut : ✅ 100 % conforme

---

## Artefacts E3 spécifiques

| Critère | Composants E3 |
|---------|---------------|
| C6 | `src/streamlit/app.py` (boutons Veille IA, Benchmark IA) ; `scripts/veille_digest.py` ; `docs/veille/` ; `docs/VEILLE_PLANIFICATION.md` |
| C7 | `scripts/ai_benchmark.py` ; `docs/e2/AI_BENCHMARK.md`, `AI_REQUIREMENTS.md` ; bouton Benchmark IA dans Streamlit |
| C8 | `src/e3/mistral/service.py` ; `src/ml/inference/sentiment.py` ; `src/streamlit/app.py` (prédiction sentiment, assistant Mistral) ; monitoring (Prometheus, Grafana) ; `docs/MISTRAL_IA_INSIGHTS.md`, `docs/DASHBOARD_GUIDE.md` |
