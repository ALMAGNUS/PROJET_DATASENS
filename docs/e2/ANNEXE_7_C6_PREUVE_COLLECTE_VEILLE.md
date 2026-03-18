# Annexe 7 (C6) - Preuve de collecte de veille

## Objectif

Prouver que la collecte de veille est executee, datee et tracable.

## Preuves de run

- Sortie Markdown datee: `docs/e2/ANNEXE_C6_VEILLE_2026-03-11.md`
- Sortie JSON datee: `docs/e2/ANNEXE_C6_VEILLE_2026-03-11.json`
- Sources et mots-cles: `docs/e2/ANNEXE_C6_SOURCES_MOTS_CLES.md`

## Procedure reproductible

```bash
python scripts/veille_digest.py
```

Attendu:
- generation de fichiers dates dans `docs/veille/`
- copie des preuves dans `docs/e2/` pour annexes dossier.

## Note de tri

Cette annexe sert de point d'entree en soutenance.  
Les fichiers dates restent la preuve brute d'execution.

# Annexe 7 (rattachée à C6) - Preuve de collecte de veille

Cette annexe documente les livrables de collecte générés automatiquement par `scripts/veille_digest.py`.

## Livrables de preuve (date de génération)

- Synthèse Markdown : `docs/veille/veille_2026-03-10.md`
- Snapshot JSON : `docs/veille/veille_2026-03-10.json`
- Copie annexe Markdown : `docs/e2/ANNEXE_C6_VEILLE_2026-03-10.md`
- Copie annexe JSON : `docs/e2/ANNEXE_C6_VEILLE_2026-03-10.json`
- Catalogue sources + mots-clés : `docs/e2/ANNEXE_C6_SOURCES_MOTS_CLES.md`
- Catalogue sources + mots-clés (JSON) : `docs/e2/ANNEXE_C6_SOURCES_MOTS_CLES.json`

## Lecture recommandee

La preuve de collecte est fournie sous double format :

1. Markdown pour lecture rapide et contextualisation des informations collectées.
2. JSON pour preuve technique structurée, horodatée et réutilisable en audit.

Ce double format démontre la traçabilité et la reproductibilité de la veille C6.
