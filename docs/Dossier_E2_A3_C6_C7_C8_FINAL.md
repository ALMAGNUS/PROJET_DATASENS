# BLOC E2 - Intégration de services d'Intelligence Artificielle

Projet : DATASENS  
Candidat : Alan Jaffre

## Introduction

Le projet DATASENS vise l'analyse de contenus textuels francophones issus de sources hétérogènes afin de produire des indicateurs de sentiment exploitables dans un contexte métier. Le bloc E1 a établi le socle de collecte, de structuration et de stockage des données. Le bloc E2 s'inscrit dans cette continuité en ajoutant une couche d'intelligence artificielle orientée usage, avec un objectif de transformation fiable des données textuelles en informations directement actionnables.

La démarche retenue est volontairement ingénieriale : il ne s'agit pas de réentraîner un modèle propriétaire de bout en bout, mais de sélectionner des services IA existants, de les comparer sur des critères explicites, de les intégrer proprement dans l'architecture applicative, puis de les piloter en production via des métriques. Cette posture permet de réduire le risque projet, de maîtriser les coûts d'exploitation et de maintenir une trajectoire d'évolution progressive.

Sur le plan technique, ce positionnement est déjà matérialisé dans le code. L'API est portée par `run_e2_api.py` et `src/e2/api/main.py`, la sécurité est gérée par JWT/RBAC dans `src/e2/auth/security.py`, la couche IA est orchestrée par `src/e2/api/routes/ai.py`, l'inférence locale est assurée dans `src/ml/inference/local_hf_service.py`, les usages génératifs sont connectés via `src/e3/mistral/service.py`, et l'observabilité est apportée par `src/e2/api/middleware/prometheus.py`.

L'enjeu du bloc E2 n'est donc pas uniquement technologique ; il est également méthodologique. Le livrable attendu à ce niveau de certification consiste à démontrer la capacité à transformer un besoin métier ambigu en une architecture IA explicable, testable, exploitable et gouvernable. Le dossier est rédigé dans cette perspective : chaque choix est relié à une contrainte, chaque contrainte à un arbitrage, et chaque arbitrage à une preuve d'implémentation.

## A3. Accompagner le choix et l'intégration d'un service d'intelligence artificielle préexistant

### A3.1 Cadrage du besoin fonctionnel et technique

Le besoin métier adressé en E2 est double. D'une part, classifier automatiquement le sentiment de textes en français avec un niveau de confiance exploitable. D'autre part, proposer des fonctionnalités d'assistance à la lecture comme le résumé et l'insight conversationnel. Le besoin d'intégration impose que ces capacités soient accessibles via API, sécurisées, traçables et observables.

Le cadrage technique écarte un choix monolithique unique. Les contraintes de contexte imposent une logique CPU-first, un contrôle des coûts, une limitation des transferts de données vers des tiers et une maintenabilité compatible avec une exploitation continue. Le service IA visé doit donc s'intégrer dans l'existant sans rupture de stack.

### A3.2 Démarche de sélection et décision d'architecture

La stratégie adoptée repose sur un modèle hybride. Le coeur du traitement de sentiment est confié à des modèles locaux Hugging Face, afin de conserver la maîtrise des données, la prédictibilité des coûts et la disponibilité de service en contexte dégradé cloud. Les fonctions génératives sont déportées vers Mistral pour les cas où la valeur fonctionnelle justifie l'appel externe.

Cette décision répond à une logique de séparation des responsabilités. Le local est privilégié dès lors que la tâche est déterministe et mesurable, notamment sur le sentiment. Le cloud est mobilisé pour des usages d'assistance qui bénéficient d'une meilleure richesse générationnelle. Le compromis est robuste car il limite le verrouillage fournisseur tout en conservant une capacité d'innovation rapide.

L'arbitrage a également été pensé sous l'angle du cycle de vie opérationnel. Un moteur local est plus simple à fiabiliser dans la durée, car son comportement est moins dépendant d'évolutions externes d'API, de quotas ou de politique tarifaire. Le moteur cloud reste pertinent, mais dans un rôle clairement délimité. Cette répartition réduit la variabilité du service sur la chaîne critique de production.

### A3.3 Intégration opérationnelle dans l'API

