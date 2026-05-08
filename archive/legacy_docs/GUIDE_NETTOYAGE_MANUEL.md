# Guide de nettoyage manuel — hiérarchie d’utilité des fichiers

Ce document classe les fichiers **versionnés dans Git** (voir `INVENTAIRE_PROJET.md`) pour t’aider à **décider toi-même** quoi archiver ou supprimer.  
**Aucune suppression automatique** : sauvegarde une branche ou un tag avant gros ménage, et lance les tests (`pytest`) après toute suppression de code ou de config.

---

## Légende des niveaux

| Niveau | Signification | Action typique |
|--------|----------------|----------------|
| **A — Critique** | Sans ces fichiers, le pipeline, l’API ou le déploiement cassent (ou le dépôt n’est plus reproductible). | **Ne pas supprimer.** |
| **B — Opérationnel** | Tests, CI, Docker, monitoring, scripts que tu utilises encore. | Garder ; ne supprimer qu’après vérification (CI, runbook). |
| **C — Documentation / preuve** | Utile pour compréhension, jury, traçabilité ; ne sert pas au runtime. | Tu peux **archiver** (zip, autre repo) ou **fusionner** des doublons, pas besoin pour exécuter `main.py`. |
| **D — Candidat au tri** | Redondant, copie d’export, instantané daté, variante OS, brouillon. | **Bon candidat** à suppression ou archivage si tu confirmes qu’aucun lien ne les référence. |
| **E — Hors dépôt (local)** | Souvent dans `.gitignore`. | Nettoyage disque OK (données régénérables) ; ne confonds pas avec le code source. |

---

## A — Critique (ne pas supprimer sans remplacement)

### Racine

- `main.py` — point d’entrée pipeline E1.
- `sources_config.json` — configuration des sources (lue par `src/e1/pipeline.py` et le dépôt).
- `requirements.txt` — dépendances Python.
- `.env.example` — modèle de variables (le vrai `.env` est local et ignoré).
- `pyproject.toml` — configuration Ruff / qualité.
- `pytest.ini` — comportement des tests.
- `docker-compose.yml`, `Dockerfile`, `Dockerfile.windows` — si tu déploies ou lances avec Docker.
- `run_e2_api.py` — si c’est ton lanceur API E2 (à confirmer selon ton usage).

### Code applicatif

- Tout le dossier `src/` **sauf** appréciation au cas par cas pour `zzdb/` (voir plus bas).

### Fichiers que le code ou la doc officielle importe

- `redec_open_api.json` — à garder si une route ou un client s’y réfère ; sinon vérifier avant suppression.

---

## B — Opérationnel (garder tant que tu t’en sers)

### CI / qualité

- `.github/workflows/*.yml` — désactiver une workflow plutôt que supprimer sans raison.
- `pyrightconfig.json` — typage IDE/CI selon ton flux.

### Tests

- Tout `tests/` — supprimer un test = accepter de ne plus couvrir ce cas ; à faire sciemment.

### Scripts `scripts/`

- **À préserver en priorité** (souvent cités ou chaîne critique) :  
  `setup_with_sql.py`, `regenerate_exports.py`, `validate_json.py`, `validate_e1_project.py`, `db_state_report.py`, outils que *tu* documentes dans ton README ou ton runbook quotidien.
- **Doublons multi-plateforme** : pour un même rôle, tu as souvent `.bat`, `.sh`, `.ps1` (ex. PySpark, merge parquet, deploy). **Garde la variante que tu utilises** ; les autres passent en **D** si tu es sûr.

### Racine — lanceurs

- `start_*.bat`, `_launch_*.bat`, `lancer_tout.bat`, `run_daily.ps1`, `run_ruff.bat` — **garder ceux de ton habitude** ; le reste peut être **D** après vérif.

### Monitoring

- `monitoring/` — garder si Grafana/Prometheus sont utilisés.

### Hadoop (Windows)

- `hadoop/README.md`, `hadoop/bin/.gitkeep` — garder si PySpark / winutils font partie de ton env.

### Notebooks

- `notebooks/` — **B** si tu t’en sers encore pour formation ou repro ; sinon voir **D**.

---

## C — Documentation / annexes (utile, pas indispensable au run)

### `docs/` (hors sous-dossiers “preuves” datées)

- Guides d’architecture, audits, `DATA_FLOW.md`, `QUICK_START*.md`, `README.md` index : **garder** une base de doc cohérente.
- Multiples variantes du **même dossier** (ex. `Dossier_E2_A3_C6_C7_C8.md`, `..._FINAL.md`, `..._FINAL_VERSION_PROPRE.md`) : souvent **une seule** version “référence” suffit ; le reste = **C/D** (archivage).

### `docs/e2/`, `docs/e3/`, etc.

