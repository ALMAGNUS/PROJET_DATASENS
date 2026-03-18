# 🔍 AUDIT VIA USER_ACTION_LOG - Comment ça marche ?

## 🎯 PRINCIPE

**USER_ACTION_LOG** est une table de **journalisation** (logging) qui enregistre **qui a fait quoi, quand, sur quelle ressource**, **SANS modifier les tables E1**.

---

## 📊 STRUCTURE DE LA TABLE

```sql
CREATE TABLE user_action_log (
    action_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profil_id INTEGER NOT NULL REFERENCES profils(profil_id),
    action_type VARCHAR(50) NOT NULL,      -- 'create', 'read', 'update', 'delete', 'export'
    resource_type VARCHAR(50) NOT NULL,    -- 'raw_data', 'source', 'export', 'dashboard'
    resource_id INTEGER,                    -- ID de la ressource (raw_data_id, source_id, etc.)
    action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),                 -- IP de l'utilisateur
    details TEXT                            -- Détails supplémentaires (JSON)
);
```

---

## 🔗 COMMENT ÇA FONCTIONNE ?

### **Principe : Référence Indirecte**

Au lieu d'ajouter `created_by` dans RAW_DATA (qui modifierait E1), on **loggue l'action** dans USER_ACTION_LOG :

```
┌─────────────────┐
│   PROFILS       │
│  profil_id = 1  │
│  email = ...    │
└────────┬────────┘
         │
         │ FK (profil_id)
         │
         ▼
┌─────────────────────────────────────┐
│   USER_ACTION_LOG                  │
│  profil_id = 1                     │
│  action_type = 'create'            │
│  resource_type = 'raw_data'        │
│  resource_id = 123  ←──┐           │
└─────────────────────────────────────┘
                                    │
                                    │ Référence indirecte
                                    │ (pas de FK, juste l'ID)
                                    ▼
                          ┌─────────────────┐
                          │   RAW_DATA      │
                          │  raw_data_id=123│
                          │  title = ...    │
                          └─────────────────┘
```

**Pas de FK dans RAW_DATA** → On utilise juste `resource_id` pour référencer l'article.

---

## 📝 EXEMPLES CONCRETS

### **Exemple 1 : Utilisateur crée un article**

#### **Scénario** :
- Utilisateur : `profil_id = 1` (admin@datasens.fr)
- Action : Créer un article
- Article créé : `raw_data_id = 456`

#### **Code Python** :

```python
# 1. Créer l'article (code existant, inchangé)
raw_data_id = repository.load_article_with_id(article, source_id)
# raw_data_id = 456

# 2. Logger l'action (NOUVEAU)
repository.log_user_action(
    profil_id=1,
    action_type='create',
    resource_type='raw_data',
    resource_id=456,
    ip_address='192.168.1.100'
)
```

#### **Résultat dans USER_ACTION_LOG** :

| action_log_id | profil_id | action_type | resource_type | resource_id | action_date | ip_address |
|---------------|-----------|-------------|---------------|--------------|-------------|------------|
| 1 | 1 | create | raw_data | 456 | 2025-01-15 10:30:00 | 192.168.1.100 |

#### **Requête SQL pour savoir qui a créé l'article 456** :

```sql
SELECT 
    p.email,
    p.firstname,
    p.lastname,
    ual.action_date,
    ual.ip_address
FROM user_action_log ual
JOIN profils p ON ual.profil_id = p.profil_id
WHERE ual.resource_type = 'raw_data'
  AND ual.resource_id = 456
  AND ual.action_type = 'create';
```

**Résultat** :
```
email: admin@datasens.fr
firstname: Admin
lastname: DataSens
action_date: 2025-01-15 10:30:00
ip_address: 192.168.1.100
```

---

### **Exemple 2 : Utilisateur modifie une source**

#### **Scénario** :
- Utilisateur : `profil_id = 2` (writer@datasens.fr)
- Action : Modifier une source
- Source modifiée : `source_id = 5`

#### **Code Python** :

```python
# 1. Modifier la source (code existant)
# UPDATE source SET active = 0 WHERE source_id = 5

# 2. Logger l'action (NOUVEAU)
repository.log_user_action(
    profil_id=2,
    action_type='update',
    resource_type='source',
    resource_id=5,
    details='{"field": "active", "old_value": 1, "new_value": 0}'
)
```

