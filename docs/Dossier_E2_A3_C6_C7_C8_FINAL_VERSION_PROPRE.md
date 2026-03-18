# BLOC E2 - Intégration de services d'Intelligence Artificielle

Projet : DATASENS  
Candidat : Alan Jaffre

## Introduction

Le projet DATASENS vise l'analyse de contenus textuels francophones issus de sources hétérogènes afin de produire des indicateurs de sentiment exploitables dans un contexte métier. Le bloc E1 a établi le socle de collecte, de structuration et de stockage des données. Le bloc E2 s'inscrit dans cette continuité en ajoutant une couche d'intelligence artificielle orientée usage, avec un objectif de transformation fiable des données textuelles en informations directement actionnables.

La démarche retenue est volontairement ingénieriale : il ne s'agit pas de réentraîner un modèle propriétaire de bout en bout, mais de sélectionner des services IA existants, de les comparer sur des critères explicites, de les intégrer proprement dans l'architecture applicative, puis de les piloter en production via des métriques. Cette posture réduit le risque projet, maîtrise les coûts d'exploitation et garantit une trajectoire d'amélioration continue, traçable et reproductible.

Sur le plan technique, ce positionnement est déjà matérialisé dans le code. L'API est portée par `run_e2_api.py` et `src/e2/api/main.py`, la sécurité est gérée par JWT/RBAC dans `src/e2/auth/security.py`, la couche IA est orchestrée par `src/e2/api/routes/ai.py`, l'inférence locale est assurée dans `src/ml/inference/local_hf_service.py`, et l'observabilité est apportée par `src/e2/api/middleware/prometheus.py`.

L'enjeu du bloc E2 n'est donc pas uniquement technologique ; il est également méthodologique. Le livrable attendu à ce niveau de certification consiste à démontrer la capacité à transformer un besoin métier ambigu en une architecture IA explicable, testable, exploitable et gouvernable. Le dossier est rédigé dans cette perspective : chaque choix est relié à une contrainte, chaque contrainte à un arbitrage, et chaque arbitrage à une preuve d'implémentation.

## A3. Accompagner le choix et l'intégration d'un service d'intelligence artificielle préexistant

### A3.1 Cadrage du besoin fonctionnel et technique

Le besoin métier adressé en E2 est double. D'une part, classifier automatiquement le sentiment de textes en français avec un niveau de confiance exploitable. D'autre part, proposer des fonctionnalités d'assistance à la lecture comme le résumé et l'insight conversationnel. Le besoin d'intégration impose que ces capacités soient accessibles via API, sécurisées, traçables et observables.

Le cadrage technique écarte un choix monolithique unique. Les contraintes de contexte imposent une logique CPU-first, un contrôle des coûts, une limitation des transferts de données vers des tiers et une maintenabilité compatible avec une exploitation continue. Le service IA visé doit donc s'intégrer dans l'existant sans rupture de stack.

### A3.2 Démarche de sélection et décision d'architecture

La stratégie adoptée repose sur un moteur local dédié au sentiment. Le cœur du traitement est confié à des modèles Hugging Face exécutés en local, afin de conserver la maîtrise des données, la prédictibilité des coûts et la disponibilité de service.

Cette décision répond à une logique de robustesse opérationnelle. Le local est privilégié dès lors que la tâche est déterministe et mesurable, notamment sur le sentiment. Le compromis est robuste car il réduit la dépendance à des services externes sur la chaîne critique.

L'arbitrage a également été pensé sous l'angle du cycle de vie opérationnel. Un moteur local est plus simple à fiabiliser dans la durée, car son comportement est moins dépendant d'évolutions externes d'API, de quotas ou de politique tarifaire. Cette orientation réduit la variabilité du service sur la chaîne critique de production.

### A3.3 Intégration opérationnelle dans l'API

L'intégration est concrète et exploitable immédiatement. Les points d'entrée `/api/v1/ai/status`, `/api/v1/ai/sentiment` et `/api/v1/ai/predict` démontrent la couverture fonctionnelle du bloc E2 et permettent de valider la chaîne de scoring local sans ambiguïté.

Le service local fournit des sorties structurées comme `label`, `confidence` et `sentiment_score`, ce qui constitue un socle solide pour la qualification des résultats et le pilotage qualité. Sur le plan architecture, ce format de sortie est essentiel car il permet de raisonner en seuils, de mesurer la dérive et d'implémenter des règles d'escalade maîtrisées.

### A3.4 Valeur apportée et trajectoire d'évolution

L'apport principal d'A3 n'est pas seulement d'avoir intégré un service IA, mais d'avoir conçu une intégration gouvernable. Le bloc E2 prépare explicitement une montée en maturité du moteur local par itérations (benchmark, ajustements de paramètres, fine-tuning), sans réécriture massive.

En termes d'impact projet, cette approche permet de traiter progressivement les points les plus sensibles : stabilisation des seuils de confiance, réduction des faux positifs sur les textes ambigus, et suivi continu de la qualité de prédiction. La valeur ajoutée n'est pas une promesse abstraite d'IA "plus performante", mais une capacité concrète à améliorer la qualité perçue sans dérive de coûts.

## C6. Veille Technologique et Réglementaire

### C6.1 Définir la ou les thématiques de veille

La veille est structurée autour de trois thématiques directement reliées aux décisions E2. La première concerne les modèles NLP francophones appliqués au sentiment. La deuxième porte sur les patterns d'intégration IA dans des APIs légères orientées CPU-first. La troisième traite du cadre réglementaire, en particulier les obligations liées à l'IA générative et à la protection des données.