- Benchmarks (`AI_BENCHMARK.md`, résultats JSON, figures) : **C** pour preuve / rapport.
- Annexes de veille **par date** : **C** ; doublons possibles avec `docs/veille/` (même période) → voir **D**.

### Fichiers méta à la racine

- `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE.md`, `README.md` — **C** au sens “pas pour exécuter”, mais **fortement recommandés** pour un dépôt public/pro ; ne les classe pas en “poubelle”.

---

## D — Candidats typiques au nettoyage (à valider toi-même)

Vérifie les références (`grep`, README, liens internes) avant de supprimer.

### Rapports d’état datés

- `reports/db_state_*.json` et `reports/db_state_*.md` — instantanés **historiques**. Tu peux **ne garder que les N derniers** ou tout archiver ailleurs et ne laisser qu’un rapport récent (ou aucun dans Git si tu préfères les générer à la demande).

### Exports “copie-collage” ou doublons de doc

- `docs/Dossier_E2_A3_C6_C7_C8_FINAL_EXPORT_GDOCS.txt`  
- `docs/Dossier_E2_A3_C6_C7_C8_FINAL_EXPORT_GDOCS_MIX.txt`  
- `docs/Dossier_E2_A3_C6_C7_C8_FINAL_EXPORT_GDOCS_V2.txt`  
  Si le `.md` “final” te suffit, les `.txt` sont souvent **redondants** (**D**).

### Veille dupliquée entre deux arbres

- `docs/e2/ANNEXE_C6_VEILLE_YYYY-MM-DD.{json,md}` **et** `docs/veille/veille_YYYY-MM-DD.{json,md}` pour **la même période** : souvent deux canaux pour la même chose. **Conserve une convention** (un seul dossier) et mets l’autre en **D** après contrôle de contenu.

### Fichiers générés ou de validation ponctuelle

- `validation_report.json` (racine) — souvent **régénérable** ; **D** si tu ne t’en sers plus en CI.

### Scripts utilitaires “one-shot” ou doublons

- `fix_ruff_unicode.py`, `_fix_unicode_prometheus.py` — **D** si les problèmes Unicode sont résolus partout et plus aucun runbook ne les cite.
- `scripts/dossier_e1_examples.py` — exemples (exclu du lint) ; **D** si plus utilisé pédagogiquement.

### Package `zzdb/` (3 fichiers)

- Données / scripts **lab** (synthétique). **D** (voire suppression du dossier) **uniquement** si aucune doc ni aucun script d’import ne référence `zzdb` ; sinon **B**.

### Notebooks obsolètes

- Si tout le flux est dans `src/` et `main.py`, les notebooks `notebooks/datasens_E1/*.ipynb` peuvent passer en **D** ou être exportés en archive hors repo.

### Documentation très redondante

- Plusieurs audits couvrant le même sujet (`AUDIT_*`) : tu peux **fusionner** ou ne garder que la version la plus à jour (**D** pour les anciennes après fusion).

---

## E — Hors Git (nettoyage disque, pas “fichiers du projet source”)

Ces chemins sont en général **ignorés** ; les supprimer libère de l’espace sans toucher au dépôt :

- `data/`, `exports/`, `*.db`, `logs/`, `output/`, `.venv/`, `models/`, `.cache/`, `error_logs/`, `README.pdf` non versionné.

Tu peux les régénérer ou les recréer selon les scripts (attention : perte de données locales).

---

## Synthèse “par dossier” (vue rapide)

| Dossier | Niveau par défaut | Commentaire nettoyage |
|---------|-------------------|------------------------|
| `src/` | **A** | Ne pas tronquer sans tests. |
| `main.py`, `sources_config.json`, `requirements.txt` | **A** | — |
| `.github/` | **B** | — |
| `tests/` | **B** | — |
| `scripts/` | **B** / **D** | Doublons OS et scripts morts → **D**. |
| `docs/` | **C** / **D** | Beaucoup de matière de preuve ; tri par ancienneté et doublons. |
| `docs/e2/` + `docs/veille/` | **C** / **D** | Attention aux doublons de veille. |
| `reports/` | **D** | Historique compressible. |
| `notebooks/` | **B** / **D** | — |
| `monitoring/` | **B** | — |
| `hadoop/` | **B** | Si Spark utilisé sous Windows. |
| `zzdb/` | **B** / **D** | Lab seulement. |

---

## Méthode conseillée avant de supprimer

1. `git grep "nom_du_fichier"` ou recherche du chemin dans `docs/` et `README*`.
2. Vérifier les workflows CI (références à des scripts ou chemins).
3. Branche `chore/nettoyage-YYYYMMDD`, suppressions par petits commits thématiques.
4. `pytest` (et tests API / Spark si concernés).

---

## Documents liés

- `INVENTAIRE_PROJET.md` — liste exhaustive des chemins versionnés.
- `FICHIERS_FONCTIONNELS.md` — vue “qu’est-ce qui exécute quoi” pour E1.
