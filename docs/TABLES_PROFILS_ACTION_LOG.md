# 👤 TABLES PROFILS & USER_ACTION_LOG - Documentation Complète

## 📊 VUE D'ENSEMBLE

**2 tables créées** :
1. **PROFILS** : Gestion des utilisateurs (authentification future)
2. **USER_ACTION_LOG** : Journalisation des actions (audit trail)

**Relation** : PROFILS 1 → N USER_ACTION_LOG (un utilisateur a plusieurs actions loggées)

**Isolation** : ✅ Ces 2 tables sont **isolées** des tables E1 (pas de FK dans RAW_DATA, SOURCE, etc.)

---

## 📋 TABLE 1 : PROFILS

### **Objectif**
Stocker les informations des utilisateurs pour l'authentification future (E2).

### **Attributs**

| Attribut | Type | Contraintes | Description |
|----------|------|-------------|-------------|
| `profil_id` | INTEGER | **PK**, AUTOINCREMENT | Identifiant unique de l'utilisateur |
| `email` | VARCHAR(255) | **UNIQUE**, NOT NULL | Email (identifiant de connexion) |
| `password_hash` | VARCHAR(255) | NOT NULL | Hash du mot de passe (bcrypt/argon2) |
| `firstname` | VARCHAR(100) | NOT NULL | Prénom |
| `lastname` | VARCHAR(100) | NOT NULL | Nom |
| `role` | VARCHAR(20) | NOT NULL, **CHECK** | Rôle : 'reader', 'writer', 'deleter', 'admin' |
| `active` | BOOLEAN | DEFAULT 1 | Compte actif (1) ou désactivé (0) |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Date de création du compte |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Dernière modification |
| `last_login` | DATETIME | NULLABLE | Dernière connexion (NULL si jamais connecté) |
| `username` | VARCHAR(50) | NULLABLE, UNIQUE | Nom d'utilisateur (optionnel, email peut servir) |

### **Clé Primaire**
- `profil_id` : Identifiant unique auto-incrémenté

### **Contraintes**
- `email` : UNIQUE (un email = un compte)
- `username` : UNIQUE (si renseigné)
- `role` : CHECK (seulement 'reader', 'writer', 'deleter', 'admin')

### **Index**
- `idx_profils_email` : Recherche rapide par email
- `idx_profils_role` : Filtrage par rôle
- `idx_profils_active` : Filtrage des comptes actifs

### **Exemple de Données**

| profil_id | email | firstname | lastname | role | active | created_at |
|-----------|-------|-----------|----------|------|--------|------------|
| 1 | admin@datasens.fr | Admin | DataSens | admin | 1 | 2025-01-15 10:00:00 |
| 2 | writer@datasens.fr | Writer | User | writer | 1 | 2025-01-15 10:05:00 |
| 3 | reader@datasens.fr | Reader | User | reader | 1 | 2025-01-15 10:10:00 |

---

## 📋 TABLE 2 : USER_ACTION_LOG

### **Objectif**
Journaliser toutes les actions des utilisateurs pour l'audit (qui a fait quoi, quand, sur quelle ressource).

### **Attributs**

| Attribut | Type | Contraintes | Description |
|----------|------|-------------|-------------|
| `action_log_id` | INTEGER | **PK**, AUTOINCREMENT | Identifiant unique de l'action loggée |
| `profil_id` | INTEGER | **FK**, NOT NULL | Utilisateur qui a effectué l'action (→ PROFILS.profil_id) |
| `action_type` | VARCHAR(50) | NOT NULL | Type d'action : 'create', 'read', 'update', 'delete', 'export', 'login' |
| `resource_type` | VARCHAR(50) | NOT NULL | Type de ressource : 'raw_data', 'source', 'export', 'dashboard', 'gold' |
| `resource_id` | INTEGER | NULLABLE | ID de la ressource (raw_data_id, source_id, etc.) - NULL si action globale |
| `action_date` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Date/heure de l'action |
| `ip_address` | VARCHAR(45) | NULLABLE | Adresse IP de l'utilisateur (IPv4 ou IPv6) |
| `details` | TEXT | NULLABLE | Détails supplémentaires (JSON) : `{"field": "title", "old": "...", "new": "..."}` |

### **Clé Primaire**
- `action_log_id` : Identifiant unique auto-incrémenté

### **Clé Étrangère**
- `profil_id` → `PROFILS.profil_id` (ON DELETE CASCADE : si utilisateur supprimé, ses logs aussi)

### **Index**
- `idx_action_log_profil` : Recherche rapide par utilisateur
- `idx_action_log_date` : Tri par date
- `idx_action_log_type` : Filtrage par type d'action

### **Exemple de Données**