L'intégration est concrète et exploitable immédiatement. Les points d'entrée `/api/v1/ai/status`, `/api/v1/ai/chat`, `/api/v1/ai/summarize`, `/api/v1/ai/sentiment`, `/api/v1/ai/predict` et `/api/v1/ai/insight` démontrent la couverture fonctionnelle du bloc E2 et permettent de valider l'orchestration locale/cloud sans ambiguïté.

Le service local fournit des sorties structurées comme `label`, `confidence` et `sentiment_score`, ce qui constitue un socle solide pour la qualification des résultats et le pilotage qualité. Sur le plan architecture, ce format de sortie est essentiel car il permet de raisonner en seuils, de mesurer la dérive et d'implémenter des règles d'escalade maîtrisées.

### A3.4 Valeur apportée et trajectoire d'évolution

L'apport principal d'A3 n'est pas seulement d'avoir intégré un service IA, mais d'avoir conçu une intégration gouvernable. Le bloc E2 prépare explicitement une montée en maturité vers une logique de routage intelligent local-first avec escalade conditionnelle cloud. Cette trajectoire est compatible avec l'existant, et elle permet une amélioration continue sans réécriture massive.

En termes d'impact projet, cette approche permet de traiter progressivement les points les plus sensibles : stabilisation des seuils de confiance, réduction des faux positifs sur les textes ambigus, et pilotage du taux d'escalade cloud. La valeur ajoutée n'est pas une promesse abstraite d'IA "plus performante", mais une capacité concrète à améliorer la qualité perçue sans dérive de coûts.

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

Les sources retenues couvrent le spectre nécessaire au projet. Sur le volet technologique, OpenAI, Mistral AI et Hugging Face permettent de suivre les évolutions de capacités, d'API et d'écosystèmes modèles. Sur le volet réglementaire, ANSSI et CNIL apportent une base fiable pour la conformité et les bonnes pratiques de sécurité.

Cette cartographie de sources est définie dans `scripts/veille_sources.json` et aligne directement les flux collectés avec les trois thématiques de veille retenues.

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

## C7. Identification et Benchmark de Services d'IA

### C7.1 Définir la problématique technique et fonctionnelle d'intelligence artificielle à adresser

La problématique fonctionnelle est de produire une classification de sentiment robuste sur des textes français hétérogènes, avec un niveau de lisibilité suffisant pour un usage métier. La problématique technique consiste à délivrer cette capacité sous forme de service API, avec une latence acceptable en CPU, un coût d'exploitation maîtrisé et une gouvernance de données conforme aux exigences du contexte.

Le besoin ne se limite pas à un score. Il inclut la fiabilité de la sortie, la capacité d'observer les performances en production et la possibilité d'orchestrer des stratégies de secours ou d'escalade sans casser l'architecture.

### C7.2 Identifier les contraintes de moyens, techniques et opérationnelles liées au contexte du projet

Les contraintes de moyens imposent une exécution sans dépendance GPU obligatoire. Les contraintes techniques imposent une intégration simple dans la stack Python/FastAPI existante, sans complexification inutile du run-time. Les contraintes opérationnelles exigent une continuité de service, y compris en cas d'indisponibilité d'un fournisseur cloud, et une réduction des transferts de données sensibles hors périmètre local.

Ces contraintes orientent naturellement vers une architecture de type local-first, avec externalisation sélective des tâches génératives à plus forte valeur ajoutée.

### C7.3 Benchmarker les outils et services d'intelligence artificielle accessibles et répondant au problème visé

Le benchmark est outillé dans `scripts/ai_benchmark.py` et documenté dans `docs/e2/AI_BENCHMARK.md`. L'évaluation compare une approche locale Hugging Face à une approche cloud de type API générative. Les critères pris en compte couvrent le coût, la latence, la confidentialité, les dépendances techniques et la conformité.

Les résultats obtenus confirment l'intérêt du local pour le coeur de la classification, avec une meilleure maîtrise des données et un meilleur alignement réglementaire, tandis que le cloud reste pertinent pour des fonctions génératives ciblées.

