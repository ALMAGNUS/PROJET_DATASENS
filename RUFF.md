# Ruff – qualité et format du code

Ruff est configuré dans `pyproject.toml` (règles E, W, F, I, UP, B, SIM, etc.). Le CI exécute Ruff sur chaque push/PR.

## Lancer Ruff en local

**Tout en un (fix auto + format) :**
```bat
run_ruff.bat
```

**Ou à la main :**
```bat
.venv\Scripts\activate.bat
ruff check src scripts main.py run_e2_api.py tests --fix
ruff format src scripts main.py run_e2_api.py tests
```

**Voir les problèmes sans corriger :**
```bat
ruff check src scripts main.py run_e2_api.py tests
ruff format --check src scripts main.py run_e2_api.py tests
```

## Améliorations déjà faites

- **Chrono (`_chrono_data`)** : 3 blocs dupliqués (gold, silver, goldai) remplacés par une fonction interne `scan_stage_dir`. **~20 lignes en moins** (avant ~48, après ~28).
- **Panel Datasets / Cockpit** : flux RAW → SILVER → GOLD clarifié, pas de confusion ZZDB/parquet.
- **Règles ignorées** (dans pyproject) : E402 (import après sys.path dans scripts), B008 (Depends), T201 (print voulu), etc.

## Avant un commit

Exécuter `run_ruff.bat` (ou `ruff check ... --fix` puis `ruff format ...`) pour que le CI passe.