Ce découpage évite une veille "catalogue" sans impact projet. Chaque thématique est reliée à une décision concrète : choix des modèles, design d'intégration, exigences de conformité et de traçabilité.

### C6.2 Planifier les temps dédiés à la veille

La veille est pensée comme un processus récurrent et non comme une tâche ponctuelle. Le rythme de production des synthèses versionnées dans `docs/veille/` est un mécanisme de planification implicite et vérifiable. Cette approche garantit que la veille alimente la décision tout au long du cycle de réalisation, y compris lors des phases de stabilisation.

D'un point de vue gouvernance, cette planification continue permet de réduire le risque de décision obsolète, en particulier sur les sujets réglementaires et sur l'évolution rapide des services IA externes.

La planification s'articule autour de deux temporalités complémentaires. Une temporalité de surveillance, courte, capte les signaux faibles et les changements de contexte. Une temporalité de décision, plus espacée, traduit ces signaux en actions sur l'architecture, la documentation et les règles d'exploitation. Cette distinction évite de confondre "actualité" et "priorité projet".

### C6.3 Choisir un outil d'agrégation des flux d'informations et d'actualités

L'outil d'agrégation retenu est un pipeline scripté interne, fondé sur `scripts/veille_sources.json` pour la configuration des flux et `scripts/veille_digest.py` pour l'agrégation RSS et la génération de synthèses. Ce choix présente un avantage net par rapport à un outil externe non maîtrisé : la reproductibilité, la versionnabilité et l'intégration native au dépôt.

Ce choix technique est cohérent avec une logique d'industrialisation. L'agrégation devient un composant du projet, auditable et modifiable, plutôt qu'un artefact isolé dépendant d'un service tiers.

### C6.4 Choisir un outil de partage ou communication des synthèses des informations collectées

Le partage est assuré par des livrables Markdown versionnés dans le dépôt, en particulier `docs/veille/veille_2026-03-09.md`. Ce format permet une diffusion immédiate auprès des parties prenantes techniques, une relecture asynchrone, et une historisation explicite des décisions informées par la veille.

Le choix du Markdown versionné répond à un besoin de traçabilité de bout en bout, depuis la source brute jusqu'à la synthèse contextualisée, puis jusqu'à l'impact sur les choix d'architecture.

### C6.5 Identifier les sources et les flux d'informations utiles à la veille thématique visée

Les sources retenues couvrent le spectre nécessaire au projet. Sur le volet technologique, Hugging Face, arXiv et les flux de benchmark NLP permettent de suivre les évolutions de capacités, de modèles et d'écosystèmes. Sur le volet réglementaire, ANSSI et CNIL apportent une base fiable pour la conformité et les bonnes pratiques de sécurité.

Cette cartographie de sources est définie dans `scripts/veille_sources.json` et aligne directement les flux collectés avec les trois thématiques de veille retenues.

Certaines sources d'actualité remontées par les flux de veille peuvent être multilingues. Ce point est traité comme une contrainte maîtrisée : les flux sont conservés pour la couverture informationnelle, puis filtrés et priorisés dans l'analyse pour maintenir un périmètre décisionnel aligné avec l'usage métier.

### C6.6 Qualifier la fiabilité des sources et des flux identifiés

La qualification de fiabilité est explicite dans la configuration avec un niveau `high` pour les sources retenues. Cette qualification n'est pas décorative : elle sert de filtre de gouvernance pour éviter l'introduction de signaux faibles non vérifiés dans les décisions de conception.

La veille distingue également la nature des sources, entre publications techniques de fournisseurs et publications institutionnelles réglementaires, afin d'éviter le biais de confirmation purement technologique.

### C6.7 Configurer les outils d'agrégation selon les flux, les sources et les thématiques

La configuration des flux est paramétrée de manière déclarative dans `scripts/veille_sources.json` avec les attributs de catégorie et de fiabilité, puis exploitée par le script d'agrégation. Ce découplage entre configuration et exécution rend l'outillage maintenable et extensible.

Le résultat est une chaîne d'agrégation alignée sur les thématiques de veille, produisant des synthèses exploitables sans intervention manuelle lourde.

### C6.8 Rédiger des synthèses des informations collectées

La production de synthèse est matérialisée dans `docs/veille/veille_2026-03-09.md`. Le document rend compte de l'état des flux, signale les absences de contenu lorsque nécessaire, et met en évidence les actualités pertinentes. Cette transparence est importante : elle évite de surinterpréter des sources silencieuses et documente la réalité de la collecte.

Sur le fond, la synthèse intègre des éléments réglementaires significatifs, notamment les obligations GPAI de l'AI Act applicables depuis août 2025 et les lignes directrices associées de la Commission européenne, ainsi que des signaux CNIL utiles pour la gouvernance de données et la conformité.

La qualité d'une synthèse ne repose pas uniquement sur la quantité de liens collectés, mais sur la capacité à expliciter les conséquences concrètes pour le projet. Dans DATASENS, les synthèses sont exploitées pour ajuster les règles de journalisation, consolider la traçabilité des traitements et documenter les périmètres d'usage entre inférence locale et services externes.

### C6.9 Communiquer les synthèses aux parties prenantes du projet

La communication est assurée par publication dans le dépôt projet, ce qui rend les synthèses immédiatement accessibles aux parties prenantes techniques et facilite leur prise en compte dans les revues de conception. Le format choisi soutient une communication structurée, traçable et réutilisable dans les livrables de certification.

