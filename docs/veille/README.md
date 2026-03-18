# Dossier `docs/veille` - A quoi il sert

Ce dossier contient les syntheses de veille E2 generees automatiquement.

## Origine des fichiers

- Script : `scripts/veille_digest.py`
- Configuration des flux : `scripts/veille_sources.json`
- Sortie : `docs/veille/veille_YYYY-MM-DD.md`

## Pourquoi c'est utile

- tracer la veille techno/reglementaire dans le temps,
- relier les decisions E2 a des sources explicites,
- disposer d'une preuve concrete de la veille dans le dossier projet.

## Regeneration

```bash
python scripts/veille_digest.py
```
