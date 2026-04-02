# DataSens - Runbook publication modele HF

Ce guide documente la manip complete pour publier un modele fine-tune dans Hugging Face, le brancher dans DataSens, puis le faire evoluer proprement (versioning + rollback).

## 1) Prerequis

- Un compte Hugging Face avec droits ecriture sur le namespace cible.
- Un token HF avec permission `repo.write`.
- Un modele local entraine dans `models/`.
- Environnement Python du projet actif (`.venv` recommande).

## 2) Recuperer un token Hugging Face

1. Ouvrir: `https://huggingface.co/settings/tokens`
2. Creer un token (`New token`) avec droits ecriture.
3. Ne jamais commit ce token dans Git.

Utilisation recommande (session PowerShell):

```powershell
$env:HUGGINGFACE_API_KEY="hf_xxxxxxxxxxxxxxxxx"
```

## 3) Publier le meilleur checkpoint local

Le script detecte automatiquement le meilleur checkpoint local selon `eval_accuracy`, puis `eval_f1_macro`, puis `step`.

```powershell
python scripts/publish_best_model_to_hf.py --repo-id "ALMAGNUS/datasens-sentiment-fr"
```

Option tag de version:

```powershell
python scripts/publish_best_model_to_hf.py --repo-id "ALMAGNUS/datasens-sentiment-fr" --revision-tag "v1.1"
```

Option test sans push:

```powershell
python scripts/publish_best_model_to_hf.py --repo-id "ALMAGNUS/datasens-sentiment-fr" --dry-run
```

## 4) Brancher le modele publie dans l'application

Dans `.env`:

```env
SENTIMENT_FINETUNED_MODEL_PATH=ALMAGNUS/datasens-sentiment-fr
```

Puis redemarrer API + cockpit pour recharger la config.

## 5) Verification rapide apres publication

1. URL modele accessible:
   - `https://huggingface.co/ALMAGNUS/datasens-sentiment-fr`
2. Prediction via API/panel IA fonctionne.
3. Le modele actif affiche bien le repo HF attendu.
4. Le fichier `docs/e2/HF_MODEL_PUBLISH.json` contient la derniere publication (metriques + tag eventuel).

## 6) Mettre a jour le modele apres un nouvel entrainement

Process standard:

1. Entrainer un nouveau modele local.
2. Publier sur le meme `repo-id`.
3. Ajouter un tag de version (`v1.2`, `v1.3`, ...).
4. Verifier en inference applicative.

Commande type:

```powershell
python scripts/publish_best_model_to_hf.py --repo-id "ALMAGNUS/datasens-sentiment-fr" --revision-tag "v1.2"
```

## 7) Rollback rapide

Si regression, revenir a une version stable:

- soit en selectionnant la revision/tag stable cote Hub,
- soit en republiant le checkpoint local precedent avec un nouveau tag de restauration (ex: `v1.1-restore`).

## 8) Hygiene securite

- Si un token est expose: revoquer immediatement.
- Regenerer un nouveau token.
- Eviter de stocker des secrets dans les fichiers versionnes.
- Preferer une variable d'environnement session pour les operations de push.

