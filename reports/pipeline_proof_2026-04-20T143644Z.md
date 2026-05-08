# Preuve d'enrichissement du pipeline DataSens

- Généré (UTC) : `2026-04-20T143644Z`
- Rapport courant : `db_state_2026-04-20T101008Z.json` (`2026-04-20T10:10:08.012467+00:00`)
- Rapport précédent : `db_state_2026-04-20T095836Z.json` (`2026-04-20T09:58:35.714910+00:00`)
- Cohérence technique : **OK**

## Lignes ajoutées par étape

| Étape | Avant | Après | Delta | Chemin | Détail |
|---|---:|---:|---:|---|---|
| 1. SQLite raw_data (buffer) | 48,707 | 48,798 | **+91** | `datasens.db · table raw_data` | Ingestion + dédup fingerprint. Source de vérité buffer. |
| 2. GOLD partition (jour, export enrichi) | 49,100 | 49,191 | **+91** | `data/gold/date=2026-04-20/articles.parquet` | Export parquet régénéré (sentiment_keyword + topics). Delta = nouvelles lignes raw_data enrichies ce run (+91). |
| 3. GoldAI fusion long terme | 75,709 | 75,709 | **+0** | `data/goldai/merged_all_dates.parquet` | Stock long terme dédupliqué par id. |
| 4. IA splits (train+val+test) | 75,709 | 75,709 | **+0** | `data/goldai/ia/{train,val,test}.parquet` | train=60,567 · val=7,570 · test=7,572 |
| 5. MongoDB (transferts) | 0 | 3,991 | **+3,991** | `MongoDB · sync_log (rows_synced, status=OK)` | 30 synchronisations OK entre les deux rapports (depuis 2026-04-20T09:58:35.714910+00:00). |

## Deltas par source (raw_data)

| Source | Delta | Total courant |
|---|---:|---:|
| `reddit_france` | +32 | 1,000 |
| `yahoo_finance` | +20 | 2,759 |
| `trustpilot_reviews` | +16 | 907 |
| `google_news_rss` | +15 | 2,533 |
| `openweather_api` | +5 | 361 |
| `rss_french_news` | +3 | 1,282 |