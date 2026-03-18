# Registre des traitements de données personnelles — DataSens

**Article 30 du RGPD** — Registre des activités de traitement

**Responsable du traitement** : [À compléter selon votre structure]  
**Dernière mise à jour** : 2026-02-12

---

## 1. Vue d'ensemble

Le projet DataSens collecte et traite des données pour l’analyse de sentiment et la veille médiatique. Ce registre décrit les traitements susceptibles de concerner des données personnelles.

---

## 2. Traitements identifiés

### Traitement T1 — Gestion des comptes utilisateurs (API E2)

| Champ | Détail |
|-------|--------|
| **Identifiant** | T1 |
| **Finalité** | Authentification et contrôle d’accès à l’API REST |
| **Base légale** | Exécution de contrat / intérêt légitime |
| **Données traitées** | email, prénom, nom, mot de passe (hashé bcrypt), rôle, adresse IP (logs de connexion) |
| **Catégories de personnes** | Utilisateurs internes de l’API (lecteurs, administrateurs) |
| **Destinataires** | Équipe projet DataSens uniquement |
| **Durée de conservation** | Comptes actifs : illimitée tant que nécessaire. Comptes désactivés : 3 ans. Logs : 2 ans |
| **Mesures de sécurité** | Hash bcrypt (12 rounds), JWT, RBAC, audit trail |
| **Localisation** | Base SQLite locale (table `profils`) |
| **Transferts hors UE** | Aucun |

---

### Traitement T2 — Journal d’audit des actions API

| Champ | Détail |
|-------|--------|
| **Identifiant** | T2 |
| **Finalité** | Traçabilité des accès aux données (audit, sécurité) |
| **Base légale** | Intérêt légitime (sécurité) / obligation légale |
| **Données traitées** | profil_id, type d’action, ressource accédée, adresse IP, date/heure |
| **Catégories de personnes** | Utilisateurs de l’API (lien indirect avec T1) |
| **Destinataires** | Équipe projet, auditeurs internes |
| **Durée de conservation** | 2 ans à compter de la date de l’action |
| **Mesures de sécurité** | Lecture restreinte, anonymisation possible après 1 an |
| **Localisation** | Base SQLite (table `user_action_log`) |
| **Transferts hors UE** | Aucun |

---

### Traitement T3 — Données de contenu (articles, flux)

| Champ | Détail |
|-------|--------|
| **Identifiant** | T3 |
| **Finalité** | Collecte et analyse de contenu médiatique (RSS, APIs, scraping) pour veille et sentiment |
| **Base légale** | Intérêt légitime (projet R&D / veille) |
| **Données traitées** | titre, contenu texte, URL, date de publication, auteur (si fourni par la source) |
| **Catégories de personnes** | Auteurs d’articles (données indirectement collectées) |
| **Destinataires** | Équipe projet, composants d’analyse (ML, API) |
| **Durée de conservation** | Données brutes : 3 ans. Exports : selon politique de suppression |
| **Mesures de sécurité** | Pas de données sensibles stockées intentionnellement ; filtrage et homogénéisation des formats |
| **Localisation** | SQLite (tables `raw_data`, `document_topic`, `model_output`), Parquet |
| **Transferts hors UE** | Aucun |

**Note** : Les contenus collectés (titres, textes, URLs) peuvent occasionnellement mentionner des personnes. Voir procédure de tri des données personnelles.

---

## 3. Droits des personnes concernées

| Droit | Modalités |
|-------|------------|
| **Accès** | Demande écrite au responsable du traitement |
| **Rectification** | Demande écrite au responsable du traitement |
| **Effacement** | Demande écrite ; effacement sous 1 mois sauf exception légale |
| **Portabilité** | Fourniture des données dans un format structuré (JSON/CSV) |
| **Opposition** | Possible sur la base de motifs légitimes |
| **Limitation** | Possible pendant la vérification d’une réclamation |

---

## 4. Référence à la procédure de tri

La procédure détaillée de détection et tri des données personnelles (y compris suppression et anonymisation) est décrite dans :

- **docs/PROCEDURE_TRI_DONNEES_PERSONNELLES.md**

---

## 5. Révisions

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | 2026-02-12 | Création initiale du registre |
