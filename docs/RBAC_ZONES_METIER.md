# 🔐 RBAC - Logique Métier des Zones RAW/SILVER/GOLD

## 🎯 Principe Fondamental

Les zones RAW, SILVER et GOLD ont des **rôles métier distincts** qui déterminent les permissions RBAC.

---

## 📊 Les 3 Zones : Rôles & Permissions

### **1. RAW : Preuve Légale & Source de Vérité** 🔒

#### **Rôle Métier**
- **Preuve légale** : Traçabilité complète des données collectées
- **Source de vérité** : Données brutes, non modifiables
- **Audit** : Historique complet des collectes

#### **Caractéristiques**
- ✅ **IMMUABLE** : Aucune modification autorisée
- ✅ **Traçable** : Chaque article a un fingerprint (SHA256)
- ✅ **Auditable** : Logs complets dans `sync_log`
- ✅ **Preuve** : En cas de litige, RAW = preuve légale

#### **Permissions RBAC**

| Rôle | Permission | Justification |
|------|------------|---------------|
| **reader** | ✅ Lecture | Consultation des données brutes |
| **writer** | ❌ Interdit | RAW = immuable, pas de modification |
| **deleter** | ❌ Interdit | RAW = preuve légale, pas de suppression |
| **admin** | ✅ Accès complet | **UNIQUEMENT** en cas d'erreur critique (ex: données corrompues) |

#### **Règles Strictes**
- ❌ **AUCUNE modification** de contenu (title, content, url)
- ❌ **AUCUNE suppression** d'article
- ✅ **Lecture seule** pour tous
- ⚠️ **Admin exceptionnel** : Modification uniquement si erreur critique documentée

#### **Exemple d'Usage**
```python
# ✅ AUTORISÉ : Lecture
GET /api/v1/raw/articles
GET /api/v1/raw/articles/{id}

# ❌ INTERDIT : Écriture
POST /api/v1/raw/articles      # ❌ Interdit
PUT /api/v1/raw/articles/{id}  # ❌ Interdit
DELETE /api/v1/raw/articles/{id} # ❌ Interdit

# ⚠️ EXCEPTION ADMIN : Correction erreur critique
PUT /api/v1/raw/articles/{id}   # ⚠️ Admin uniquement, avec justification
```

---

### **2. SILVER : Zone de Travail** 🔧

#### **Rôle Métier**
- **Zone de travail** : Transformation et amélioration des données
- **Enrichissement** : Ajout topics, sentiment, corrections
- **Qualité** : Amélioration continue de la qualité

#### **Caractéristiques**
- ✅ **MODIFIABLE** : Transformation autorisée
- ✅ **Enrichissement** : Topics, sentiment, corrections
- ✅ **Amélioration** : Correction erreurs, normalisation
- ✅ **Flexible** : Zone de travail pour data scientists

#### **Permissions RBAC**

| Rôle | Permission | Justification |
|------|------------|---------------|
| **reader** | ✅ Lecture | Consultation des données enrichies |
| **writer** | ✅ Lecture + Écriture | Zone de travail : transformation autorisée |
| **deleter** | ✅ Lecture + Suppression | Nettoyage zone de travail |
| **admin** | ✅ Accès complet | Gestion complète zone de travail |

#### **Règles**
- ✅ **Modification autorisée** : Correction, amélioration, enrichissement
- ✅ **Création autorisée** : Ajout articles enrichis manuellement
- ✅ **Suppression autorisée** : Nettoyage données de mauvaise qualité
- ✅ **Flexibilité** : Zone de travail pour amélioration continue

#### **Exemple d'Usage**
```python
# ✅ AUTORISÉ : Lecture (tous)
GET /api/v1/silver/articles
GET /api/v1/silver/articles/{id}

# ✅ AUTORISÉ : Écriture (writer, admin)
POST /api/v1/silver/articles      # ✅ Writer, Admin
PUT /api/v1/silver/articles/{id}  # ✅ Writer, Admin

# ✅ AUTORISÉ : Suppression (deleter, admin)
DELETE /api/v1/silver/articles/{id} # ✅ Deleter, Admin
```

---

### **3. GOLD : Zone de Diffusion** 📊

#### **Rôle Métier**
- **Zone de diffusion** : Données finales validées
- **Export** : Prêtes pour export, visualisation, analyse
- **Production** : Données utilisées par les consommateurs finaux

