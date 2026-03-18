# BLOC E2 - Integration de services d'Intelligence Artificielle

Projet : DATASENS  
Candidat : Alan Jaffre

## Introduction - Positionnement du bloc E2 dans DATASENS

Le projet DATASENS vise l'analyse des sentiments a partir de sources heterogenes afin de produire des indicateurs exploitables. Le bloc E1 a pose les fondations de collecte, de structuration et de stockage des donnees. Le bloc E2 prolonge ce socle en introduisant l'IA comme levier de transformation de donnees textuelles en informations interpretable par des utilisateurs metier.

L'objectif E2 n'est pas d'entrainer un modele from scratch, mais d'identifier, evaluer, parametrer et integrer des services IA preexistants de maniere robuste et justifiable. Cette posture est pleinement alignée avec un contexte professionnel : maitrise du risque, explicabilite des choix, traçabilite des decisions techniques.

Socle E2 constate dans le code :
- API FastAPI : `run_e2_api.py`, `src/e2/api/main.py`
- Prefix API : `"/api/v1"` (config)
- Documentation : `/docs`, `/redoc`, `/openapi.json`
- Securite : `src/e2/auth/security.py` (bcrypt + JWT), dependances RBAC
- IA : `src/e2/api/routes/ai.py`, `src/e3/mistral/service.py`, `src/ml/inference/local_hf_service.py`
- Monitoring : `src/e2/api/middleware/prometheus.py`

---

## A3 - Accompagner le choix et l'integration d'un service IA preexistant

Le besoin IA de DATASENS est concret : analyser automatiquement des textes en francais, fournir des sorties fiables (sentiment + confiance), et exposer ces fonctions via API de maniere securisee et monitorable.

L'architecture implementee repond deja a ce besoin avec une approche hybride :
- **Inference locale HF** pour les usages coeur (maitrise cout, confidentialite, disponibilite),
- **Mistral API** pour les usages generatifs (chat, resume, assistance).

L'integration est operationnelle dans les routes :
- `/api/v1/ai/status`
- `/api/v1/ai/chat`
- `/api/v1/ai/summarize`
- `/api/v1/ai/sentiment`
- `/api/v1/ai/predict`
- `/api/v1/ai/insight`

Le service local (`src/ml/inference/local_hf_service.py`) calcule deja des signaux exploitables (`label`, `confidence`, `sentiment_score`), ce qui permet une industrialisation progressive sans rupture de stack.

---

## C6 - Veille technologique et reglementaire

### C6.1 Thematiques de veille retenues

La veille E2 est centree sur trois axes :
- modeles NLP francophones pour sentiment,
- patterns d'integration IA dans une API legere et CPU-first,
- cadre reglementaire IA et protection des donnees.

Preuves internes :
- `VEILLE_SENTIMENT_MODELS.md`
- `scripts/veille_sources.json`
- `scripts/veille_digest.py`
- sortie auto : `docs/veille/veille_2026-03-09.md`

### C6.2 Organisation, planification et outillage

La veille est structuree, pas opportuniste :
- configuration des flux dans `scripts/veille_sources.json`,
- aggregation RSS via `feedparser` dans `scripts/veille_digest.py`,
- generation de synthese Markdown versionnee dans `docs/veille/`.

Cette organisation assure la traçabilite entre information collecte et decision technique.

### C6.3 Fiabilite des sources et actualite recente utile

Les sources sont qualifiees dans la config (`reliability: high`) et couvrent le spectre technique et reglementaire : OpenAI, Mistral, Hugging Face, ANSSI, CNIL.

