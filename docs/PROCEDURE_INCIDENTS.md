# Procédure de résolution des incidents techniques — DataSens

**Critère C21** — Résoudre les incidents techniques de l'application IA

---

## 1. Modèle de gestion d'incident

| Étape | Action | Livrable |
|-------|--------|----------|
| **1. Identification** | Détecter le problème (alerte, log, rapport utilisateur) | Signalement (Issue, ticket) |
| **2. Diagnostic** | Identifier la cause racine (RCA) | Cause documentée |
| **3. Reproduction** | Reproduire en environnement de développement | Cas de test ou script |
| **4. Débogage** | Appliquer la procédure de débogage | Solution technique |
| **5. Implémentation** | Coder la correction | Commit / merge request |
| **6. Validation** | Tester (tests unitaires, CI) | Tests verts |
| **7. Versionnement** | Commiter et merger dans le dépôt | Historique Git |
| **8. Documentation** | Mettre à jour CHANGELOG et éventuellement la doc | Traçabilité |

---

## 2. Procédure de débogage

### 2.1 Localisation de l'erreur

1. **Logs** : Consulter `sync_log`, `user_action_log`, `logs/datasens.log`
2. **Métriques** : Vérifier Prometheus/Grafana (http://localhost:9090, http://localhost:3000)
3. **Stack trace** : Repérer le fichier et la ligne dans l'exception Python
4. **Contexte** : Source de données, moment (après mise à jour ?), environnement

### 2.2 Reproduction en local

```bash
# Activer l'environnement
.\.venv\Scripts\Activate.ps1   # Windows

# Lancer les tests concernés
pytest tests/test_e1_isolation.py -v
pytest tests/test_e2_api.py -v

# Reproduire via script minimal si besoin
python -c "from src.e1.core import ...; ..."
```

### 2.3 Correction et validation

1. Modifier le code (fix ciblé)
2. Lancer les tests : `pytest tests/ -v`
3. Vérifier le CI : push sur une branche, vérifier GitHub Actions

---

## 3. Exemple documenté : Incident 1.4.1 (encodage GDELT)

### Contexte

- **Problème** : Plantage du pipeline lors du chargement de fichiers JSON GDELT (caractères invalides, null bytes)
- **Symptôme** : `UnicodeDecodeError` ou crash silencieux sur `_collect_local_files()`
- **Détection** : Logs, erreurs lors de l'agrégation GOLD

### Cause identifiée

- Null bytes (`\x00`), caractères de contrôle et caractère de remplacement Unicode (`\ufffd`) dans les champs `title` et `content`
- Lecture JSON sans gestion d'erreur d'encodage

### Solution implémentée

1. **sanitize_text()** : Suppression des null bytes et caractères invalides
2. **ContentTransformer** : Application de `sanitize_text()` sur `title` et `content`
3. **Lecture JSON** : `encoding='utf-8', errors='replace'`
4. **sanitize_url()** : Nettoyage des URLs

### Fichiers modifiés

- `src/e1/core.py`
- `src/e1/aggregator.py`
- `src/aggregator.py`

### Versionnement

- Commit : CHANGELOG [1.4.1] — 2025-02-10
- Dépôt : Git, branche main

---

## 4. Suivi des incidents (outil)

- **GitHub Issues** : Créer une issue pour chaque incident (template : titre, description, étapes reproduction, solution)
- **Labels** : `bug`, `incident`, `monitoring`
- **Lien** : Associer le commit de correction à l'issue (`fixes #XX`)

---

## 5. Références

- **CHANGELOG** : Historique des corrections
- **Tests** : `tests/test_e1_isolation.py`, `tests/test_e2_api.py`
- **CI** : `.github/workflows/ci-cd.yml`