#### **Résultat dans USER_ACTION_LOG** :

| action_log_id | profil_id | action_type | resource_type | resource_id | details |
|---------------|-----------|-------------|----------------|-------------|---------|
| 2 | 2 | update | source | 5 | {"field": "active", "old_value": 1, "new_value": 0} |

---

### **Exemple 3 : Utilisateur exporte des données**

#### **Scénario** :
- Utilisateur : `profil_id = 3` (reader@datasens.fr)
- Action : Exporter GOLD data
- Pas de ressource spécifique (action globale)

#### **Code Python** :

```python
# 1. Exporter (code existant)
exporter.export_gold()

# 2. Logger l'action (NOUVEAU)
repository.log_user_action(
    profil_id=3,
    action_type='export',
    resource_type='gold',
    resource_id=None,  # Pas de ressource spécifique
    details='{"format": "parquet", "rows": 2659}'
)
```

#### **Résultat dans USER_ACTION_LOG** :

| action_log_id | profil_id | action_type | resource_type | resource_id | details |
|---------------|-----------|-------------|----------------|-------------|---------|
| 3 | 3 | export | gold | NULL | {"format": "parquet", "rows": 2659} |

---

## 🔍 REQUÊTES UTILES

### **1. Qui a créé l'article X ?**

```sql
SELECT 
    p.email,
    p.firstname,
    p.lastname,
    ual.action_date
FROM user_action_log ual
JOIN profils p ON ual.profil_id = p.profil_id
WHERE ual.resource_type = 'raw_data'
  AND ual.resource_id = 456
  AND ual.action_type = 'create'
ORDER BY ual.action_date DESC
LIMIT 1;
```

---

### **2. Toutes les actions d'un utilisateur**

```sql
SELECT 
    ual.action_type,
    ual.resource_type,
    ual.resource_id,
    ual.action_date,
    ual.details
FROM user_action_log ual
WHERE ual.profil_id = 1
ORDER BY ual.action_date DESC;
```

---

### **3. Historique d'une ressource (article)**

```sql
SELECT 
    p.email,
    ual.action_type,
    ual.action_date,
    ual.details
FROM user_action_log ual
JOIN profils p ON ual.profil_id = p.profil_id
WHERE ual.resource_type = 'raw_data'
  AND ual.resource_id = 456
ORDER BY ual.action_date DESC;
```

**Résultat** :
```
email: admin@datasens.fr | action_type: create | action_date: 2025-01-15 10:30:00
email: writer@datasens.fr | action_type: update | action_date: 2025-01-15 14:20:00
email: reader@datasens.fr | action_type: read | action_date: 2025-01-15 16:45:00
```

---

### **4. Statistiques par utilisateur**

```sql
SELECT 
    p.email,
    COUNT(*) as total_actions,
    COUNT(CASE WHEN ual.action_type = 'create' THEN 1 END) as creates,
    COUNT(CASE WHEN ual.action_type = 'update' THEN 1 END) as updates,
    COUNT(CASE WHEN ual.action_type = 'delete' THEN 1 END) as deletes
FROM user_action_log ual
JOIN profils p ON ual.profil_id = p.profil_id
GROUP BY p.profil_id, p.email;
```

---

### **5. Actions récentes (dashboard)**

```sql
SELECT 
    p.email,
    ual.action_type,
    ual.resource_type,
    ual.action_date
FROM user_action_log ual
JOIN profils p ON ual.profil_id = p.profil_id
ORDER BY ual.action_date DESC
LIMIT 50;
```

---

## 💻 IMPLÉMENTATION DANS LE CODE

### **Méthode à ajouter dans `Repository`** :

```python
def log_user_action(self, profil_id: int, action_type: str, 
                   resource_type: str, resource_id: int | None = None,
                   ip_address: str | None = None, details: str | None = None):
    """Log user action in USER_ACTION_LOG (audit trail)"""
    try:
        self.cursor.execute("""
            INSERT INTO user_action_log 
            (profil_id, action_type, resource_type, resource_id, ip_address, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (profil_id, action_type, resource_type, resource_id, ip_address, details))
        self.conn.commit()
        return True
    except Exception as e:
        print(f"   ⚠️  Action log error: {str(e)[:60]}")
        return False
```

---

### **Utilisation dans le pipeline** :

