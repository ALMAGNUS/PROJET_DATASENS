# Preuve d'enrichissement du pipeline DataSens

- Généré (UTC) : `2026-05-24T103005Z`
- Rapport courant : `db_state_2026-05-24T101213Z.json` (`2026-05-24T10:12:12.012133+00:00`)
- Rapport précédent : `db_state_2026-05-23T072248Z.json` (`2026-05-23T07:22:47.037268+00:00`)
- Cohérence technique : **OK**

## Lignes ajoutées par étape

| Étape | Avant | Après | Delta | Chemin | Détail |
|---|---:|---:|---:|---|---|
| 1. SQLite raw_data (buffer) | 54,120 | 54,264 | **+144** | `datasens.db · table raw_data` | Ingestion + dédup fingerprint. Source de vérité buffer. |
| 2. GOLD partition (jour, export enrichi) | 54,120 | 54,264 | **+144** | `data/gold/date=2026-05-24/articles.parquet` | Export parquet régénéré (sentiment_keyword + topics). Delta = nouvelles lignes raw_data enrichies ce run (+144). |
| 3. GoldAI fusion long terme | 90,283 | 90,427 | **+144** | `data/goldai/merged_all_dates.parquet` | Stock long terme dédupliqué par id. |
| 4. IA splits (train+val+test) | 21,785 | 21,901 | **+116** | `data/goldai/ia/{train,val,test}.parquet` | train=17,520 · val=2,190 · test=2,191 |
| 5. MongoDB (transferts) | 0 | 2,833 | **+2,833** | `MongoDB · sync_log (rows_synced, status=OK)` | 26 synchronisations OK entre les deux rapports (depuis 2026-05-23T07:22:47.037268+00:00). |

## Deltas par source (raw_data)

| Source | Delta | Total courant |
|---|---:|---:|
| `yahoo_finance` | +47 | 4,214 |
| `google_news_rss` | +38 | 3,988 |
| `rss_french_news` | +24 | 2,022 |
| `reddit_france` | +23 | 1,937 |
| `openweather_api` | +5 | 568 |
| `GDELT_Last15_English` | +4 | 216 |
| `datagouv_datasets` | +3 | 968 |