Cette modalité de communication consolide un principe essentiel : la veille n'est pas un document annexe, elle est un intrant formel des décisions projet.

Dans la pratique, la démarche adoptée est hybride. Une veille automatisée produit des livrables datés et reproductibles via l'agrégation RSS, tandis qu'une veille manuelle est conduite en parallèle dans Feedly et Google Alerts pour intégrer un tri expert, détecter des signaux faibles et écarter le bruit informationnel. Cette combinaison permet de concilier industrialisation du processus et pertinence métier des informations réellement utilisées pour arbitrer.

## C7. Identification et Benchmark de Services d'IA

### C7.1 Définir la problématique technique et fonctionnelle d'intelligence artificielle à adresser

La problématique fonctionnelle est de produire une classification de sentiment robuste sur des textes français hétérogènes, avec un niveau de lisibilité suffisant pour un usage métier. La problématique technique consiste à délivrer cette capacité sous forme de service API, avec une latence acceptable en CPU, un coût d'exploitation maîtrisé et une gouvernance de données conforme aux exigences du contexte.

Le besoin ne se limite pas à un score. Il inclut la fiabilité de la sortie, la capacité d'observer les performances en production et la possibilité d'orchestrer des stratégies de secours ou d'escalade sans casser l'architecture.

### C7.2 Identifier les contraintes de moyens, techniques et opérationnelles liées au contexte du projet

Les contraintes de moyens imposent une exécution sans dépendance GPU obligatoire. Les contraintes techniques imposent une intégration simple dans la stack Python/FastAPI existante, sans complexification inutile du run-time. Les contraintes opérationnelles exigent une continuité de service locale et une réduction des transferts de données sensibles hors périmètre projet.

Ces contraintes orientent naturellement vers une architecture locale de bout en bout pour le périmètre C7/C8.

Une contrainte complémentaire porte sur l'hétérogénéité linguistique des données de marché et d'actualité : la source finance obligatoire `yahoo_finance` est majoritairement en anglais. Même avec un objectif fonctionnel centré français, une fraction structurelle des textes collectés reste donc en anglais. La stratégie retenue consiste à objectiver cet impact via benchmark comparatif et à privilégier le moteur offrant le meilleur compromis sur le cas d'usage FR.

### C7.3 Benchmarker les outils et services d'intelligence artificielle accessibles et répondant au problème visé

Le benchmark est outillé dans `scripts/ai_benchmark.py` et documenté dans `docs/e2/AI_BENCHMARK.md`. L'évaluation compare plusieurs modèles locaux Hugging Face sur un même dataset et un protocole identique. Les critères pris en compte couvrent la qualité de classification (Accuracy, F1 macro), la latence, la confiance moyenne et la robustesse par classe.

**Identification précise des modèles comparés :**

| Clé benchmark | Modèle HuggingFace réel | Nature |
|---|---|---|
| `sentiment_fr` | `ac0hik/Sentiment_Analysis_French` | Modèle FR dédié, presse/opinion — **meilleur du benchmark** |
| `finetuned_local` | Config `.env` ou `models/sentiment_fr-sentiment-finetuned` | sentiment_fr (CamemBERT) fine-tuné sur données projet (run v2) |
| `flaubert_multilingual` | `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` | XLM-RoBERTa multilingue Twitter — N.B. : ce n'est pas FlauBERT |
| `bert_multilingual` | `nlptown/bert-base-multilingual-uncased-sentiment` | BERT multilingue 5★ — pas CamemBERT |

> **Note architecturale importante :** La clé `flaubert_multilingual` désigne en réalité un modèle XLM-RoBERTa de Cardiff NLP entraîné sur Twitter (`cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`), et non le modèle FlauBERT de l'INRIA. Ce nom reflète la propriété de multilinguisme du modèle. Le vrai FlauBERT (`flaubert/flaubert_base_uncased`) est disponible comme backbone alternatif dans le script de fine-tuning, mais n'a pas été évalué séparément dans ce benchmark.

Le benchmark daté repose sur le dataset `data/goldai/ia/test.parquet`, avec un échantillonnage équilibré de **120 exemples par classe** (`neg`, `neu`, `pos`), soit **360 échantillons au total**. Les résultats détaillés par classe (précision, rappel, F1, support) sont conservés dans `docs/e2/AI_BENCHMARK_RESULTS.json` pour audit.

Tableau de synthèse du benchmark (360 échantillons équilibrés, 2026-03-12) :

| Rang | Modèle | Accuracy | F1 macro | F1 pondéré | Confiance moy. | Latence moy. (ms) |
|:---:|---|---:|---:|---:|---:|---:|
| 🥇 | `finetuned_local` | **0,6389** | **0,6360** | 0,6360 | 68,6 % | 197,7 |
| 🥈 | `sentiment_fr` | 0,5861 | 0,5784 | 0,5784 | 79,2 % | 204,2 |
| 🥉 | `flaubert_multilingual` | 0,4556 | 0,4284 | 0,4284 | 81,7 % | 197,8 |
| 4 | `bert_multilingual` | 0,3944 | 0,3214 | 0,3214 | 60,4 % | 179,4 |

Tableau détaillé par classe (modèle `sentiment_fr`) :

| Classe | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `neg` (négatif) | 0,549 | 0,762 | **0,639** | 80 |
| `neu` (neutre)  | 0,724 | 0,525 | **0,609** | 80 |
| `pos` (positif) | 0,493 | 0,438 | **0,464** | 80 |

Tableau détaillé par classe (modèle `finetuned_local` — run v2, backbone sentiment_fr + class weights) :

