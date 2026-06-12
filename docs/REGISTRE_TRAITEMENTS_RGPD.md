# Registre des traitements de données à caractère personnel — DataSens

> Registre tenu au titre de l'article **30 du RGPD** (Règlement UE 2016/679).
> Document de référence pour la conformité du projet DATASENS.
> Procédure opérationnelle associée : [`PROCEDURE_TRI_DONNEES_PERSONNELLES.md`](PROCEDURE_TRI_DONNEES_PERSONNELLES.md).

| Champ | Valeur |
|---|---|
| **Responsable du traitement** | Porteur du projet DATASENS (contexte de formation / certification) |
| **Contact / DPO** | Référent projet (à compléter avec l'adresse de contact réelle) |
| **Date de création du registre** | 2026-06-12 |
| **Dernière mise à jour** | 2026-06-12 |
| **Version** | 1.0 |

---

## 1. Vue d'ensemble des traitements

| N° | Traitement | Finalité principale | Base légale | Données personnelles |
|----|-----------|---------------------|-------------|----------------------|
| T1 | Gestion des comptes & authentification | Contrôler l'accès à l'API/cockpit (JWT/RBAC) | Intérêt légitime / mesures pré-contractuelles | email, nom, prénom, mot de passe (haché) |
| T2 | Journalisation & sécurité (audit) | Traçabilité des accès, détection d'abus | Intérêt légitime / obligation de sécurité (art. 32) | identifiant compte, adresse IP, horodatage, action |
| T3 | Collecte & analyse d'opinion publique | Analyser le sentiment/les thèmes de contenus publics | Intérêt légitime (art. 6.1.f) | données potentiellement identifiantes citées dans des contenus **publics** (noms, pseudos, auteurs) |

---

## 2. Fiche détaillée par traitement

### T1 — Gestion des comptes & authentification

| Élément | Détail |
|---|---|
| **Finalité** | Authentifier les utilisateurs et gérer leurs droits d'accès par zone (viewer / analyst / admin) |
| **Base légale** | Intérêt légitime (sécuriser l'accès) ; mesures pré-contractuelles pour un usage applicatif |
| **Personnes concernées** | Utilisateurs autorisés de l'application (analystes, administrateurs) |
| **Catégories de données** | email, prénom, nom, mot de passe **haché (bcrypt)**, rôle, dates création/maj, dernière connexion |
| **Source** | Saisie directe lors de la création de compte |
| **Destinataires** | Équipe projet uniquement ; aucune diffusion externe |
| **Transfert hors UE** | Aucun |
| **Durée de conservation** | Comptes actifs : durée d'utilisation ; comptes inactifs/désactivés : **3 ans** puis suppression |
| **Stockage** | Table `profils` (SQLite, poste unique) |
| **Mesures de sécurité** | Mot de passe haché bcrypt (`passlib`), authentification JWT court (`python-jose`), RBAC par zone, pas d'API publique de gestion utilisateurs |

### T2 — Journalisation & sécurité (audit trail)

| Élément | Détail |
|---|---|
| **Finalité** | Tracer les actions/accès pour la sécurité et la détection d'anomalies (brute-force, abus) |
| **Base légale** | Intérêt légitime + obligation de sécurité (art. 32 RGPD) |
| **Personnes concernées** | Utilisateurs authentifiés de l'application |
| **Catégories de données** | identifiant de compte (`profil_id`), adresse IP, horodatage, type d'action |
| **Source** | Générée automatiquement par l'API à chaque requête |
| **Destinataires** | Équipe projet (administration/monitoring) |
| **Transfert hors UE** | Aucun |
| **Durée de conservation** | **2 ans** (puis suppression ou anonymisation du `profil_id`/IP) |
| **Stockage** | Tables `user_action_log` / `audit_log` (SQLite) |
| **Mesures de sécurité** | Accès restreint, anonymisation possible des entrées anciennes (cf. procédure §4.2) |

### T3 — Collecte & analyse d'opinion publique

| Élément | Détail |
|---|---|
| **Finalité** | Constituer un corpus de contenus **publics** (presse, RSS, avis, réseaux, open data) pour l'analyse de sentiment et de thèmes |
| **Base légale** | Intérêt légitime (art. 6.1.f) — analyse d'opinion à partir de sources publiques/ouvertes |
| **Personnes concernées** | Auteurs/personnes éventuellement citées ou identifiables dans des contenus publiés (journalistes, auteurs d'avis, pseudos de forums) |
| **Catégories de données** | `title`, `content`, `url` pouvant contenir des noms, pseudonymes ou informations identifiantes présentes dans la source publique |
| **Source** | Sources publiques : RSS, API officielles (INSEE, OpenWeather, data.gouv…), scraping de pages publiques, datasets ouverts (Kaggle, GDELT), CSV interne |
| **Destinataires** | Équipe projet ; agrégats/statistiques de sentiment exposés via l'API/cockpit |
| **Transfert hors UE** | Aucun stockage hors UE ; certaines sources sont hébergées hors UE mais seules des données **publiques** sont collectées |
| **Durée de conservation** | **3 ans** à compter de la collecte (`collected_at`), puis tri/suppression/anonymisation |
| **Stockage** | Table `raw_data` (SQLite) + couches Parquet RAW/SILVER/GOLD/GoldAI + backup GridFS MongoDB |
| **Mesures de sécurité** | Pas de catégories particulières (art. 9) volontairement recherchées ; anonymisation possible (`[ANONYMISE]`) ; suppression sous contraintes de clés étrangères (cf. procédure §4.3) |

---

## 3. Données NON collectées (minimisation)

Conformément au principe de **minimisation** (art. 5.1.c) :
- Aucune donnée de catégorie particulière (santé, opinions politiques au sens nominatif,
  religion, orientation…) n'est **recherchée** ni indexée volontairement.
- Aucun profilage individuel : l'analyse porte sur des **agrégats** de sentiment/thèmes,
  pas sur le suivi d'une personne identifiée.
- Aucune donnée de paiement, aucune donnée de mineurs ciblée.

---

## 4. Droits des personnes

| Droit | Mise en œuvre |
|---|---|
| Accès / rectification | Sur demande ; identification des occurrences (profils, logs, contenu) |
| Effacement (droit à l'oubli) | Procédure dédiée (`PROCEDURE_TRI_DONNEES_PERSONNELLES.md` §7), réponse sous 1 mois |
| Opposition | Retrait/anonymisation de la donnée concernée dans `raw_data` |
| Limitation | Gel de la donnée (exclusion des exports/branches IA) |

Ordre de suppression respectant l'intégrité référentielle :
`model_output` → `document_topic` → `raw_data` ; et `user_action_log` → `profils`.

---

## 5. Mesures de sécurité transverses (art. 32)

- **Authentification** : JWT court + bcrypt sur les mots de passe.
- **Habilitations** : RBAC par zone (viewer / analyst / admin).
- **Isolation** : frontières E1/E2/E3 ; l'API E2 ne mute pas les données SILVER (501 par design).
- **Traçabilité** : audit trail des requêtes API.
- **Supervision** : métriques Prometheus dont échecs d'authentification (cf. `METRIQUES_SEUILS_ALERTES.md`).
- **Sauvegarde** : backup GridFS MongoDB des couches analytiques.

---

## 6. Révisions

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | 2026-06-12 | Création du registre (traitements T1, T2, T3) |

---

*Registre à réviser à chaque évolution des traitements (nouvelle source, nouvelle finalité,
nouveau destinataire) et au minimum une fois par an.*
