# Parcours utilisateurs — DataSens E4

## Vue d'ensemble

Ce document modélise les parcours utilisateurs de l'application DataSens (cockpit Streamlit + API). Les flux couvrent l'authentification, le pilotage des données, le pilotage IA et l'assistant conversationnel.

---

## Parcours 1 : Authentification

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Accès      │────▶│  Login form  │────▶│  JWT reçu   │
│  Cockpit    │     │  (user/pwd)  │     │  Session OK │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Accès      │
                                        │  Dashboard  │
                                        └─────────────┘
```

**Étapes :**
1. Utilisateur ouvre le cockpit Streamlit
2. Formulaire de login (identifiant, mot de passe)
3. Appel API `POST /api/v1/auth/login` → JWT
4. Token stocké en session, accès aux pages protégées
5. Bouton déconnexion disponible dans la sidebar

**Acteur :** Utilisateur authentifié (rôle reader, writer ou admin)

---

## Parcours 2 : Pilotage des données (Flux Parquet)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Page       │────▶│  Vue Flux   │────▶│  Fusion     │
│  Pilotage   │     │  Parquet    │     │  GoldAI     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │  Copie IA   │
                                         │  (split)    │
                                         └─────────────┘
```

**Étapes :**
1. Accès à l'onglet « Pilotage » du cockpit
2. Visualisation du flux RAW → SILVER → GOLD → GoldAI
3. Affichage des dates incluses, tailles, métadonnées
4. Bouton « Fusion GoldAI » : exécution `merge_parquet_goldai.py`
5. Bouton « Créer copie IA » : exécution `create_ia_copy.py` (splits train/val/test)
6. Mise à jour des graphiques et compteurs

**Acteur :** Analyste, Admin

---

## Parcours 3 : Pilotage IA (Benchmark et fine-tuning)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Page       │────▶│  Résultats  │────▶│  Fine-tuning│
│  Benchmark  │     │  benchmark  │     │  (optionnel)│
└─────────────┘     └─────────────┘     └─────────────┘
```

**Étapes :**
1. Accès à l'onglet « Benchmark » du cockpit
2. Affichage des résultats (F1 macro, accuracy, latence par modèle)
3. Filtres topics (finance, politique)
4. Option : lancer un cycle de fine-tuning (scripts externes)
5. Visualisation des métriques de validation et courbe de perte

**Acteur :** Data Scientist, Admin

---

## Parcours 4 : Prédiction sentiment

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Saisie     │────▶│  API        │────▶│  Affichage  │
│  texte      │     │  /predict   │     │  label/conf │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Étapes :**
1. Utilisateur saisit un texte dans le champ prévu
2. Clic sur « Prédire » ou équivalent
3. Appel `POST /api/v1/ai/predict` avec `{text, model, task}`
4. Réponse : `{label, confidence, sentiment_score}`
5. Affichage du résultat (positif/négatif/neutre, score)

**Acteur :** Utilisateur authentifié

---

## Parcours 5 : Assistant IA (insights par thème)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Sélection  │────▶│  Question   │────▶│  Réponse    │
│  thème      │     │  utilisateur │     │  Mistral    │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Étapes :**
1. Accès à l'onglet « Assistant IA »
2. Sélection du thème (politique, financier, utilisateurs)
3. Consultation des exemples de données (optionnel)
4. Saisie d'une question
5. Appel `POST /api/v1/ai/insight` → Mistral enrichi du contexte GoldAI
6. Affichage de la réponse

**Acteur :** Utilisateur authentifié (Mistral configuré)

---

## Schéma fonctionnel global

```
                    ┌─────────────────────────────────────┐
                    │           COCKPIT STREAMLIT          │
                    │  ┌─────────┬─────────┬─────────────┐ │
                    │  │Pilotage │Benchmark│ Assistant IA│ │
                    │  └────┬────┴────┬────┴──────┬──────┘ │
                    └───────┼─────────┼───────────┼────────┘
                            │         │           │
                            ▼         ▼           ▼
                    ┌─────────────────────────────────────┐
                    │              API E2/E3               │
                    │  /raw, /silver, /gold, /ai/*,       │
                    │  /analytics/*, /auth/login          │
                    └─────────────────────────────────────┘
                            │
                            ▼
                    ┌─────────────────────────────────────┐
                    │  Pipeline E1 │ ML Inference │ Mistral│
                    └─────────────────────────────────────┘
```
