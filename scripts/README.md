# Scripts Utilitaires DataSens

## 📋 Liste des scripts

### 🗄️ Base de données

- **`setup_with_sql.py`** : Initialiser la base de données SQLite
  ```bash
  python scripts/setup_with_sql.py
  ```

- **`show_tables.py`** : Afficher les tables de la base de données
  ```bash
  python scripts/show_tables.py
  ```

### 📊 Visualisation

- **`show_dashboard.py`** : Afficher le dashboard global d'enrichissement
  ```bash
  python scripts/show_dashboard.py
  ```

- **`view_exports.py`** : Visualiser les fichiers CSV dans exports/
  ```bash
  python scripts/view_exports.py
  ```

### 🔧 Utilitaires

- **`enrich_all_articles.py`** : Enrichir rétroactivement tous les articles
  ```bash
  python scripts/enrich_all_articles.py
  ```

- **`validate_json.py`** : Valider le fichier sources_config.json
  ```bash
  python scripts/validate_json.py
  ```

### 📦 Archivés (`scripts/_archive/`)

One-shot terminés (migrations, démos, smoke tests). Restent exécutables mais ne sont plus référencés dans le pipeline runtime. Voir `docs/AUDIT_CODE_NETTOYAGE.md` pour le détail.

## 📖 Documentation

- `scripts/SCRIPTS_LIST.md` — fiche par script avec rôle et usage.
- `docs/AUDIT_CODE_NETTOYAGE.md` — audit code et plan de nettoyage.
- `docs/DASHBOARD_GUIDE.md` — détails d'utilisation du dashboard.