| action_log_id | profil_id | action_type | resource_type | resource_id | action_date | ip_address |
|---------------|-----------|-------------|---------------|-------------|-------------|------------|
| 1 | 1 | create | raw_data | 456 | 2025-01-15 10:30:00 | 192.168.1.100 |
| 2 | 1 | read | raw_data | 456 | 2025-01-15 10:35:00 | 192.168.1.100 |
| 3 | 2 | update | source | 5 | 2025-01-15 11:00:00 | 192.168.1.101 |
| 4 | 1 | export | gold | NULL | 2025-01-15 12:00:00 | 192.168.1.100 |

---

## 🔗 RELATION ENTRE LES 2 TABLES

### **Relation Merise**

```
PROFILS (1) ──→ (N) USER_ACTION_LOG
```

**Type** : **1 → N** (Un utilisateur a plusieurs actions loggées)

**Clé Commune** : `profil_id` (dans USER_ACTION_LOG, référence PROFILS.profil_id)

### **Schéma Visuel**

```
┌─────────────────┐
│   PROFILS       │
│  profil_id (PK) │ ←──┐
│  email          │    │
│  firstname      │    │
│  lastname       │    │
│  role           │    │
└─────────────────┘    │
                        │ FK (profil_id)
                        │
                        │
┌─────────────────────────────────────┐
│   USER_ACTION_LOG                   │
│  action_log_id (PK)                 │
│  profil_id (FK) ────────────────────┘
│  action_type                         │
│  resource_type                       │
│  resource_id                         │
│  action_date                         │
└─────────────────────────────────────┘
```

### **Contrainte de Référence**

```sql
FOREIGN KEY (profil_id) REFERENCES profils(profil_id) ON DELETE CASCADE
```

**Signification** :
- Si un utilisateur est supprimé (`DELETE FROM profils WHERE profil_id = 1`)
- Toutes ses actions loggées sont automatiquement supprimées (CASCADE)

---

## ✅ ISOLATION DES TABLES E1

### **Principe**

**PROFILS et USER_ACTION_LOG sont isolées** des tables E1 :
- ❌ **Aucune FK dans RAW_DATA** (pas de `created_by`)
- ❌ **Aucune FK dans SOURCE** (pas de `created_by`)
- ❌ **Aucune FK dans les autres tables E1**

### **Comment ça fonctionne sans FK dans E1 ?**

**Référence indirecte** via `resource_type` + `resource_id` :

```
USER_ACTION_LOG
├── resource_type = 'raw_data'  ← Type de ressource
└── resource_id = 456           ← ID de la ressource (raw_data_id)
```

**Exemple** :
- Action : `create` sur `raw_data` avec `resource_id = 456`
- Pour savoir qui a créé l'article 456 : Requête JOIN entre USER_ACTION_LOG et PROFILS
- Pas besoin de FK dans RAW_DATA !

### **Avantages de l'Isolation**

1. ✅ **Pas de modification E1** : Tables RAW_DATA, SOURCE, etc. inchangées
2. ✅ **Code existant intact** : Pipeline E1 fonctionne normalement
3. ✅ **Audit complet** : Toutes les actions loggées (create, read, update, delete, export)
4. ✅ **Flexible** : Fonctionne pour toutes les ressources (raw_data, source, export, etc.)
5. ✅ **Historique** : On peut voir l'historique complet d'une ressource

---

## 📊 EXEMPLES DE REQUÊTES

### **1. Qui a créé l'article 456 ?**

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

**Résultat** :
```
email: admin@datasens.fr
firstname: Admin
lastname: DataSens
action_date: 2025-01-15 10:30:00
```

---

### **2. Toutes les actions d'un utilisateur**

```sql
SELECT 
    ual.action_type,
    ual.resource_type,
    ual.resource_id,
    ual.action_date
FROM user_action_log ual
WHERE ual.profil_id = 1
ORDER BY ual.action_date DESC;
```

---

### **3. Historique complet d'une ressource**

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

## 🎯 RÉSUMÉ

### **Table PROFILS**
- ✅ Stocke les utilisateurs (email, password_hash, role, etc.)
- ✅ Clé primaire : `profil_id`
- ✅ Isolée des tables E1

### **Table USER_ACTION_LOG**
- ✅ Journalise toutes les actions des utilisateurs
- ✅ Clé primaire : `action_log_id`
- ✅ Clé étrangère : `profil_id` → `PROFILS.profil_id`
- ✅ Référence indirecte aux ressources E1 via `resource_type` + `resource_id`
- ✅ Isolée des tables E1 (pas de FK dans RAW_DATA, SOURCE, etc.)

### **Relation**
- ✅ **1 → N** : Un utilisateur a plusieurs actions loggées
- ✅ **Clé commune** : `profil_id` (dans USER_ACTION_LOG)

### **Isolation**
- ✅ **OUI**, les 2 tables fonctionnent de manière isolée
- ✅ **Aucune FK** dans les tables E1
- ✅ **Référence indirecte** via `resource_type` + `resource_id`
- ✅ **Code E1 intact** : Pipeline fonctionne normalement

---

**Status** : ✅ **DOCUMENTATION COMPLÈTE - TABLES ISOLÉES ET FONCTIONNELLES**