| Classe | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `neg` | 0,581 | 0,842 | **0,687** | 120 |
| `neu` | 0,861 | 0,567 | **0,683** | 120 |
| `pos` | 0,570 | 0,508 | **0,537** | 120 |

**Historique v1 → v2 :** Le run v1 (backbone CamemBERT distil, sans class weights) produisait F1 pos = 0. La **version 2** corrige ce problème par : (1) `class_weight='balanced'` via `WeightedTrainer`, (2) backbone changé de `camembert` à `sentiment_fr` (meilleur pré-entraîné), (3) métrique de sélection `f1_macro`. Le modèle fine-tuné v2 dépasse désormais `sentiment_fr` sur toutes les classes.

> **Glossaire :** Le *backbone* est le modèle pré-entraîné sur lequel on fait le fine-tuning (ex. sentiment_fr, camembert). À ne pas confondre avec *barebone* (système minimal) ou *blackbone* (non standard en ML).

Au-delà du résultat brut, la méthode de benchmark est essentielle. Elle formalise un cadre d'évaluation reproductible qui permet de rejouer les comparaisons lors d'un changement de modèle, d'un nouveau besoin métier ou d'une évolution réglementaire. Le benchmark devient ainsi un outil de pilotage et non un exercice ponctuel figé à la date du dossier.

Une limite méthodologique est explicitement assumée : les labels de référence utilisés pour ce benchmark proviennent d'une annotation sémantique automatisée (pseudo-labels), et non d'une campagne d'annotation manuelle exhaustive. Les scores sont donc interprétés comme une comparaison relative robuste entre modèles. La validation finale de performance métier reste adossée à un échantillon de contrôle annoté manuellement.

Sur le plan d'exécution, la chaîne est industrialisée avec une séquence explicite : régénération de la copie IA (`scripts/create_ia_copy.py`, option `--topics finance,politique` pour veille ciblée), fine-tuning avec class weights (`scripts/finetune_sentiment.py --model sentiment_fr --epochs 3`) puis benchmark comparatif (`scripts/ai_benchmark.py`). Un mode rapide par défaut (`--max-train-samples 3000`) est utilisé pour les environnements CPU contraints. Le modèle actif est configuré via `SENTIMENT_FINETUNED_MODEL_PATH=models/sentiment_fr-sentiment-finetuned` dans `.env`.

Le run v2 (backbone sentiment_fr, class weights, mode quick ou full) produit un modèle `finetuned_local` qui dépasse `sentiment_fr` sur le benchmark. La filière locale est opérationnelle et recommandée pour la production.

Tableau d'arbitrage de mise en production (post v2) :

| Critère de décision | `sentiment_fr` | `finetuned_local` v2 | Décision |
|---|---:|---:|---|
| Qualité globale (F1 macro) | 0,578 | **0,636** | Avantage `finetuned_local` |
| Robustesse classe positive (F1 pos) | 0,462 | **0,537** | Avantage `finetuned_local` |
| Latence moyenne (ms) | 204,2 | **197,7** | Avantage `finetuned_local` |
| Recommandation actuelle | Fallback | **Moteur principal** | `finetuned_local` en production |

Visualisation graphique des résultats (preuve C7/C8) :

- Métriques de validation entraînement (quick ou full) : `docs/e2/figures/e2_training_{quick|full}_validation_metrics.png`
- Vue d'ensemble benchmark (qualité + latence) : `docs/e2/figures/e2_benchmark_overview.png`
- F1 par classe et par modèle (révèle le F1 pos = 0) : `docs/e2/figures/e2_benchmark_f1_per_class.png`
- Déséquilibre de classes et impact sur F1 positif : `docs/e2/figures/e2_benchmark_class_imbalance.png`
- Courbes multi-critères normalisées (qualité, confiance, efficience latence) : `docs/e2/figures/e2_benchmark_curves_normalized.png`
- Frontière de Pareto qualité/latence (aide à la décision) : `docs/e2/figures/e2_innovation_pareto_quality_latency.png`
- Performance d'exécution entraînement : `docs/e2/figures/e2_training_{quick|full}_runtime.png`
- Courbe de perte entraînement (visualisation pédagogique) : `docs/e2/figures/e2_training_{quick|full}_loss_curve.png`

Ces graphes sont générés automatiquement depuis `python scripts/plot_e2_results.py`, en s'appuyant sur `docs/e2/AI_BENCHMARK_RESULTS.json` (benchmark) et `docs/e2/TRAINING_RESULTS.json` (entraînement, écrit par `finetune_sentiment.py`).

Lecture pédagogique des métriques (niveau développeur junior) :

