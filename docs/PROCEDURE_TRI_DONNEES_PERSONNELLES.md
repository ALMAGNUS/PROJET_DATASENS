# Procédure de tri des données personnelles — DataSens

**Conformité RGPD** — Détection, identification et suppression des données personnelles inutiles ou trop anciennes

**Document de référence** : Registre des traitements (REGISTRE_TRAITEMENTS_RGPD.md)  
**Dernière mise à jour** : 2026-02-12

---

## 1. Objectif

Cette procédure décrit comment :
- détecter les données personnelles stockées dans les bases DataSens ;
- identifier les données inutiles, obsolètes ou dépassant la durée de conservation ;
- supprimer ou anonymiser ces données conformément au RGPD.

---

## 2. Périmètre des données

| Table / Fichier | Données personnelles potentielles | Durée max (référence) |
|-----------------|-----------------------------------|-------------------------|
| `profils` | email, firstname, lastname | Comptes actifs : illimité. Comptes inactifs : 3 ans |
| `user_action_log` | profil_id, ip_address (lien avec profils) | 2 ans |
| `raw_data` | title, content, url (auteurs, noms cités dans le texte) | 3 ans |
| `synthetic_articles` (ZZDB) | author, content (données synthétiques) | Selon politique projet |

---

## 3. Procédure de détection

### 3.1 Table `profils`

**Données concernées** : email, firstname, lastname.

**Détection des comptes à traiter** :
- Comptes désactivés (`active = 0`) depuis plus de 3 ans ;
- Comptes sans connexion (`last_login` NULL) depuis plus de 2 ans (à définir selon politique).

**Requête SQL de repérage** :
```sql
-- Comptes désactivés depuis plus de 3 ans
SELECT profil_id, email, updated_at FROM profils
WHERE active = 0 AND updated_at < datetime('now', '-3 years');

-- Comptes jamais connectés depuis plus de 2 ans
SELECT profil_id, email, created_at FROM profils
WHERE last_login IS NULL AND created_at < datetime('now', '-2 years');
```

### 3.2 Table `user_action_log`

**Données concernées** : profil_id, ip_address.

**Détection** : Entrées de plus de 2 ans.

**Requête SQL** :
```sql
SELECT COUNT(*) FROM user_action_log
WHERE action_date < datetime('now', '-2 years');
```

### 3.3 Table `raw_data`

**Données concernées** : Contenu pouvant inclure noms, emails, informations identifiantes dans `title` ou `content`.

**Détection** :
- Articles dont `collected_at` ou `published_at` > 3 ans ;
- Champ `author` si présent dans le schéma (ZZDB) : à vérifier avant suppression.

**Requête SQL** :
```sql
SELECT raw_data_id, title, collected_at FROM raw_data
WHERE collected_at < datetime('now', '-3 years')
LIMIT 100;
```

### 3.4 Fichiers Parquet / Exports CSV

**Détection** : Mêmes règles que `raw_data` via la colonne de date (`collected_at`, `date`).

---

## 4. Procédure de suppression / anonymisation

### 4.1 Comptes utilisateurs (`profils`)

**Étapes** :
1. Lister les comptes éligibles (cf. section 3.1).
2. Vérifier qu’aucune obligation légale ne impose la conservation.
3. Supprimer les entrées liées dans `user_action_log` (ou anonymiser `profil_id`).
4. Supprimer le compte dans `profils`.

**Ordre recommandé** :
```sql
-- 1. Supprimer les logs liés (CASCADE si défini)
DELETE FROM user_action_log
WHERE profil_id IN (SELECT profil_id FROM profils WHERE active = 0 AND updated_at < datetime('now', '-3 years'));

-- 2. Supprimer les comptes
DELETE FROM profils
WHERE active = 0 AND updated_at < datetime('now', '-3 years');
```

### 4.2 Logs d’audit (`user_action_log`)

**Étapes** :
1. Identifier les logs de plus de 2 ans.
2. Supprimer ou anonymiser : remplacer `profil_id` par une valeur neutre (ex. -1) si la traçabilité globale doit être conservée.
3. Supprimer ou anonymiser `ip_address` pour les entrées anciennes.

**Exemple** :
```sql
DELETE FROM user_action_log
WHERE action_date < datetime('now', '-2 years');
```

### 4.3 Données de contenu (`raw_data`)

**Options** :
- **Suppression** : Supprimer les lignes concernées. Attention aux clés étrangères (`document_topic`, `model_output`).
- **Anonymisation** : Remplacer les champs identifiants dans `title`/`content` (ex. noms, emails) par des placeholders (ex. `[ANONYMISE]`). Cette option peut nécessiter un script dédié.

**Suppression avec contraintes** :
```sql
-- Supprimer d'abord les tables dépendantes
DELETE FROM model_output WHERE raw_data_id IN (
  SELECT raw_data_id FROM raw_data WHERE collected_at < datetime('now', '-3 years')
);
DELETE FROM document_topic WHERE raw_data_id IN (
  SELECT raw_data_id FROM raw_data WHERE collected_at < datetime('now', '-3 years')
);
DELETE FROM raw_data WHERE collected_at < datetime('now', '-3 years');
```

---

## 5. Fréquence d’exécution

| Traitement | Fréquence recommandée |
|------------|------------------------|
| Détection comptes `profils` | Trimestriel |
| Suppression `user_action_log` | Semestriel |
| Détection / tri `raw_data` | Annuel |

---

## 6. Traçabilité

Pour chaque exécution de la procédure :
- consigner la date ;
- consigner le nombre de lignes supprimées ou anonymisées par table ;
- archiver le registre des exécutions (fichier ou table dédiée).

**Exemple de log** :
```
2026-02-12 | user_action_log | DELETE | 150 lignes (action_date < 2024-02-12)
2026-02-12 | profils | DELETE | 2 comptes (inactifs > 3 ans)
```

---

## 7. Droits des personnes et demandes d’effacement

En cas de demande d’effacement (droit à l’oubli) :
1. Identifier toutes les occurrences de la personne (profils, logs, éventuellement contenu).
2. Appliquer les suppressions dans l’ordre : `user_action_log` → `profils`.
3. Pour le contenu : évaluer si une mention dans `raw_data` est identifiable ; si oui, supprimer ou anonymiser.
4. Confirmer l’effacement à la personne concernée sous 1 mois.

---

## 8. Révisions

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | 2026-02-12 | Création initiale |
