# 🔍 Audit E2 — Grille de compétences (A3 : Services IA)

**Date**: 2026-02-12  
**Projet**: DataSens

---

## A3. Accompagner le choix et l'intégration d'un service d'intelligence artificielle préexistant

### C6. Veille technique et réglementaire

| Critère | Statut | Justification |
|---------|--------|---------------|
| Définition de la ou des thématiques de veille | ✅ TRUE | `scripts/veille_sources.json` : thème `veille_ia_datasens`, catégories `ia` (OpenAI, Mistral, HF) et `reglementaire` (ANSSI, CNIL) |
| Planification des temps dédiés à la veille | ✅ TRUE | `docs/VEILLE_PLANIFICATION.md` : fréquence hebdomadaire, durée 1 h, activités réparties |
| Choix d'un outil d'agrégation des flux | ✅ TRUE | feedparser + `veille_digest.py` : agrégation RSS multi-sources |
| Choix d'un outil de partage des synthèses | ✅ TRUE | Markdown → `docs/veille/` ; bouton Streamlit lance le script ; synthèses accessibles au projet |
| Identification des sources et flux | ✅ TRUE | veille_sources.json : 5 sources (url, catégorie), accessibilité via RSS |
| Qualification de la fiabilité des sources | ✅ TRUE | Champ `reliability` dans veille_sources.json (ex. `"high"` pour toutes) |
| Configuration des outils selon flux/thématiques | ✅ TRUE | veille_digest.py lit veille_sources.json, fetch_feed() par source, build_digest() par catégorie |
| Rédaction des synthèses | ✅ TRUE | `build_digest()` génère Markdown structuré (titre, liens, date) |
| Communication des synthèses aux parties prenantes | ✅ TRUE | Fichiers `docs/veille/veille_YYYY-MM-DD.md` ; lancement depuis Streamlit |

### C7. Identification des services IA préexistants

| Critère | Statut | Justification |
|---------|--------|---------------|
| Définition de la problématique IA | ✅ TRUE | `scripts/ai_benchmark.py` → `docs/e2/AI_REQUIREMENTS.md` : « Classer et enrichir les textes (sentiment/topics) en local » |
| Identification des contraintes | ✅ TRUE | AI_REQUIREMENTS.md : « Données sensibles, coût maîtrisé, compatibilité CPU » |
| Benchmark des outils/services IA | ✅ TRUE | AI_BENCHMARK.md (généré par ai_benchmark.py) : tableau Local HF vs API Cloud (coût, latence, confidentialité, conformité) |
| Rédaction des conclusions et recommandations | ✅ TRUE | « Recommandation : CamemBERT/FlauBERT en local via transformers » ; implémentation effective dans `src/ml/inference/sentiment.py` + Mistral API (chat/insights) |

### C8. Paramétrage du service IA

| Critère | Statut | Justification |
|---------|--------|---------------|
| Création de l'environnement d'exécution | ✅ TRUE | Compte SaaS Mistral (MISTRAL_API_KEY) ; environnement local Python (.venv, requirements.txt) ; config dans `src/config.py` |
| Installation et configuration des dépendances | ✅ TRUE | `requirements.txt` : mistralai, transformers, torch, sentencepiece ; SDK Mistral ; pip install |
| Création des accès (comptes, groupes, droits) | ✅ TRUE | `scripts/create_test_user.py` : admin, reader ; table `profils` ; RBAC (reader/writer/deleter/admin) ; JWT pour l’API |
| Installation et configuration du monitorage | ✅ TRUE | Prometheus (endpoint `/metrics`), Grafana ; `docs/MONITORING_E2_API.md`, `monitoring/README_GRAFANA.md` ; PrometheusMiddleware |
| Rédaction de la documentation | ✅ TRUE | `docs/MISTRAL_IA_INSIGHTS.md`, `docs/README_E2_API.md`, config via `.env.example`, doc des endpoints IA |

---

## Synthèse

| Compétence | Critères OK | Partiel | KO |
|------------|-------------|---------|-----|
| A3 C6 | 9 | 0 | 0 |
| A3 C7 | 4 | 0 | 0 |
| A3 C8 | 5 | 0 | 0 |

### Statut : ✅ 100 % conforme

### Références des artefacts

| Critère | Fichiers / composants |
|---------|------------------------|
| C6 Veille | `scripts/veille_digest.py`, `scripts/veille_sources.json`, `docs/VEILLE_PLANIFICATION.md`, `docs/veille/`, Streamlit (bouton Veille IA) |
| C7 Benchmark | `scripts/ai_benchmark.py`, `docs/e2/AI_BENCHMARK.md`, `docs/e2/AI_REQUIREMENTS.md` (générés) |
| C8 Paramétrage | `src/config.py`, `src/e3/mistral/service.py`, `.env.example`, `scripts/create_test_user.py`, `docs/MONITORING_E2_API.md`, `docs/MISTRAL_IA_INSIGHTS.md` |