| Métrique | Ce que ça mesure | Comment la lire | Risque si on la regarde seule |
|---|---|---|---|
| Accuracy | Taux de prédictions correctes globales | 0,57 = 57 % des prédictions justes | Peut masquer une classe mal traitée (ex. F1 pos = 0 avec accuracy = 54 %) |
| Precision (par classe) | Quand le modèle prédit une classe, probabilité d'avoir raison | Precision `neg` élevée = peu de faux positifs | Peut être bonne même si le modèle oublie beaucoup de vrais cas |
| Recall (par classe) | Capacité à retrouver tous les vrais cas d'une classe | Recall `neg` = 0,95 = 95 % des vrais négatifs détectés | Peut monter artificiellement en sur-prédictant une classe |
| F1 (par classe) | Équilibre precision/recall sur une classe | F1 proche de 1 = bon compromis precision/recall | Cache parfois les causes d'erreur |
| F1 macro | Moyenne des F1 par classe, poids égal | Métrique principale ici — sévère sur les classes difficiles, c'est son intérêt | Peut sembler décevant mais révèle les vraies faiblesses |
| F1 pondéré | Moyenne F1 pondérée par le support (nb de cas) | Reflète la performance "moyenne" en production | **Dangereux seul** : masque les erreurs sur classes minoritaires (ex. positif) |
| Support | Nombre d'exemples d'une classe évaluée | Ici 80/80/80 : comparaison équitable entre classes | Sans support équilibré, les comparaisons sont biaisées |
| Confiance moyenne | Niveau de certitude interne du modèle | Confiance haute est utile, mais ≠ preuve de justesse | Un modèle peut être très confiant et se tromper |
| Latence moyenne | Temps moyen d'inférence par texte (ms) | Plus bas = meilleure réactivité API | Optimiser uniquement la latence peut dégrader la qualité |

Exemple concret avec nos résultats (post v2) :

- `finetuned_local` v2 (sentiment_fr fine-tuné) est le meilleur compromis : F1 macro 63,6 %, F1 pos 53,7 %, latence 198 ms.
- `sentiment_fr` reste un excellent fallback (F1 macro 57,8 %) si le modèle fine-tuné n'est pas disponible.
- La décision de production combine robustesse par classe, qualité globale et performance runtime.

Règle d'argumentation E2 (simple et défendable) :

- priorité 1 : éviter les erreurs métier critiques — ne jamais avoir F1 = 0 sur une classe (class imbalance à corriger) ;
- priorité 2 : conserver une qualité globale stable — F1 macro ≥ 0,50 comme seuil de référence ;
- priorité 3 : optimiser la latence sans casser la qualité — après les deux premières priorités.

### C7.4 Rédiger des conclusions préconisant un ou plusieurs services d'intelligence artificielle

Les conclusions formalisées dans `docs/e2/AI_REQUIREMENTS.md`, `docs/e2/AI_BENCHMARK.md` et `docs/e2/AI_BENCHMARK_RESULTS.json` préconisent `finetuned_local` (sentiment_fr fine-tuné) comme moteur principal, avec `sentiment_fr` en fallback. Cette préconisation est techniquement cohérente avec les composants déjà intégrés dans le code, économiquement soutenable, et conforme aux contraintes de gouvernance des données.

L'intérêt de cette conclusion est sa capacité d'industrialisation immédiate. Elle ne suppose pas de rupture technologique, réduit le coût de maintenance, et crée un cadre clair pour les évolutions futures, notamment l'ajustement des seuils de décision et le fine-tuning piloté par métriques.

La recommandation est également robuste du point de vue risque. Le service coeur reste opérationnel sans dépendance externe critique. En cas de renforcement réglementaire, la chaîne locale permet d'ajuster rapidement la politique de conformité.

Le dataset d'entraînement utilisé pour cette trajectoire est enrichi métier et non générique. Les colonnes `topic_1` et `topic_2` présentes dans `data/goldai/ia/train.parquet` montrent une représentation explicite des contextes finance et politique. Le split train comporte 36 170 exemples (neutre = 17 703, négatif = 13 627, positif = 4 840), le split val 4 521 exemples et le split test 4 522 exemples. Ce déséquilibre structurel (positif = 13 % seulement) est documenté, diagnostiqué et corrigé dans la version 2 du fine-tuning par l'ajout de `class_weight='balanced'`. Cela renforce la pertinence de l'apprentissage pour les usages DATASENS orientés actualité, opinion et signaux de décision politique et économique.

## C8. Paramétrage et Intégration d'un Service d'IA

### C8.1 Créer l'environnement d'exécution du service

L'environnement d'exécution est structuré autour d'une API FastAPI lancée par `python run_e2_api.py`, avec une séparation explicite entre configuration, couche applicative, sécurité et services IA. Ce découpage favorise la lisibilité opérationnelle et réduit le coût de maintenance.

La structure de l'environnement permet d'opérer le service de manière stable en local, tout en maintenant un point d'extension vers des services externes lorsque cela est nécessaire.

Dans le cadre E2, l'environnement est paramétré pour un fonctionnement CPU-first, cohérent avec les contraintes projet. Le service IA est chargé au démarrage de l'API puis utilisé dans les routes de prédiction et d'assistance. La logique d'exécution suit une chaîne claire : chargement configuration, sélection du modèle local, exposition des endpoints IA, puis instrumentation des appels.

### C8.2 Installer et configurer les éventuelles dépendances

Les dépendances critiques sont présentes et maîtrisées, notamment `transformers` et `torch`. Elles couvrent respectivement l'inférence locale et le support de calcul. Le paramétrage applicatif est centralisé dans `.env.example` avec des variables dédiées aux chemins de modèles et aux paramètres d'inférence CPU.

Ce mode de configuration rend le comportement du service explicite et reproductible entre environnements, ce qui est indispensable pour une exploitation fiable.

Le découplage entre code et configuration facilite aussi la gestion des environnements de livraison. Les mêmes composants applicatifs peuvent être déployés avec des profils d'exécution différents selon les contraintes de performance, de confidentialité ou de budget, sans divergence fonctionnelle du code métier.

