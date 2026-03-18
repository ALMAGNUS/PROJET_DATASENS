# Annexe 3 — Plan de soutenance E4 (15 min)

## Structure

| Durée | Séquence | Compétences |
|-------|----------|-------------|
| 0:00 - 1:30 | Contexte E4, périmètre A6/A7/A8 | — |
| 1:30 - 4:00 | Conception (C14/C15) : données, parcours, architecture | C14, C15 |
| 4:00 - 7:00 | Développement (C16/C17) : cockpit, API, droits | C16, C17 |
| 7:00 - 10:00 | Tests et livraison (C18/C19) : CI/CD, workflows | C18, C19 |
| 10:00 - 13:00 | Démo live : cockpit, prédiction, assistant IA | C17 |
| 13:00 - 15:00 | Conclusion, annexes, Q&A | — |

---

## Séquence 1 : Contexte (0:00 - 1:30)

- Présenter le bloc E4 (conception, développement, tests/livraison)
- Rappeler les compétences C14 à C19
- Montrer le dossier principal et le tableau de couverture

---

## Séquence 2 : Conception (1:30 - 4:00)

- **C14** : Modélisation données (zones RAW/SILVER/GOLD, tables SQLite), parcours utilisateurs (PARCOURS_UTILISATEUR.md), user stories (AGILE_ROADMAP.md), accessibilité (OBJECTIFS_ACCESSIBILITE.md)
- **C15** : Architecture (ARCHITECTURE.md), flux data (DATA_FLOW.md), choix techniques (Python, FastAPI, Streamlit, Docker), specs techniques (README_E2_API.md)

---

## Séquence 3 : Développement (4:00 - 7:00)

- **C16** : Outils pilotage (GitHub Projects, AGILE_ROADMAP), communication
- **C17** : Cockpit Streamlit (pages, auth), API (routes, RBAC), droits (JWT, profils), tests (pytest), Git, documentation

---

## Séquence 4 : Tests et livraison (7:00 - 10:00)

- **C18** : Workflows GitHub Actions (test, e3-quality-gate), étapes, déclencheurs, doc CI_CHAINE_TESTS.md
- **C19** : Chaîne CD (ci-cd.yml), build Docker, push registry, doc CD_CHAINE_LIVRAISON.md

---

## Séquence 5 : Démo live (10:00 - 13:00)

1. Lancer API + cockpit
2. Login (formulaire, JWT)
3. Page Pilotage : flux Parquet, fusion GoldAI
4. Page Benchmark : résultats, filtres
5. Page Assistant IA : question par thème, réponse Mistral
6. Prédiction sentiment : saisie texte, appel API, résultat

---

## Séquence 6 : Conclusion (13:00 - 15:00)

- Synthèse : conception documentée, développement opérationnel, CI/CD en place
- Renvoi aux annexes (preuves, captures, extraits code)
- Q&A
