# Backlog technique — DataSens

> Dette technique et améliorations identifiées après le run quotidien du 2026-04-18.
> Aucun de ces points n'est bloquant : le pipeline tourne, la cohérence est OK, le dataset IA est complet.

---

## 1. API INSEE — migration OAuth2

**Contexte.** L'endpoint OAuth historique `https://api.insee.fr/token` renvoie `HTTP 404` depuis 2026 :

```
WARNING | e1.core:_insee_get_bearer_token | INSEE OAuth token: HTTP 404
— endpoint deprecated. Definir INSEE_TOKEN_URL dans .env (voir portail-api.insee.fr).
```

**État actuel.**
- Code `src/e1/core.py::_insee_get_bearer_token` : endpoint OAuth rendu **configurable** via `INSEE_TOKEN_URL` (commit phase 14). Le defaut reste l'ancien endpoint pour retro-compatibilite ; il suffit de le surcharger dans `.env` des que le nouveau portail le publie.
- `.env.example` : variable `INSEE_TOKEN_URL` documentee.
- Le fallback `_extract_insee_indicators` sur le site public recupere 35 indicateurs par run (resilience OK), sans auth ni quotas negocies.

**Action restante.**
- Creer un compte sur `https://portail-api.insee.fr/`.
- Noter l'URL exacte du token endpoint (documentation OAuth du portail).
- Renseigner dans `.env` :
  ```
  INSEE_TOKEN_URL=https://portail-api.insee.fr/token   # a confirmer
  INSEE_CONSUMER_KEY=...
  INSEE_CONSUMER_SECRET=...
  ```
- Optionnel : supprimer le fallback une fois la nouvelle API stabilisee.

**Priorité.** P2 — fonctionnel actuellement grâce au fallback.

**Fichiers concernés.** `src/e1/core.py`, `.env.example`.

---

## 2. Modèle `sentiment_fr-sentiment-finetuned` — tokenizer « incomplet »

**Statut : diagnostic clarifie, pas d'action requise.**

**Contexte.** Le script `scripts/backup_parquet_to_mongo.py` signalait l'absence du fichier `sentencepiece.bpe.model` pour `sentiment_fr-sentiment-finetuned`, alors que `camembert-sentiment-finetuned` le contient (~0.77 MB).

**Diagnostic.** Ce fichier est **optionnel** et specifique aux tokenizers SentencePiece (CamemBERT, XLM-RoBERTa). Les modeles bases sur DistilBERT/BERT utilisent `vocab.txt` a la place. L'absence n'est donc pas une erreur fonctionnelle.

**Action effectuee (commit phase 13).** Le script de backup distingue desormais :

- `required_model_files` — `model.safetensors`, `config.json`, `tokenizer_config.json` (log `MISSING` si absent).
- `optional_model_files` — `tokenizer.json`, `special_tokens_map.json`, `sentencepiece.bpe.model`, `spiece.model`, `vocab.txt`, `vocab.json`, `merges.txt` (log `OPTIONAL absent`).

**Action restante (optionnelle).** Verifier que `tokenizer_config.json` + le fichier vocab approprie sont bien presents pour `sentiment_fr-sentiment-finetuned`. Si oui, le modele est utilisable tel quel via `AutoTokenizer.from_pretrained(...)`.

**Priorité.** P3 — cosmetique, resolu cote outillage.

---

## 3. Confiance moyenne des topics — 0.12

**Statut : documente.**

**Contexte.** Le dashboard affiche `Confiance moyenne: 0.12` sur ~48 000 articles tagges.

**Explication.** Valeur **structurellement basse** : moyenne des liaisons `document_topic` (jusqu'a 2 par article sur 20 topics), incluant systematiquement les seconds topics faibles et les assignations par defaut `autre` (0.3). Ne traduit pas une erreur du modele.

**Action effectuee (commit phase 12).**
- Section `2.4 Interpreter la « confiance moyenne »` ajoutee a `docs/Dossier_E1_topics_sentiments+scripts.md`.
- Ligne d'explication inline ajoutee dans la sortie console de `src/dashboard.py` (pointe vers la doc).

**Action restante (optionnelle).** Complementer la moyenne brute par deux metriques plus parlantes :
- Moyenne du `confidence_score` **top-1 par article** (seulement le meilleur topic).
- Part des articles avec `topic_1 != "autre"` (couverture effective).

**Priorité.** P3 — amelioration de lisibilite, pas de correction.

**Fichiers concernés.** `src/dashboard.py`, `docs/Dossier_E1_topics_sentiments+scripts.md`.

---

## Améliorations transverses

- **`docker-compose.yml`** — **traite (commit phase 11)**. Le service `datasens-e1` (one-shot) est passe a `restart: "no"` avec un commentaire explicatif. Les autres services (metrics, prometheus, API, mongodb, uptime-kuma, grafana) conservent `unless-stopped` (services permanents).
- **Nettoyage manuel** : voir `GUIDE_NETTOYAGE_MANUEL.md` (non versionne) pour la liste des fichiers candidats a suppression.
- **Inventaire** : voir `INVENTAIRE_PROJET.md` (non versionne) pour l'etat des lieux complet.

---

*Dernière mise à jour : 2026-04-18 (phases 11-14 traitees).*