Le paramétrage IA est concret et traçable. La variable `SENTIMENT_FINETUNED_MODEL_PATH` (prioritaire) pointe vers le modèle fine-tuné recommandé. Les variables `SENTIMENT_FR_MODEL_PATH`, `CAMEMBERT_MODEL_PATH`, `FLAUBERT_MODEL_PATH`, `INFERENCE_BATCH_SIZE`, `INFERENCE_MAX_LENGTH` et `TORCH_NUM_THREADS` pilotent le fallback et le profil de performance CPU. Cette configuration permet de contrôler le comportement fonctionnel sans modifier le code applicatif.

Le retour d'expérience d'intégration a conduit à un durcissement utile du socle technique : ajout explicite de `accelerate>=0.26.0` pour le `Trainer` Hugging Face, arrêt strict du batch en cas d'erreur intermédiaire, et normalisation systématique des labels de sentiment lors de la création des jeux `train/val/test` pour éliminer les variantes d'encodage (ex. `n�gatif`). Cette correction améliore directement la fiabilité des métriques C7 et la stabilité opérationnelle C8.

### C8.3 Créer les accès à l'environnement d'exécution et de configuration du service

L'accès au service est sécurisé par JWT et RBAC dans `src/e2/auth/security.py`, avec des dépendances de permission pour contrôler l'exposition des fonctionnalités. Cette approche protège l'environnement d'exécution et formalise les droits d'accès à la couche IA.

L'accès à la configuration suit une logique de variables d'environnement, ce qui permet de séparer les secrets, les paramètres d'inférence et les options de service du code métier. Ce point est central pour un déploiement propre et pour la conformité sécurité.

L'intégration IA est exposée dans les routes `/api/v1/ai/status`, `/api/v1/ai/sentiment` et `/api/v1/ai/predict`. En exploitation, l'endpoint de statut permet de vérifier immédiatement la disponibilité de la couche locale. Cette vérification opérationnelle est essentielle pour justifier que le service est intégré et pilotable, et non seulement configuré sur le papier.

### C8.4 Installer et configurer les outils de monitorage disponibles avec le service intégré

Le monitorage repose sur le middleware Prometheus dans `src/e2/api/middleware/prometheus.py`. Les métriques exposées couvrent le volume de requêtes, la durée des appels, les erreurs API et les signaux de dérive. Cette instrumentation fournit les indicateurs nécessaires au pilotage de la qualité de service, à la détection précoce d'anomalies et à l'objectivation des arbitrages techniques.

L'observabilité ainsi obtenue permet un pilotage basé sur des faits mesurables, et prépare la mise en place d'objectifs de service plus formels à mesure que le projet se stabilise.

À ce niveau, la maturité attendue n'est pas seulement d'afficher des métriques, mais de relier ces métriques à des décisions d'exploitation. Dans DATASENS, l'usage visé est clair : ajuster les seuils de confiance, suivre la charge réelle et anticiper les régressions de latence.

Le benchmark C7 est directement réinjecté dans C8 pour le paramétrage du moteur principal. Le modèle recommandé `finetuned_local` (via `SENTIMENT_FINETUNED_MODEL_PATH`) devient le candidat prioritaire en inférence locale, tandis que les métriques de latence et de qualité guident les ajustements de batch et de longueur de séquence. Cette continuité entre benchmark et exploitation constitue la preuve d'une intégration IA réellement industrialisée.

Pilotage du drift et déclenchement du réentraînement :

| Indicateur de drift | Métrique suivie | Seuil d'alerte (exemple projet) | Action |
|---|---|---|---|
| **Performance drift** (dégradation qualité) | `F1 macro`, `accuracy`, F1 par classe | Baisse > 0,03 vs baseline ou `F1 pos < 0,20` | Lancer un cycle `run_training_loop_e2.bat` puis re-benchmark |
| **Prediction drift** (sorties qui dérivent) | Distribution `neg/neu/pos` en prod vs baseline | Ecart absolu > 10 points sur une classe | Audit des textes récents + vérification qualité labels |
| **Confidence drift** (modèle moins sûr) | Confiance moyenne des prédictions | Baisse > 0,05 sur 7 jours glissants | Revue des cas ambigus et ajustement seuils |
| **Latency drift** (dérive runtime) | Latence moyenne d'inférence (ms) | Hausse > 25 % | Ajuster batch/threads et vérifier charge machine |
| **Data drift** (entrée qui change) | Ratio EN/FR, longueur texte, thèmes dominants | Variation > 20 % vs baseline | Rebalancer dataset et relancer benchmark |

Précisions de lecture (niveau junior) :

- **Data drift** : la forme des données d'entrée change (langue, longueur, sujets). Le modèle peut rester identique mais recevoir un flux différent.
- **Concept drift** : le sens des classes évolue dans le temps (ex. ton financier ironique, nouveaux usages). On l'observe surtout via la baisse des métriques de performance.
- **Prediction drift** : sans changer les entrées visibles, la distribution des sorties du modèle bouge (ex. trop de `neutre`), signe possible de dérive.

Règle d'exploitation retenue :

- benchmark quotidien pour surveiller,
- réentraînement déclenché uniquement si seuil franchi (pas systématique),
- validation par benchmark post-training avant tout changement de modèle en production.

### C8.5 Rédiger la documentation technique

La documentation technique est disponible sur plusieurs niveaux complémentaires. Le contrat d'API est exposé via `/docs`, `/redoc` et `/openapi.json`. Les décisions de benchmark et de cadrage sont documentées dans `docs/e2/AI_BENCHMARK.md` et `docs/e2/AI_REQUIREMENTS.md`. La veille est historisée dans `docs/veille/`. Les composants applicatifs clés sont identifiés dans les modules de l'API, de la sécurité, de l'inférence et du monitoring.

