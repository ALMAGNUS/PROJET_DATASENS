# E2 - Soutenance (Q&A rapide)

## Pitch 60 secondes

E2 ajoute une couche IA operationnelle a DATASENS sans casser l'architecture E1.  
Le choix est hybride : inference locale HF pour le sentiment (cout, confidentialite, robustesse) et Mistral en complement pour les usages generatifs.  
L'integration est exposee via FastAPI, securisee en JWT/RBAC, et monitorable via Prometheus.  
La veille techno/reglementaire est outillee (sources qualifiees, syntheses automatiques), ce qui relie clairement les choix techniques aux contraintes reelles du projet.

---

## Questions frequentes et reponses

### 1) Pourquoi ne pas avoir entraine un modele from scratch ?
Le besoin E2 est l'integration d'un service IA preexistant. Le fine-tuning cible est plus rapide, moins couteux, et plus realiste en contexte projet.

### 2) Qu'est-ce qui prouve que le fine-tuning existe vraiment ?
Le script `scripts/finetune_sentiment.py` entraine/evalue un modele 3 classes, calcule `accuracy` et `f1 weighted`, puis sauvegarde le modele dans `models/...-sentiment-finetuned`.

### 3) Quelles donnees sont utilisees pour ce fine-tuning ?
`data/goldai/ia/train.parquet` et `data/goldai/ia/val.parquet` (generees via `scripts/create_ia_copy.py`).

### 4) Comment activer le modele fine-tune dans l'API ?
Ajouter dans `.env` :
`SENTIMENT_FINETUNED_MODEL_PATH=models/camembert-sentiment-finetuned`  
Puis redemarrer `python run_e2_api.py`.

### 5) Pourquoi local-first ?
Pour limiter l'exposition des donnees, maitriser les couts et garantir une execution meme sans dependance cloud.

### 6) A quoi sert Mistral alors ?
A des usages generatifs (chat, resume, insight), en complement de la prediction locale.

### 7) Comment prouvez-vous la securite API ?
JWT + RBAC dans `src/e2/auth/security.py` et dependencies permissions ; routes protegees ; tests API existants (`tests/test_e2_api.py`).

### 8) Quel monitoring est en place ?
Prometheus middleware : requetes, latence, erreurs, metriques de drift (`datasens_drift_*`).

### 9) Quelles limites vous assumez ?
Ironie, ambiguite contextuelle, variations lexicales. Ces limites sont documentees et pilotees par metriques.

### 10) Quelle innovation concrete proposee pour la suite ?
Un routeur SIG (Sentiment Intelligence Gateway) : local en premier, escalation cloud sur faible confiance, suivi des escalades en metriques.

---

## Commandes utiles (demo)

```bash
python run_e2_api.py
python scripts/run_e2_tests.py
python scripts/finetune_sentiment.py --model camembert --epochs 3 --batch-size 16
python scripts/finetune_sentiment.py --model camembert --eval-only
python scripts/veille_digest.py
```
