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

- **`migrate_sources.py`** : Ajouter des sources manquantes à la DB
  ```bash
  python scripts/migrate_sources.py
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

## 📖 Documentation

Voir `docs/DASHBOARD_GUIDE.md` pour plus de détails sur l'utilisation.

