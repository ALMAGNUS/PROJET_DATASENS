# Annexe 2 — Captures E4 (checklist)

## But

Fournir des preuves visuelles pour valider C14 à C19.

---

## Règle de nommage

`E4_ANNEXE2_<NUMERO>_<SUJET>.png`

---

## Checklist captures

### Capture 1 — Cockpit Streamlit (C17)

- **Titre** : "Interface cockpit — Pilotage données et IA"
- **Écran** : Page Pilotage ou Benchmark du cockpit
- **Contenu** : Flux Parquet, boutons Fusion/Copie IA, ou résultats benchmark

### Capture 2 — Authentification (C17)

- **Titre** : "Authentification JWT — Login et accès protégé"
- **Écran** : Formulaire login ou sidebar avec utilisateur connecté
- **Contenu** : Champs email/mot de passe ou affichage rôle

### Capture 3 — API documentation (C15/C17)

- **Titre** : "Documentation API — OpenAPI/ReDoc"
- **Écran** : http://localhost:8001/docs ou /redoc
- **Contenu** : Endpoints IA, analytics, schémas

### Capture 4 — CI/CD (C18/C19)

- **Titre** : "Chaîne CI/CD — Workflow GitHub Actions"
- **Écran** : GitHub Actions, workflow test ou ci-cd
- **Contenu** : Statut vert, jobs test/build

### Capture 5 — Monitoring (C15)

- **Titre** : "Monitoring — Prometheus/Grafana"
- **Écran** : Grafana dashboard ou Prometheus /metrics
- **Contenu** : Métriques datasens_*

---

## Procédure rapide

1. Lancer API + cockpit (ou docker-compose)
2. Se connecter au cockpit
3. Naviguer Pilotage, Benchmark, Assistant IA
4. Ouvrir /docs, GitHub Actions, Grafana
5. Prendre les 5 captures avec le nommage indiqué