#### **Caractéristiques**
- ✅ **VALIDÉES** : Données finales, prêtes pour diffusion
- ✅ **STABLES** : Pas de modification après validation
- ✅ **EXPORT** : Format Parquet, CSV pour consommation
- ✅ **DIFFUSION** : Utilisées par dashboards, analyses, rapports

#### **Permissions RBAC**

| Rôle | Permission | Justification |
|------|------------|---------------|
| **reader** | ✅ Lecture | Consultation des données finales |
| **writer** | ❌ Interdit | GOLD = validé, pas de modification |
| **deleter** | ❌ Interdit | GOLD = diffusion, pas de suppression |
| **admin** | ✅ Accès complet | Gestion exceptionnelle si nécessaire |

#### **Règles Strictes**
- ❌ **AUCUNE modification** : Données validées, stables
- ❌ **AUCUNE suppression** : GOLD = zone de diffusion
- ✅ **Lecture seule** : Consultation et export uniquement
- ⚠️ **Admin exceptionnel** : Modification uniquement si erreur critique documentée

#### **Exemple d'Usage**
```python
# ✅ AUTORISÉ : Lecture
GET /api/v1/gold/articles
GET /api/v1/gold/articles/{id}
GET /api/v1/gold/stats

# ❌ INTERDIT : Écriture
POST /api/v1/gold/articles      # ❌ Interdit
PUT /api/v1/gold/articles/{id}  # ❌ Interdit
DELETE /api/v1/gold/articles/{id} # ❌ Interdit

# ⚠️ EXCEPTION ADMIN : Correction erreur critique
PUT /api/v1/gold/articles/{id}   # ⚠️ Admin uniquement, avec justification
```

---

## 🔄 Workflow Complet

```
1. COLLECTE → RAW (preuve légale)
   ↓
   ✅ Lecture seule pour tous
   ❌ Aucune modification
   
2. TRANSFORMATION → SILVER (zone de travail)
   ↓
   ✅ Lecture pour tous
   ✅ Écriture pour writer
   ✅ Suppression pour deleter
   
3. VALIDATION → GOLD (zone de diffusion)
   ↓
   ✅ Lecture seule pour tous
   ❌ Aucune modification
```

---

## 🎯 Récapitulatif Permissions

| Zone | Reader | Writer | Deleter | Admin | **Rôle Métier** |
|------|--------|--------|---------|-------|-----------------|
| **RAW** | ✅ Read | ❌ | ❌ | ✅ Full | 🔒 **Preuve légale** - Source de vérité immuable |
| **SILVER** | ✅ Read | ✅ Write | ✅ Delete | ✅ Full | 🔧 **Zone de travail** - Transformation autorisée |
| **GOLD** | ✅ Read | ❌ | ❌ | ✅ Full | 📊 **Zone de diffusion** - Données validées, lecture seule |

---

## 📋 Règles d'Exception Admin

### **RAW : Modification Exceptionnelle**

**Conditions** :
- ✅ Erreur critique documentée (ex: données corrompues)
- ✅ Justification dans `user_action_log.details`
- ✅ Audit trail complet

**Exemple** :
```python
# Admin corrige erreur critique dans RAW
PUT /api/v1/raw/articles/{id}
{
    "title": "Correction erreur critique",
    "justification": "Données corrompues lors de la collecte, correction documentée"
}
# → Logged dans user_action_log avec details complets
```

### **GOLD : Modification Exceptionnelle**

**Conditions** :
- ✅ Erreur critique documentée (ex: validation incorrecte)
- ✅ Justification dans `user_action_log.details`
- ✅ Audit trail complet

**Exemple** :
```python
# Admin corrige erreur critique dans GOLD
PUT /api/v1/gold/articles/{id}
{
    "sentiment": "Correction validation",
    "justification": "Sentiment incorrect après validation, correction documentée"
}
# → Logged dans user_action_log avec details complets
```

---

## ✅ Avantages de cette Architecture

1. **Traçabilité** : RAW = preuve légale, historique complet
2. **Flexibilité** : SILVER = zone de travail, amélioration continue
3. **Stabilité** : GOLD = données validées, stables pour diffusion
4. **Sécurité** : Permissions strictes par zone
5. **Audit** : Toutes les actions loggées dans `user_action_log`

---

**Status** : ✅ **LOGIQUE MÉTIER DÉFINIE - PRÊT POUR IMPLÉMENTATION**