Cette documentation est exploitable en audit technique, en maintien en conditions opérationnelles et en soutenance de certification, car elle relie les choix d'architecture aux preuves d'implémentation.

La documentation remplit donc une double fonction : fonction de transfert, pour permettre la reprise rapide du périmètre par un autre développeur, et fonction de preuve, pour démontrer l'alignement entre intention de conception et implémentation effective.

Pour C8, la preuve documentaire suit une logique de chaîne complète : configuration (`.env.example`), exécution (`run_e2_api.py`), exposition API (`/docs`, `/openapi.json`), mesure d'efficacité (`docs/e2/AI_BENCHMARK_RESULTS.json`) et supervision (`src/e2/api/middleware/prometheus.py`). Cette chaîne permet de vérifier, étape par étape, que le paramétrage et l'intégration IA sont effectivement implémentés, testables et gouvernables.

## Conclusion

Le bloc E2 de DATASENS présente une architecture cohérente, opérationnelle et gouvernable. Le choix de services IA n'est pas opportuniste : il résulte d'un cadrage explicite, d'un benchmark documenté et d'une intégration déjà effective dans l'API. La veille technologique et réglementaire est outillée, planifiée et reliée aux décisions du projet. Le paramétrage, la sécurité et le monitorage sont en place et permettent une exploitation crédible.

La trajectoire recommandée est d'approfondir la filière locale plutôt que d'accumuler de nouveaux composants. Une stratégie de pilotage par métriques, appuyée sur un benchmark régulier, une validation méthodologique et une veille réglementaire continue, constitue une voie réaliste pour consolider la valeur métier tout en maintenant la maîtrise technique.

En synthèse, le bloc E2 démontre une compétence d'ingénierie complète : capacité à cadrer un besoin IA, à sélectionner une solution en tenant compte du contexte réel, à intégrer cette solution dans une architecture sécurisée, puis à l'exploiter avec des mécanismes de contrôle et d'amélioration continue. Cette cohérence entre choix, implémentation et gouvernance est précisément ce qui distingue une preuve de concept d'une base industrialisable.

## Annexes

### Annexe 1 : Preuves associées à la partie A3

Les éléments de preuve mobilisés pour la partie A3 sont principalement les composants d'intégration IA exposés dans `src/e2/api/routes/ai.py`, le service d'inférence locale dans `src/ml/inference/local_hf_service.py`, ainsi que les tests d'API dans `tests/test_e2_api.py`. Ces fichiers attestent du caractère opérationnel de l'intégration locale de la classification de sentiment dans le socle applicatif.

### Annexe 2 : Preuves associées à la partie C6

Les preuves de veille technologique et réglementaire sont matérialisées dans `scripts/veille_sources.json` pour la qualification des flux, `scripts/veille_digest.py` pour l'agrégation et la génération automatisée, `docs/veille/veille_2026-03-10.md` et `docs/veille/veille_2026-03-10.json` pour les sorties de veille, `docs/e2/ANNEXE_C6_VEILLE_2026-03-10.md` et `docs/e2/ANNEXE_C6_VEILLE_2026-03-10.json` pour les copies annexes, `docs/e2/ANNEXE_C6_SOURCES_MOTS_CLES.md` pour la cartographie des sources et mots-clés, et `VEILLE_SENTIMENT_MODELS.md` pour le cadrage thématique. Cet ensemble démontre que la veille est outillée, planifiée et reliée aux décisions du projet.

### Annexe 3 : Preuves associées à la partie C7

Les preuves de benchmark et de recommandation sont contenues dans `scripts/ai_benchmark.py`, `scripts/run_benchmark_e2.bat`, `docs/e2/AI_BENCHMARK.md`, `docs/e2/AI_BENCHMARK_RESULTS.json`, `docs/e2/AI_REQUIREMENTS.md` et `docs/e2/ANNEXE_3_C7_PREUVE_EXECUTION_BENCHMARK.md`. Elles documentent la comparaison chiffrée entre modèles et le dataset utilisé (`data/goldai/ia/test.parquet`), puis la décision d'architecture en faveur d'un moteur local principal.

Les preuves d'industrialisation récente complètent cette annexe : `scripts/run_training_loop_e2.bat` (mode quick/full, contrôle d'échec), `scripts/create_ia_copy.py` (normalisation des labels avant split) et `scripts/finetune_sentiment.py` (fine-tuning borné par volume en contexte CPU). Cet ensemble démontre la capacité à exécuter un cycle complet entraînement + benchmark sur un poste contraint, sans dégrader la traçabilité.

Les preuves visuelles benchmark/entraînement sont consolidées dans `docs/e2/figures/` et référencées dans `docs/e2/AI_BENCHMARK.md`. Cette couche de visualisation complète les tableaux chiffrés en facilitant l'interprétation comparative des performances (qualité globale, robustesse par classe et coût de latence).

### Annexe 4 : Preuves associées à la partie C8

Les preuves de paramétrage et d'intégration sont visibles dans `run_e2_api.py` et `src/e2/api/main.py` pour l'environnement d'exécution, `src/e2/auth/security.py` pour la sécurisation des accès, `src/e2/api/middleware/prometheus.py` pour le monitorage, et la documentation d'interface accessible via `/docs`, `/redoc` et `/openapi.json`. Les modules IA déjà cités confirment la mise en oeuvre concrète de la configuration, de l'exploitation et du pilotage technique du service.

### Annexe 5 (rattachée à C6) : Processus de veille hybride (automatique + manuelle)

