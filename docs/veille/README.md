# Dossier `docs/veille`

Synthèses quotidiennes de veille technologique (compétence C6), générées par `scripts/veille_digest.py`.

## Fichiers

| Fichier | Rôle |
|---------|------|
| `veille_YYYY-MM-DD.md` / `.json` | Snapshot du jour (sources RSS filtrées) |
| `../e2/ANNEXE_C6_SOURCES_MOTS_CLES.md` | Catalogue des sources et mots-clés (mis à jour à chaque run) |

Chaque run quotidien ([`run_daily.ps1`](../../run_daily.ps1) à la racine, ou `python main.py`) alimente ce dossier. L'historique complet est **volontairement versionné** : c'est la preuve C6 d'une veille continue sur la durée du projet (pas seulement une démo du dernier mois).

## Régénération

```bash
python scripts/veille_digest.py
```

Configuration des flux : `scripts/veille_sources.json`.
