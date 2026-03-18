# 📊 Guide Dashboard & Rapports de Collecte

## 🎯 Vue d'ensemble

Le système DataSens inclut **3 outils de visualisation** qui se mettent à jour automatiquement :

1. **Rapport de Collecte** (session actuelle) - S'affiche après chaque `python main.py`
2. **Dashboard Global** (toutes les données) - Vue d'ensemble complète
3. **Visualiseur CSV** - Pour explorer les fichiers exports/

---

## 1️⃣ Rapport de Collecte (Session Actuelle)

### ✅ Automatique après chaque collecte

Le rapport s'affiche **automatiquement** à la fin de chaque exécution de `python main.py`.

### 📋 Contenu du rapport

- **Résumé session** : Articles collectés, taggés, analysés dans cette session
- **Détail par source** : Combien d'articles collectés par source dans cette session
- **Distribution topics** : Quels topics ont été assignés aux nouveaux articles
- **Distribution sentiment** : Répartition positif/neutre/négatif des nouveaux articles

### 🔄 Dynamique

Le rapport est **100% dynamique** : il lit directement depuis la base de données et montre uniquement les articles collectés **depuis le début de la session actuelle**.

---

## 2️⃣ Dashboard Global

### 📊 Afficher le dashboard

```bash
# À tout moment
python show_dashboard.py
```

### 📋 Contenu du dashboard

- **Résumé global** : Total articles, uniques, nouveaux aujourd'hui, enrichis
- **Nouveaux articles** : Détail par source des articles collectés aujourd'hui
- **Enrichissement Topics** : Articles taggés, topics utilisés, confiance moyenne
- **Enrichissement Sentiment** : Distribution positif/neutre/négatif
- **Articles par source** : Statistiques détaillées par source
- **Évaluation IA** : Status du dataset pour l'entraînement IA

### 🔄 Dynamique

Le dashboard est **100% dynamique** : il lit directement depuis la base de données à chaque exécution, donc il reflète toujours l'état actuel de vos données.

---

## 3️⃣ Visualiser les CSV dans exports/

### 📂 Fichiers disponibles

Les fichiers CSV sont générés automatiquement dans le dossier `exports/` :

- **`raw.csv`** : Toutes les données brutes (DB + fichiers locaux Kaggle/GDELT)
- **`silver.csv`** : Données nettoyées avec topics (sans sentiment)
- **`gold.csv`** : Données complètes avec topics + sentiment

### 👀 Visualiser les CSV

```bash
# Script interactif pour explorer les CSV
python view_exports.py
```

Le script vous permet de :
- Voir la liste des fichiers disponibles
- Choisir un fichier à visualiser (1-3)
- Voir tous les fichiers d'un coup (`all`)
- Aperçu des premières lignes avec colonnes

### 📊 Ouvrir directement dans Excel/Notepad

Les fichiers CSV sont dans :
```
C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS\exports\
```

Vous pouvez :
- **Double-cliquer** sur `raw.csv`, `silver.csv`, ou `gold.csv` pour les ouvrir dans Excel
- **Ouvrir avec Notepad** pour voir le contenu brut
- **Importer dans Power BI** ou Tableau pour visualisations avancées

---

## 🔄 Mise à jour automatique

### ✅ Oui, tout est dynamique !

1. **Rapport de collecte** : Se génère automatiquement après chaque `python main.py`
2. **Dashboard** : Lit toujours les données les plus récentes depuis la DB
3. **CSV exports** : Sont régénérés à chaque run du pipeline

### 📈 Exemple de workflow

```bash
# 1. Lancer la collecte
python main.py

# → Affiche automatiquement :
#    - Rapport de collecte (session actuelle)
#    - Dashboard global (toutes les données)
#    - Génère les CSV dans exports/

# 2. Voir les CSV
python view_exports.py

# 3. Vérifier le dashboard à tout moment
python show_dashboard.py
```

---

## 📊 Structure des fichiers CSV

### raw.csv
Colonnes : `id`, `source`, `title`, `content`, `url`, `fingerprint`, `collected_at`

### silver.csv
Colonnes : `id`, `source`, `title`, `content`, `url`, `fingerprint`, `collected_at`, `topic_1`, `topic_1_score`, `topic_2`, `topic_2_score`

### gold.csv
Colonnes : `id`, `source`, `title`, `content`, `url`, `collected_at`, `topic_1`, `topic_1_score`, `topic_2`, `topic_2_score`, `sentiment`, `sentiment_score`

---

## 💡 Conseils

1. **Vérifier après chaque collecte** : Le rapport de collecte vous montre exactement ce qui a été ajouté
2. **Dashboard régulier** : Utilisez `python show_dashboard.py` pour suivre l'évolution du dataset
3. **CSV pour analyse** : Les fichiers CSV sont parfaits pour Excel, Python, ou outils BI
4. **Enrichissement rétroactif** : Si vous voulez enrichir tous les anciens articles :
   ```bash
   python enrich_all_articles.py
   ```

---

## ❓ Questions fréquentes

**Q: Le dashboard se met à jour automatiquement ?**  
R: Oui ! Il lit directement depuis la DB, donc il reflète toujours l'état actuel.

**Q: Où sont les fichiers CSV ?**  
R: Dans `exports/` à la racine du projet. Vous pouvez les ouvrir directement dans Excel.

**Q: Le rapport de collecte montre quoi ?**  
R: Uniquement les articles collectés dans la session actuelle (depuis le dernier `python main.py`).

**Q: Comment voir les nouveaux articles d'aujourd'hui ?**  
R: Le dashboard global montre une section "[NOUVEAUX] NOUVEAUX ARTICLES AUJOURD'HUI PAR SOURCE".