Au-delà du résultat brut, la méthode de benchmark est essentielle. Elle formalise un cadre d'évaluation reproductible qui permet de rejouer les comparaisons lors d'un changement de modèle, d'un nouveau besoin métier ou d'une évolution réglementaire. Le benchmark devient ainsi un outil de pilotage, et non un exercice ponctuel figé à la date du dossier.

### C7.4 Rédiger des conclusions préconisant un ou plusieurs services d'intelligence artificielle

Les conclusions formalisées dans `docs/e2/AI_REQUIREMENTS.md` et `docs/e2/AI_BENCHMARK.md` préconisent explicitement un moteur principal local pour le sentiment, complété par un moteur cloud secondaire pour les usages génératifs. Cette préconisation est techniquement cohérente avec les composants déjà intégrés dans le code, économiquement soutenable, et conforme aux contraintes de gouvernance des données.

L'intérêt de cette conclusion est sa capacité d'industrialisation immédiate. Elle ne suppose pas de rupture technologique et crée un cadre clair pour les évolutions futures, en particulier l'introduction de règles de routage basées sur les seuils de confiance.

La recommandation est également robuste du point de vue risque. En cas d'indisponibilité cloud, le service coeur reste opérationnel. En cas d'évolution de coût fournisseur, l'impact est contenu au périmètre génératif. En cas de renforcement réglementaire, la part locale de la chaîne permet d'ajuster plus rapidement la politique de conformité.

## C8. Paramétrage et Intégration d'un Service d'IA

### C8.1 Créer l'environnement d'exécution du service

L'environnement d'exécution est structuré autour d'une API FastAPI lancée par `python run_e2_api.py`, avec une séparation explicite entre configuration, couche applicative, sécurité et services IA. Ce découpage favorise la lisibilité opérationnelle et réduit le coût de maintenance.

La structure de l'environnement permet d'opérer le service de manière stable en local, tout en maintenant un point d'extension vers des services externes lorsque cela est nécessaire.

### C8.2 Installer et configurer les éventuelles dépendances

Les dépendances critiques sont présentes et maîtrisées, notamment `transformers`, `torch` et `mistralai`. Elles couvrent respectivement l'inférence locale, le support de calcul et l'intégration des fonctionnalités génératives externes. Le paramétrage applicatif est centralisé dans `.env.example` avec des variables dédiées aux chemins de modèles, aux paramètres d'inférence CPU et aux accès cloud.

Ce mode de configuration rend le comportement du service explicite et reproductible entre environnements, ce qui est indispensable pour une exploitation fiable.

Le découplage entre code et configuration facilite aussi la gestion des environnements de livraison. Les mêmes composants applicatifs peuvent être déployés avec des profils d'exécution différents selon les contraintes de performance, de confidentialité ou de budget, sans divergence fonctionnelle du code métier.

### C8.3 Créer les accès à l'environnement d'exécution et de configuration du service

L'accès au service est sécurisé par JWT et RBAC dans `src/e2/auth/security.py`, avec des dépendances de permission pour contrôler l'exposition des fonctionnalités. Cette approche protège l'environnement d'exécution et formalise les droits d'accès à la couche IA.

L'accès à la configuration suit une logique de variables d'environnement, ce qui permet de séparer les secrets, les paramètres d'inférence et les options de service du code métier. Ce point est central pour un déploiement propre et pour la conformité sécurité.

### C8.4 Installer et configurer les outils de monitorage disponibles avec le service intégré

Le monitorage repose sur le middleware Prometheus dans `src/e2/api/middleware/prometheus.py`. Les métriques exposées couvrent le volume de requêtes, la durée des appels, les erreurs API et les signaux de dérive. Cette instrumentation fournit les indicateurs nécessaires au pilotage de la qualité de service et à la détection précoce d'anomalies.

L'observabilité ainsi obtenue permet un pilotage basé sur des faits mesurables, et prépare la mise en place d'objectifs de service plus formels à mesure que le projet se stabilise.

À ce niveau, la maturité attendue n'est pas seulement d'afficher des métriques, mais de relier ces métriques à des décisions d'exploitation. Dans DATASENS, l'usage visé est clair : ajuster les seuils de confiance, suivre la charge réelle, anticiper les régressions de latence et objectiver les arbitrages entre traitement local et escalade cloud.

### C8.5 Rédiger la documentation technique