Le processus de veille est organisé en deux niveaux complémentaires afin de concilier robustesse industrielle et pertinence métier. Le niveau automatique repose sur l'agrégation de flux RSS qualifiés, configurés dans `scripts/veille_sources.json` et exploités par `scripts/veille_digest.py`. Cette chaîne produit des livrables horodatés en Markdown et JSON (`docs/veille/veille_YYYY-MM-DD.md` et `docs/veille/veille_YYYY-MM-DD.json`), ainsi qu'une copie dédiée au dossier E2 dans `docs/e2/`, ce qui garantit la traçabilité et la reproductibilité de la collecte.

Le niveau manuel repose sur Feedly et Google Alerts. Il ne remplace pas l'automatisation ; il intervient comme couche d'analyse experte pour filtrer le bruit informationnel, confirmer la valeur des signaux faibles et prioriser les informations réellement utiles aux décisions projet. Cette revue humaine permet notamment de distinguer les contenus de fond (benchmark, conformité, publications techniques structurantes) des contenus à faible impact opérationnel.

La méthode appliquée est cyclique. La collecte automatique est exécutée selon un rythme régulier, puis une revue manuelle vérifie la pertinence des éléments remontés, extrait les points d'impact, et formalise les décisions associées dans le dossier technique. Ce fonctionnement répond aux attendus C6 : définition des thématiques, outillage d'agrégation, qualification des sources, production de synthèses et communication des résultats aux parties prenantes.

Le choix d'une veille hybride constitue un compromis assumé et professionnel. L'automatisation apporte la preuve, l'historique et la continuité ; la revue manuelle apporte le discernement, la contextualisation et la priorisation stratégique. Ensemble, ces deux niveaux renforcent la qualité des arbitrages techniques, réglementaires et d'exploitation réalisés dans le bloc E2.

### Annexe 6 (rattachée à C6) : Liste de mots-clés Google Alerts / Feedly

La liste structurée des mots-clés de veille manuelle, ainsi que l'historique utilisateur conservé, est fournie dans `docs/e2/ANNEXE_6_C6_GOOGLE_ALERTS_FEEDLY_MOTS_CLES.md`. Cette annexe formalise le périmètre de collecte manuelle et permet de justifier les thématiques surveillées hors agrégation automatisée.

### Annexe 7 (rattachée à C6) : Preuve de collecte de veille

La preuve de collecte est fournie dans `docs/e2/ANNEXE_7_C6_PREUVE_COLLECTE_VEILLE.md`, avec renvoi explicite vers les sorties générées en Markdown et en JSON. Cette annexe démontre la traçabilité technique de la veille et la capacité à produire des artefacts auditables.

### Annexe 8 (rattachée à C7/C8) : Interprétation du run quotidien (11/03/2026)

Le run quotidien exécuté (`main.py` puis `scripts/merge_parquet_goldai.py` puis `scripts/create_ia_copy.py`) est conforme aux objectifs d'exploitation. La collecte a extrait 1 344 articles, dont 133 nouveaux articles effectivement intégrés après déduplication (1 211 doublons), ce qui confirme le bon fonctionnement du contrôle d'unicité. Les sources économiques obligatoires sont bien alimentées sur la session, avec 42 nouveaux éléments `yahoo_finance` et 38 `google_news_rss`.

La chaîne de données est complète de bout en bout : exports RAW/SILVER/GOLD générés, fusion GoldAI incrémentale terminée (`45 213` lignes finales), puis création des splits IA (`train=36 170`, `val=4 521`, `test=4 522`) avec normalisation des labels sentiment. Aucun incident bloquant n'a été observé ; les warnings Spark/Hadoop Windows relevés dans les logs sont non bloquants dans ce contexte local.

### Annexe 9 (rattachée à E1/E2/E5) : Preuves visuelles d'observabilité et d'API

Les preuves visuelles attendues pour la partie observabilité et exposition de service sont regroupées dans `docs/e2/ANNEXE_9_PREUVES_VISUELLES_MLOPS_API.md`. Cette annexe liste les captures obligatoires (Grafana, Uptime Kuma, Prometheus, ReDoc et OpenAPI JSON), les URL de vérification, ainsi que les éléments à faire apparaître à l'écran (date, endpoint, statut, métriques) pour rendre la preuve auditable sans ambiguïté.

### Annexe 10 (rattachée à C7/C8) : Preuves d'exécution technique E2

Les preuves d'exécution technique de la chaîne E2 sont consolidées dans `docs/e2/ANNEXE_10_PREUVES_EXECUTION_E2.md`. Cette annexe regroupe les commandes de run (training loop, benchmark, API, drift/metrics), les résultats attendus et leur interprétation, afin de démontrer une mise en oeuvre réelle et reproductible.

### Annexe 11 (rattachée à C7/C8) : Captures E2

La checklist normalisée des captures à produire est fournie dans `docs/e2/ANNEXE_11_CAPTURES_E2.md`. Elle précise le nommage des fichiers, les écrans obligatoires (benchmark, training quick, predict API, ReDoc/OpenAPI, Prometheus/Grafana/Uptime Kuma) et le contenu minimal attendu pour chaque preuve.

### Annexe 12 (rattachée à A3/C6/C7/C8) : Plan de démonstration E2 (15 min)

Le script de démonstration oral minute par minute est disponible dans `docs/e2/ANNEXE_12_PLAN_DEMO_E2_15MIN.md`. Cette annexe facilite une soutenance structurée, en liant chaque séquence de démonstration à une compétence évaluée et à une preuve visuelle correspondante.
