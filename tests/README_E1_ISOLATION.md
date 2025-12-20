# 🧪 Tests de Non-Régression E1

**Objectif**: Garantir qu'E1 fonctionne toujours après isolation et lors de la construction E2/E3

---

## 🚀 Lancement Rapide

### Tests rapides (sans tests lents)
```bash
pytest tests/test_e1_isolation.py -v -m "not slow"
```

### Tous les tests (y compris tests lents)
```bash
pytest tests/test_e1_isolation.py -v
```

### Via script dédié
```bash
python tests/run_e1_isolation_tests.py --fast   # Tests rapides
python tests/run_e1_isolation_tests.py --slow   # Tous les tests
python tests/run_e1_isolation_tests.py          # Tests rapides par défaut
```

---

## 📋 Tests Disponibles

### **TestE1Isolation** (Tests rapides)
- ✅ `test_e1_pipeline_importable` : E1Pipeline doit être importable
- ✅ `test_e1_core_importable` : Tous les modules E1 sont accessibles
- ✅ `test_e1_database_schema` : Schéma DB E1 existe
- ✅ `test_e1_interface_stable` : Interface E1DataReader fonctionne
- ✅ `test_e1_exports_structure` : Structure exports E1 correcte
- ✅ `test_e1_pipeline_initialization` : E1Pipeline s'initialise
- ✅ `test_e1_repository_methods` : Repository E1 fonctionne
- ✅ `test_e1_shared_interface_importable` : Interface shared accessible
- ✅ `test_e1_no_direct_imports_from_e2_e3` : E1 isolé (pas de dépendances E2/E3)

### **TestE1PipelineComplete** (Tests lents - marqués `@pytest.mark.slow`)
- ⏱️ `test_e1_pipeline_complete` : Exécute le pipeline E1 complet

---

## ✅ Validation Avant Merge

**RÈGLE**: Tous les tests rapides DOIVENT passer avant chaque merge E2/E3

```bash
# Avant chaque merge
pytest tests/test_e1_isolation.py -v -m "not slow"

# Résultat attendu: Tous les tests passent ✅
```

---

## 🔍 Détails des Tests

### Test d'Import
Vérifie que E1 peut être importé depuis le package isolé :
```python
from e1.pipeline import E1Pipeline
```

### Test de Schéma DB
Vérifie que les tables E1 existent :
- `source`
- `raw_data`
- `sync_log`
- `topic`
- `document_topic`
- `model_output`

### Test d'Interface
Vérifie que `E1DataReader` fonctionne :
- Lecture RAW
- Lecture SILVER
- Lecture GOLD
- Stats DB

### Test d'Isolation
Vérifie que E1 n'importe PAS depuis E2/E3 (isolation respectée)

---

## 🚨 En Cas d'Échec

Si un test échoue :

1. **Vérifier l'isolation** : E1 ne doit pas avoir été modifié
2. **Vérifier les imports** : Les chemins d'import doivent être corrects
3. **Vérifier la DB** : Le schéma doit être intact
4. **Vérifier les exports** : Les dossiers `exports/` et `data/` doivent exister

---

## 📊 CI/CD

Les tests sont automatiquement lancés dans GitHub Actions :
- **Tests rapides** : À chaque push/PR
- **Tests complets** : Sur push vers `main` uniquement

Voir `.github/workflows/test.yml`

---

## 📚 Documentation

- **Stratégie isolation** : `docs/E1_ISOLATION_STRATEGY.md`
- **Plan d'action** : `docs/PLAN_ACTION_E1_E2_E3.md`

---

**Status**: ✅ **TESTS CRÉÉS - PRÊTS POUR VALIDATION**