Points d'actualite integres (sources officielles) :
- AI Act / GPAI : obligations applicables depuis le 2 aout 2025 (transparence, documentation, copyright policy), cadre d'application et calendrier de mise en conformite.
  - [General-purpose AI obligations under the AI Act](https://digital-strategy.ec.europa.eu/en/factpages/general-purpose-ai-obligations-under-ai-act)
  - [Guidelines for providers of GPAI models](https://digital-strategy.ec.europa.eu/en/policies/guidelines-gpai-providers)
- MTEB : referentiel utile pour evaluer les modeles d'embeddings (complement strategique au sentiment pur).
  - [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)

---

## C7 - Identification et benchmark des services IA

### C7.1 Problematique et contraintes projet

Problematique fonctionnelle :
- classer le sentiment sur des textes heterogenes en francais,
- exposer des fonctions d'assistance (resume, insight),
- conserver une lecture claire de la fiabilite des predictions.

Contraintes structurantes :
- execution CPU sans dependance GPU obligatoire,
- cout maitrise,
- continuite de service meme en mode deconnecte cloud,
- minimisation des flux externes de donnees.

### C7.2 Benchmark realise et decision technique

Le benchmark est outille dans `scripts/ai_benchmark.py` et produit :
- `docs/e2/AI_BENCHMARK.md`
- `docs/e2/AI_REQUIREMENTS.md`

Comparatif operationnel retenu :
- **Local HF** (CamemBERT/FlauBERT/sentiment_fr) : maitrise des donnees, robustesse locale.
- **API Cloud (Mistral)** : valeur ajoutee generative.

Decision E2 justifiee :
- moteur principal pour le sentiment : **Local HF**,
- moteur secondaire pour enrichissement generatif : **Mistral**.

Ce choix est cohérent avec le code actuel et avec les contraintes de deploiement.

---

## C8 - Parametrage et integration d'un service IA

### C8.1 Environnement d'execution, acces et dependances

Dependances cle presentes dans `requirements.txt` :
- `transformers`
- `torch`
- `mistralai`

Parametrage present dans `.env.example` :
- `SENTIMENT_FR_MODEL_PATH`
- `CAMEMBERT_MODEL_PATH`
- `FLAUBERT_MODEL_PATH`
- `INFERENCE_BATCH_SIZE`
- `INFERENCE_MAX_LENGTH`
- `TORCH_NUM_THREADS`
- `MISTRAL_API_KEY`

### C8.2 Integration dans l'architecture applicative

- lancement API : `python run_e2_api.py`
- securite : JWT + RBAC (`src/e2/auth/security.py`, dependances de permissions)
- route de verification service cloud : `/api/v1/ai/status`
- exploitation API : `/redoc`, `/docs`, `/openapi.json`

### C8.3 Monitoring, limites et pilotage

Le middleware Prometheus (`src/e2/api/middleware/prometheus.py`) expose deja :
- `datasens_e2_api_requests_total`
- `datasens_e2_api_request_duration_seconds`
- `datasens_e2_api_errors_total`
- `datasens_drift_*`

Ces metriques permettent un suivi pragmatique : latence, erreurs, trafic, derive.

Limites connues et assumees :
- ambiguite semantique et ironie (limite classique NLP),
- variabilite selon domaine lexical,
- besoin d'un cadrage continu des seuils de confiance.

---

## Proposition "a la pointe" sans hallucination : Sentiment Intelligence Gateway (SIG)

Objectif : ajouter une couche d'orchestration, sans casser l'existant.

Principe :
1. inference locale HF en premier passage,
2. escalation cloud uniquement en cas de faible confiance,
3. journalisation et metriques d'escalade pour boucle d'amelioration.

Pourquoi ce choix est pro et realiste :
- reutilise les composants deja presents,
- optimise cout/qualite,
- renforce la confidentialite par defaut,
- facilite la gouvernance technique et reglementaire.

Evolutions incrementales recommandees :
1. endpoint routeur (`/api/v1/ai/sentiment-router`),
2. seuil paramétrable (`SENTIMENT_GATE_THRESHOLD`),
3. metriques dediees (taux escalade, latence locale/cloud, erreurs d'escalade).

---

## Conclusion

Le bloc E2 de DATASENS est techniquement coherent et deja bien avance :
- choix IA argumente par contraintes reelles,
- integration API securisee et monitorable,
- veille outillee et traçable,
- trajectoire d'innovation claire sans sur-promesse.

La strategie la plus efficace est d'industrialiser l'orchestration existante plutot que d'ajouter des briques non maitrisées : local-first, cloud sur exception utile, pilotage par metriques, et veille reglementaire continue.

---

## Annexes - Preuves internes

- `VEILLE_SENTIMENT_MODELS.md`
- `docs/e2/AI_BENCHMARK.md`
- `docs/e2/AI_REQUIREMENTS.md`
- `scripts/veille_sources.json`
- `scripts/veille_digest.py`
- `docs/veille/veille_2026-03-09.md`
- `src/e2/api/routes/ai.py`
- `src/e3/mistral/service.py`
- `src/ml/inference/local_hf_service.py`
- `src/e2/api/middleware/prometheus.py`
- `src/e2/auth/security.py`
- `tests/test_e2_api.py`
