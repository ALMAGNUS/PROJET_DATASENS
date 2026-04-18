# Backlog technique — DataSens

> Dette technique et améliorations identifiées après le run quotidien du 2026-04-18.
> Aucun de ces points n'est bloquant : le pipeline tourne, la cohérence est OK, le dataset IA est complet.

---

## 1. API INSEE — migration OAuth2

**Contexte.** L'endpoint OAuth historique renvoie `HTTP 404` :

```
WARNING | e1.core:_insee_get_bearer_token | INSEE OAuth token: HTTP 404
— url deprecated, visit https://portail-api.insee.fr/
```

**État actuel.** Le fallback `_extract_insee_indicators` sur le site public récupère 35 indicateurs par run. La source reste donc alimentée (résilience OK), mais sans authentification ni quotas négociés.

**Action.**
- Créer un compte sur `https://portail-api.insee.fr/`
- Mettre à jour `_insee_get_bearer_token` avec le nouvel endpoint OAuth2
- Ajouter les credentials au `.env` (variables déjà prévues : `INSEE_CLIENT_ID`, `INSEE_CLIENT_SECRET`)
- Supprimer le fallback une fois la nouvelle API stabilisée

**Priorité.** P2 — fonctionnel actuellement grâce au fallback.

**Fichiers concernés.** `src/e1/core.py` (`_insee_get_bearer_token`, `_extract_insee_indicators`), `.env.example`.

---

## 2. Modèle `sentiment_fr-sentiment-finetuned` — tokenizer incomplet

**Contexte.** Le script de backup MongoDB signale l'absence du fichier `sentencepiece.bpe.model` pour le second modèle fine-tuné :

```
-- ABSENT  sentencepiece.bpe.model  (modèle sentiment_fr-sentiment-finetuned)
```

Le modèle `camembert-sentiment-finetuned` possède bien le sien (0.77 MB).

**Impact potentiel.** Une tentative de chargement de ce modèle via `AutoTokenizer.from_pretrained(...)` peut échouer selon la classe de tokenizer demandée. Pas de problème pour le run quotidien car l'inférence s'appuie actuellement sur `camembert-sentiment-finetuned`.

**Action.**
- Vérifier le répertoire du modèle (`models/sentiment_fr-sentiment-finetuned/`)
- Ré-exporter le tokenizer complet depuis le notebook/training script :
  ```python
  tokenizer.save_pretrained("models/sentiment_fr-sentiment-finetuned/")
  ```
- Re-lancer le backup MongoDB pour confirmer la présence (STORED attendu)

**Priorité.** P3 — cosmétique tant que ce modèle n'est pas utilisé en inférence.

---

## 3. Confiance moyenne des topics — 0.12

**Contexte.** Le dashboard affiche `Confiance moyenne: 0.12` sur 48 151 articles taggés. Distribution cohérente mais score bas.

**Explication.** Comportement attendu d'un classifier zero-shot multi-classes sur 20 topics (probabilité diluée mécaniquement). Ne traduit pas une erreur du modèle.

**Action (optionnelle).**
- Documenter cette valeur dans le `README` ou dans la doc du pipeline comme « métrique structurelle liée au multi-label, non à la qualité du modèle »
- Alternative : remplacer la moyenne brute par la moyenne du top-1 par article, plus représentative
- Alternative : réduire la taxonomie à 8-10 topics majeurs, ce qui mécaniquement remonterait la confiance moyenne

**Priorité.** P3 — amélioration de lisibilité, pas de correction.

**Fichiers concernés.** `src/dashboard.py` (calcul de la moyenne), doc topics.

---

## Améliorations transverses (déjà identifiées)

- **`docker-compose.yml`** : retirer `restart: unless-stopped` du service `datasens-e1` ou le remplacer par `on-failure:3`, pour éviter toute boucle de restart en cas de crash répété (retour d'expérience du 2026-04-18).
- **Nettoyage manuel** : voir `GUIDE_NETTOYAGE_MANUEL.md` (non versionné) pour la liste des fichiers candidats à suppression.
- **Inventaire** : voir `INVENTAIRE_PROJET.md` (non versionné) pour l'état des lieux complet.

---

*Dernière mise à jour : 2026-04-18*
