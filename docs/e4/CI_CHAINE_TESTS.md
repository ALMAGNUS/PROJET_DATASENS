# Chaîne d'intégration continue — DataSens E4

## Outil

**GitHub Actions** — workflows dans `.github/workflows/`

---

## Workflows

### 1. test.yml

| Élément | Valeur |
|---------|--------|
| **Déclencheur** | `push`, `pull_request` |
| **Jobs** | `test-e1-isolation`, `test-e1-complete` (main uniquement, slow) |
| **Étapes** | checkout, setup Python 3.10, pip install, PYTHONPATH, pytest |
| **Tests** | `tests/test_e1_isolation.py` (-m "not slow" par défaut) |
| **Validation** | Import E1Pipeline, E1DataReader, structure exports/data |

### 2. ci-cd.yml

| Élément | Valeur |
|---------|--------|
| **Déclencheur** | `push`, `pull_request` (main, develop) |
| **Jobs** | `test` → `build` → `deploy` |
| **test** | Lint, pytest (E1 isolation + autres), validation structure |
| **build** | Docker build, push ghcr.io (si pas PR) |
| **deploy** | Placeholder (main uniquement) |

### 3. e3-quality-gate.yml

| Élément | Valeur |
|---------|--------|
| **Déclencheur** | `push`, `pull_request` (main, develop) |
| **Job** | `e3-quality-gate` |
| **Étapes** | checkout, setup Python 3.10, pip install, PYTHONPATH, `python scripts/run_e3_quality_gate.py` |
| **Tests** | `tests/test_e3_quality_gate.py` (4 tests : RAW vide, fallback drift, predict, metrics) |

---

## Procédure d'installation et de test (local)

```bash
# 1. Cloner et installer
git clone <repo>
cd PROJET_DATASENS
pip install -r requirements.txt pytest

# 2. Configurer PYTHONPATH
export PYTHONPATH=$PWD:$PWD/src

# 3. Lancer les tests E1
pytest tests/test_e1_isolation.py -v -m "not slow"

# 4. Lancer le quality gate E3
python scripts/run_e3_quality_gate.py

# 5. Lancer tous les tests
pytest tests/ -v
```

---

## Déclencheurs résumés

| Événement | Workflows exécutés |
|-----------|-------------------|
| Push sur main/develop | test, ci-cd, e3-quality-gate |
| Pull request | test, ci-cd, e3-quality-gate |
| Push sur autre branche | (selon config) |
