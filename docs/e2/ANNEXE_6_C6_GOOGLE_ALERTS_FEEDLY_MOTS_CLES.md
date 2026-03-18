# Annexe 6 (C6) - Google Alerts / Feedly / Mots-cles

## Objectif

Formaliser la veille manuelle complementaire a la veille automatisee, avec une liste explicite de mots-cles et thematiques.

## Perimetre

- Veille technologique IA/NLP francophone
- Veille integration API IA et bonnes pratiques MLOps
- Veille reglementaire (CNIL, AI Act, ANSSI)

## Sources de reference

- Version detaillee de travail: `docs/e2/ANNEXE_C6_SOURCES_MOTS_CLES.md`
- Version structuree JSON: `docs/e2/ANNEXE_C6_SOURCES_MOTS_CLES.json`

## Note de tri

Cette annexe est la version "prete soutenance" a citer dans le dossier principal.  
Les fichiers `ANNEXE_C6_*` restent les preuves techniques detaillees.

# Annexe 6 (rattachée à C6) - Liste de mots-clés Google Alerts / Feedly

## Liste principale recommandée (ciblée dossier E2)

Cette liste est la version de référence à présenter en soutenance. Elle est nettoyée, structurée et directement exploitable pour la veille manuelle.

1. `"analyse des sentiments" IA`
2. `"sentiment analysis" NLP model`
3. `"sentiment bias" AI`
4. `"emotion recognition NLP"`
5. `"AI Act" emotion recognition ban EU`
6. `"emotion manipulation" EU AI Act`
7. `"BERT sentiment classification"`
8. `"CamemBERT sentiment"`
9. `"FlauBERT sentiment"`
10. `"GoEmotions dataset"`
11. `"Llama sentiment analysis"`
12. `"Mistral AI sentiment model"`
13. `"LLM benchmark" evaluation`
14. `"MTEB leaderboard" sentence embedding`
15. `"Hugging Face leaderboard" sentiment`
16. `"Inria" CamemBERT FlauBERT NLP`
17. `"CNIL" intelligence artificielle RGPD`
18. `"ANSSI" intelligence artificielle sécurité`
19. `"DAMA DMBOK" gouvernance des données`
20. `"CIA triad" confidentiality integrity availability AI`
21. `"DICT" disponibilité intégrité confidentialité traçabilité`
22. `"ITIL" IA exploitation`
23. `"Apache Spark" partitioning parquet`
24. `"Polars" Spark big data pipeline`

## Liste utilisateur conservée (historique de veille, optionnel)

Cette section conserve la liste brute initiale pour traçabilité. Elle n'est pas obligatoire dans la version finale du dossier si tu veux un rendu plus lisible.

affective computing  
AI Act emotion recognition  
analyse des sentiments en IA  
BERT sentiment  
BIG DATA  
Confidentiality Integrity Availability CIA  
DAMA DMBOK gouvernance des données  
DATA  
DATA LAKE  
Disponibilité/Intégrité/Confidentialité/Tracabilité DICT  
emotion manipulation ban EU  
emotion recognition NLP  
GoEmotions dataset  
ia  
IA générative  
inria  
inria camembert  
inria flaubert  
ITIL  
Llama sentiment  
LLM  
Mistral AI emotion  
Pandas Polars Spark  
Partitionner ses fichiers big data spark  
saclAI  
sentiment analysis AI  
sentiment bias AI  
SPARK

## Bonnes pratiques de réglage

Limiter chaque alerte à 1-2 concepts maximum améliore la pertinence.  
Créer des alertes séparées par thème (sentiment, benchmark, réglementaire, gouvernance) facilite la traçabilité dans le dossier E2.  
Pour les termes trop larges (`ia`, `DATA`, `LLM`, `BIG DATA`), préférer des requêtes composées avec guillemets et opérateurs (`AND`, `OR`).
