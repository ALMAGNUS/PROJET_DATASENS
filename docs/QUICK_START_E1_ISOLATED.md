# 🚀 Guide de Démarrage Rapide - E1 Isolé

**Pour développeurs** : Comment utiliser E1 isolé et construire E2/E3

---

## ✅ E1 est Isolé - C'est Fait !

E1 est maintenant dans `src/e1/` et est **protégé**. Vous pouvez construire E2/E3 sans risque.

---

## 📦 Structure Actuelle

```
src/
├── e1/          ← E1 ISOLÉ (ne pas modifier depuis E2/E3)
├── e2/          ← E2 (FastAPI) - À construire
├── e3/          ← E3 (PySpark + ML) - À construire
└── shared/      ← Interfaces (E1DataReader)
```

---

## 🔌 Utiliser E1 depuis E2/E3

### **✅ CORRECT - Utiliser E1DataReader**

```python
# src/e2/api/routes/gold.py
from shared.interfaces import E1DataReader, E1DataReaderImpl
from pathlib import Path

# Créer instance
base_path = Path('data')
db_path = Path.home() / 'datasens_project' / 'datasens.db'
reader = E1DataReaderImpl(base_path, db_path)

# Lire données GOLD
df = reader.read_gold_data()  # ✅ Lecture seule
```

### **❌ INCORRECT - Importer directement E1**

```python
# ❌ NE JAMAIS FAIRE
from e1.repository import Repository  # ❌ INTERDIT
from e1.core import Article  # ❌ INTERDIT
```

---

## 🧪 Tests Avant Merge

**RÈGLE** : Tous les tests E1 DOIVENT passer avant chaque merge E2/E3

```bash
# Tests rapides (recommandé)
pytest tests/test_e1_isolation.py -v -m "not slow"

# Résultat attendu: 10 passed ✅
```

---

## 📚 Documentation Complète

- **Stratégie isolation** : `docs/E1_ISOLATION_STRATEGY.md`
- **Plan d'action** : `docs/PLAN_ACTION_E1_E2_E3.md`
- **Récapitulatif Phase 0** : `docs/E1_ISOLATION_COMPLETE.md`
- **Tests** : `tests/README_E1_ISOLATION.md`

---

## 🎯 Prochaines Étapes

1. **Phase 1** : Docker & CI/CD
2. **Phase 2** : FastAPI + RBAC
3. **Phase 3** : PySpark

**Voir** : `docs/PLAN_ACTION_E1_E2_E3.md` pour plan détaillé

---

**Status**: ✅ **E1 ISOLÉ - PRÊT POUR E2/E3**