La documentation technique est disponible sur plusieurs niveaux complémentaires. Le contrat d'API est exposé via `/docs`, `/redoc` et `/openapi.json`. Les décisions de benchmark et de cadrage sont documentées dans `docs/e2/AI_BENCHMARK.md` et `docs/e2/AI_REQUIREMENTS.md`. La veille est historisée dans `docs/veille/`. Les composants applicatifs clés sont identifiés dans les modules de l'API, de la sécurité, de l'inférence et du monitoring.

Cette documentation est exploitable en audit technique, en maintien en conditions opérationnelles et en soutenance de certification, car elle relie les choix d'architecture aux preuves d'implémentation.

La documentation remplit donc une double fonction : fonction de transfert, pour permettre la reprise rapide du périmètre par un autre développeur, et fonction de preuve, pour démontrer l'alignement entre intention de conception et implémentation effective.

## Conclusion

Le bloc E2 de DATASENS présente une architecture cohérente, opérationnelle et gouvernable. Le choix de services IA n'est pas opportuniste : il résulte d'un cadrage explicite, d'un benchmark documenté et d'une intégration déjà effective dans l'API. La veille technologique et réglementaire est outillée, planifiée et reliée aux décisions du projet. Le paramétrage, la sécurité et le monitorage sont en place et permettent une exploitation crédible.

La trajectoire recommandée est d'approfondir l'orchestration plutôt que d'accumuler de nouveaux composants. Une stratégie local-first, complétée par une escalade cloud conditionnée par la confiance, pilotée par métriques et appuyée par une veille réglementaire continue, constitue une voie réaliste pour consolider la valeur métier tout en maintenant la maîtrise technique.

En synthèse, le bloc E2 démontre une compétence d'ingénierie complète : capacité à cadrer un besoin IA, à sélectionner une solution en tenant compte du contexte réel, à intégrer cette solution dans une architecture sécurisée, puis à l'exploiter avec des mécanismes de contrôle et d'amélioration continue. Cette cohérence entre choix, implémentation et gouvernance est précisément ce qui distingue une preuve de concept d'une base industrialisable.

## Annexes

### Annexe 1 : Preuves associées à la partie A3

Les éléments de preuve mobilisés pour la partie A3 sont principalement les composants d'intégration IA exposés dans `src/e2/api/routes/ai.py`, le service génératif encapsulé dans `src/e3/mistral/service.py`, le service d'inférence locale dans `src/ml/inference/local_hf_service.py`, ainsi que les tests d'API dans `tests/test_e2_api.py`. Ces fichiers attestent du caractère opérationnel de l'approche hybride locale/cloud et de son intégration effective dans le socle applicatif.

### Annexe 2 : Preuves associées à la partie C6

Les preuves de veille technologique et réglementaire sont matérialisées dans `scripts/veille_sources.json` pour la qualification des flux, `scripts/veille_digest.py` pour l'agrégation et la génération automatisée, `docs/veille/veille_2026-03-09.md` pour la synthèse versionnée, et `VEILLE_SENTIMENT_MODELS.md` pour le cadrage thématique. Cet ensemble démontre que la veille est outillée, planifiée et reliée aux décisions du projet.

### Annexe 3 : Preuves associées à la partie C7

Les preuves de benchmark et de recommandation sont contenues dans `scripts/ai_benchmark.py`, `docs/e2/AI_BENCHMARK.md` et `docs/e2/AI_REQUIREMENTS.md`. Elles documentent la comparaison entre approche locale et approche cloud selon des critères explicites, puis la décision d'architecture en faveur d'un moteur local principal complété par un moteur cloud secondaire pour les usages génératifs.

### Annexe 4 : Preuves associées à la partie C8

Les preuves de paramétrage et d'intégration sont visibles dans `run_e2_api.py` et `src/e2/api/main.py` pour l'environnement d'exécution, `src/e2/auth/security.py` pour la sécurisation des accès, `src/e2/api/middleware/prometheus.py` pour le monitorage, et la documentation d'interface accessible via `/docs`, `/redoc` et `/openapi.json`. Les modules IA déjà cités confirment la mise en oeuvre concrète de la configuration, de l'exploitation et du pilotage technique du service.

