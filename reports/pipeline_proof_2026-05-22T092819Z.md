# Preuve d'enrichissement du pipeline DataSens

- Généré (UTC) : `2026-05-22T092819Z`
- Rapport courant : `db_state_2026-05-22T061533Z.json` (`2026-05-22T06:15:31.379654+00:00`)
- Rapport précédent : `db_state_2026-05-21T064615Z.json` (`2026-05-21T06:46:13.325433+00:00`)
- Cohérence technique : **OK**

## Lignes ajoutées par étape

| Étape | Avant | Après | Delta | Chemin | Détail |
|---|---:|---:|---:|---|---|
| 1. SQLite raw_data (buffer) | 53,795 | 53,961 | **+166** | `datasens.db · table raw_data` | Ingestion + dédup fingerprint. Source de vérité buffer. |
| 2. GOLD partition (jour, export enrichi) | 53,795 | 53,961 | **+166** | `data/gold/date=2026-05-22/articles.parquet` | Export parquet régénéré (sentiment_keyword + topics). Delta = nouvelles lignes raw_data enrichies ce run (+166). |
| 3. GoldAI fusion long terme | 89,958 | 90,124 | **+166** | `data/goldai/merged_all_dates.parquet` | Stock long terme dédupliqué par id. |
| 4. IA splits (train+val+test) | 21,527 | 21,657 | **+130** | `data/goldai/ia/{train,val,test}.parquet` | train=17,325 · val=2,165 · test=2,167 |
| 5. MongoDB (transferts) | 0 | 2,814 | **+2,814** | `MongoDB · sync_log (rows_synced, status=OK)` | 26 synchronisations OK entre les deux rapports (depuis 2026-05-21T06:46:13.325433+00:00). |

## Deltas par source (raw_data)

| Source | Delta | Total courant |
|---|---:|---:|
| `yahoo_finance` | +42 | 4,122 |
| `google_news_rss` | +38 | 3,912 |
| `datagouv_datasets` | +30 | 947 |
| `reddit_france` | +25 | 1,888 |
| `rss_french_news` | +24 | 1,974 |
| `openweather_api` | +5 | 558 |
| `GDELT_Last15_English` | +2 | 209 |