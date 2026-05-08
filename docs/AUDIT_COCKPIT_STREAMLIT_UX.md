# Audit UX Cockpit Streamlit

## Matrice de navigation

| Onglet | Objectif principal | Action principale attendue | Blocs secondaires | Complexité visible |
|---|---|---|---|---|
| `Vue d'ensemble` | Lire l'état global du système | Vérifier les KPIs clés du run | Santé technique et détails API | Moyenne |
| `Pipeline & Fusion` | Piloter la fusion GOLD -> GoldAI | Sélectionner une date puis lancer/valider une fusion | Historique run summary, enrichissement détaillé | Élevée |
| `Flux & visualisation` | Explorer les datasets par étape | Charger et inspecter RAW/SILVER/GOLD/GoldAI/IA | Suivi d'article, graphiques avancés | Très élevée |
| `Pilotage` | Exécuter des actions opératoires | Lancer pipeline / API / scripts | Rapports d'exécution | Moyenne |
| `IA` | Interroger la prédiction et l'assistant | Prédire un sentiment ou poser une question | Aide usage, exemples, chat historique | Moyenne |
| `Modèles & Sélection` | Gouverner le modèle actif | Comparer puis activer un modèle | Détails benchmark | Moyenne |
| `Monitoring` | Surveiller l'infra et la qualité data | Lire l'état live des services | Grilles techniques, Mongo/GridFS, télémétrie | Élevée |
| `Démo guidée` | Présenter un parcours court | Suivre le script de démonstration | Rappels sur tous les onglets | Faible |

## Frontière fonctionnelle recommandée

- `Pipeline & Fusion`: décision, contrôle, preuve synthétique.
- `Flux & visualisation`: exploration détaillée des données et diagnostics approfondis.
- `Monitoring`: santé runtime et diagnostics techniques avancés.

## Principes appliqués pendant la stabilisation

- États vides explicites (pas de placeholder ambigu).
- Détails techniques repliés par défaut.
- Messages API harmonisés.
- Réduction des répétitions visuelles sur les sections d'étapes.
