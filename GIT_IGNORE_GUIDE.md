# 📋 Guide .gitignore - Exclusions Git

## ✅ Fichiers et Dossiers Exclus du Versioning

### 📁 Dossiers Exclus

| Dossier | Raison | Contenu |
|---------|--------|---------|
| `data/` | Données volumineuses | RAW, SILVER, GOLD, fichiers Parquet, JSON, CSV |
| `exports/` | Exports générés | CSV et Parquet exportés |
| `visualizations/` | Graphiques générés | Images PNG avec timestamp |
| `docs/` | Documentation | Fichiers Markdown de documentation |
| `logs/` | Fichiers de log | Logs d'exécution |
| `*.db`, `*.sqlite` | Bases de données | Fichiers SQLite (trop volumineux) |

### 📄 Fichiers Exclus

- `*.log` - Fichiers de log
- `*.db`, `*.sqlite` - Bases de données
- `.env`, `.env.local` - Variables d'environnement
- `*.ipynb` - Notebooks Jupyter
- Fichiers temporaires (`*.tmp`, `*.bak`, `*.swp`)

---

## 🚀 Commandes Utiles

### Vérifier ce qui sera commité

```bash
git status
```

### Voir uniquement les fichiers trackés (hors .gitignore)

```bash
git ls-files
```

### Vérifier si un fichier est ignoré

```bash
git check-ignore -v chemin/vers/fichier
```

### Retirer des fichiers déjà trackés (si nécessaire)

```bash
# Retirer un dossier du tracking
git rm -r --cached nom_du_dossier/

# Puis commit
git commit -m "Remove tracked files from git"
```

---

## 📊 Impact

**Avant** : Tous les fichiers (docs, data, exports) étaient trackés  
**Après** : Seulement le code source et la configuration sont trackés

**Résultat** :
- ✅ Push plus rapides (pas de fichiers volumineux)
- ✅ Repository plus léger
- ✅ Pas de données sensibles dans Git
- ✅ Historique Git plus propre

---

## ⚠️ Important

Les fichiers dans `data/`, `exports/`, `visualizations/` et `docs/` **ne seront pas** :
- ❌ Commités
- ❌ Pushés vers le remote
- ❌ Versionnés dans Git

**Ils restent sur votre machine locale** mais ne sont pas partagés via Git.

---

## 🔄 Pour Partager les Données

Si vous devez partager des données avec l'équipe :

1. **Utiliser un stockage externe** (S3, Google Drive, etc.)
2. **Créer un script de téléchargement** dans le README
3. **Utiliser Git LFS** (Large File Storage) pour fichiers spécifiques
4. **Documenter** où trouver les données dans le README

---

**Status**: ✅ `.gitignore` configuré - Docs et données exclus du versioning