```python
# Dans main.py, après création d'un article
raw_data_id = self.db.load_article_with_id(article, source_id)
if raw_data_id:
    # Logger l'action (si utilisateur connecté)
    if current_user_id:  # Variable globale ou session
        self.db.log_user_action(
            profil_id=current_user_id,
            action_type='create',
            resource_type='raw_data',
            resource_id=raw_data_id,
            ip_address=request.remote_addr if hasattr(request, 'remote_addr') else None
        )
```

---

## ✅ AVANTAGES DE CETTE APPROCHE

1. ✅ **Pas de modification E1** : Tables RAW_DATA, SOURCE inchangées
2. ✅ **Audit complet** : Toutes les actions loggées
3. ✅ **Flexible** : Fonctionne pour toutes les ressources (raw_data, source, export, etc.)
4. ✅ **Historique** : On peut voir l'historique complet d'une ressource
5. ✅ **Performance** : Table séparée, pas d'impact sur requêtes E1
6. ✅ **Extensible** : Facile d'ajouter de nouveaux types d'actions

---

## ⚠️ LIMITATIONS

1. ⚠️ **Pas de contrainte FK** : `resource_id` peut référencer une ressource supprimée
   - **Solution** : Vérifier l'existence de la ressource dans les requêtes

2. ⚠️ **Logging manuel** : Il faut appeler `log_user_action()` à chaque action
   - **Solution** : Middleware/décorateurs dans E2 (FastAPI)

3. ⚠️ **Pas de relation directe** : Impossible de faire `JOIN RAW_DATA.created_by`
   - **Solution** : Utiliser sous-requête ou vue SQL

---

## 🎯 COMPARAISON : USER_ACTION_LOG vs FK dans E1

| Critère | USER_ACTION_LOG | FK dans E1 (created_by) |
|---------|-----------------|-------------------------|
| **Modification E1** | ❌ Aucune | ✅ Nécessaire |
| **Audit complet** | ✅ Oui (toutes actions) | ⚠️ Seulement création |
| **Historique** | ✅ Oui (plusieurs actions) | ❌ Seulement créateur |
| **Performance** | ✅ Table séparée | ⚠️ Colonne supplémentaire |
| **Flexibilité** | ✅ Tous types d'actions | ❌ Seulement création |

---

## 📊 EXEMPLE COMPLET : Workflow Audit

### **Scénario** : Utilisateur admin crée, modifie, puis supprime un article

```python
# 1. Créer article
raw_data_id = repository.load_article_with_id(article, source_id)
repository.log_user_action(1, 'create', 'raw_data', raw_data_id)

# 2. Modifier article (futur - E2)
# UPDATE raw_data SET title = 'Nouveau titre' WHERE raw_data_id = raw_data_id
repository.log_user_action(1, 'update', 'raw_data', raw_data_id, 
                          details='{"field": "title", "old": "Ancien", "new": "Nouveau"}')

# 3. Supprimer article (futur - E2)
# DELETE FROM raw_data WHERE raw_data_id = raw_data_id
repository.log_user_action(1, 'delete', 'raw_data', raw_data_id)
```

**Résultat dans USER_ACTION_LOG** :

| action_log_id | profil_id | action_type | resource_type | resource_id | action_date |
|---------------|-----------|-------------|---------------|-------------|-------------|
| 10 | 1 | create | raw_data | 456 | 2025-01-15 10:00:00 |
| 11 | 1 | update | raw_data | 456 | 2025-01-15 11:00:00 |
| 12 | 1 | delete | raw_data | 456 | 2025-01-15 12:00:00 |

**Historique complet de l'article 456** :
```sql
SELECT * FROM user_action_log 
WHERE resource_type = 'raw_data' AND resource_id = 456
ORDER BY action_date;
```

---

## ✅ RÉSUMÉ

**USER_ACTION_LOG fonctionne comme un journal (log)** :
1. ✅ Chaque action est **enregistrée** avec qui, quoi, quand, sur quelle ressource
2. ✅ **Pas besoin de FK** dans les tables E1
3. ✅ **Référence indirecte** via `resource_type` + `resource_id`
4. ✅ **Audit complet** sans modifier le code E1 existant

**C'est comme un carnet de bord** : on note qui a fait quoi, sans toucher aux tables principales.

---

**Status** : ✅ **EXPLICATION COMPLÈTE - PRÊT POUR IMPLÉMENTATION**
