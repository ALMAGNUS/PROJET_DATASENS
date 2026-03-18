# Exigences IA - DataSens E2

## Problématique
Comparer objectivement plusieurs modèles de sentiment pour sélectionner un moteur principal mesuré.

## Contraintes
- Données sensibles: privilégier le traitement local
- Exécution CPU
- Latence compatible API
- Qualité mesurable (scores reproductibles)

## Critères de décision
- Priorité 1: F1 macro (équilibre classes)
- Priorité 2: Accuracy
- Priorité 3: Latence moyenne

## Recommandation actuelle
`finetuned_local` sur la base du benchmark daté.