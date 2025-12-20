"""Data Aggregator - RAW/SILVER/GOLD (DB + fichiers locaux)"""
import json
import sqlite3
from pathlib import Path

import pandas as pd


class DataAggregator:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)

    def _collect_local_files(self) -> pd.DataFrame:
        """Collect GDELT files from local data/raw/ (ZZDB and Kaggle excluded: already in DB via extractors)"""
        data = []
        for p in [Path('data/raw'), Path.home() / 'datasens_project' / 'data' / 'raw', Path.home() / 'Desktop' / 'DEV IA 2025' / 'PROJET_DATASENS' / 'data' / 'raw']:
            if not p.exists(): continue
            # ZZDB and Kaggle sources excluded: they are already in DB (via CSVExtractor/SQLiteExtractor/KaggleExtractor)
            # Only collect GDELT files that are not in DB (GDELT peut être lu directement depuis fichiers locaux)
            for gdelt_dir in p.glob('gdelt_*'):
                if not gdelt_dir.is_dir(): continue
                for json_file in gdelt_dir.rglob('*.json'):
                    try:
                        with open(json_file, encoding='utf-8') as f:
                            raw = json.load(f)
                            items = raw if isinstance(raw, list) else (raw.get('items', []) if isinstance(raw, dict) else [])
                            for item in items:
                                if isinstance(item, dict):
                                    title = item.get('title') or item.get('headline') or ''
                                    content = item.get('content') or item.get('text') or item.get('description') or ''
                                    if len(title) > 3:
                                        data.append({'source': gdelt_dir.name, 'title': title[:500], 'content': content[:2000] if content else title[:2000], 'url': item.get('url', ''), 'collected_at': ''})
                    except: pass
        return pd.DataFrame(data) if data else pd.DataFrame(columns=['source', 'title', 'content', 'url', 'collected_at'])

    def aggregate_raw(self) -> pd.DataFrame:
        """RAW: DB + fichiers locaux (sans enrichissement)"""
        df_db = pd.read_sql_query("SELECT r.raw_data_id as id, s.name as source, r.title, r.content, r.url, r.fingerprint, r.collected_at, r.quality_score FROM raw_data r JOIN source s ON r.source_id = s.source_id ORDER BY r.collected_at DESC", self.conn)
        # Classification des sources : ZZDB = DB non relationnelle, Kaggle = fichiers plats
        def classify_source(x):
            x_lower = str(x).lower()
            if 'zzdb' in x_lower:
                return 'db_non_relational'  # Base de données non relationnelle
            elif 'kaggle' in x_lower:
                return 'flat_files'  # Fichiers plats
            else:
                return 'real_source'  # Source réelle

        df_db['source_type'] = df_db['source'].apply(classify_source)
        local_df = self._collect_local_files()
        if not local_df.empty:
            local_df['id'] = range(len(df_db), len(df_db) + len(local_df)) if not df_db.empty else range(len(local_df))
            local_df['fingerprint'] = ''
            local_df['quality_score'] = 0.5
            local_df['source_type'] = local_df['source'].apply(classify_source)
            df = pd.concat([df_db, local_df], ignore_index=True)
        else:
            df = df_db
        return df

    def aggregate_silver(self) -> pd.DataFrame:
        """SILVER: RAW + topics (sans sentiment) - TOUJOURS 2 topics par article"""
        df = self.aggregate_raw()
        # S'assurer que source_type est présent
        if 'source_type' not in df.columns:
            df['source_type'] = df['source'].apply(lambda x: 'academic' if 'zzdb' in str(x).lower() else 'real')
        topics = pd.read_sql_query("SELECT dt.raw_data_id, t.name as topic_name, dt.confidence_score, ROW_NUMBER() OVER (PARTITION BY dt.raw_data_id ORDER BY dt.confidence_score DESC) as rn FROM document_topic dt JOIN topic t ON dt.topic_id = t.topic_id", self.conn)
        t1 = topics[topics['rn'] == 1][['raw_data_id', 'topic_name', 'confidence_score']].rename(columns={'topic_name': 'topic_1', 'confidence_score': 'topic_1_score'})
        t2 = topics[topics['rn'] == 2][['raw_data_id', 'topic_name', 'confidence_score']].rename(columns={'topic_name': 'topic_2', 'confidence_score': 'topic_2_score'})
        df = df.merge(t1, left_on='id', right_on='raw_data_id', how='left').merge(t2, left_on='id', right_on='raw_data_id', how='left')
        df = df.drop(columns=[c for c in df.columns if 'raw_data_id' in c], errors='ignore')

        # GARANTIR topic_2 : Si topic_2 est vide mais topic_1 existe, assigner "autre" comme topic_2
        mask_topic2_empty = df['topic_2'].isna() | (df['topic_2'] == '')
        mask_topic1_exists = df['topic_1'].notna() & (df['topic_1'] != '')
        mask_fill_topic2 = mask_topic2_empty & mask_topic1_exists

        df.loc[mask_fill_topic2, 'topic_2'] = 'autre'
        df.loc[mask_fill_topic2, 'topic_2_score'] = 0.1  # Confiance faible pour fallback

        # Fillna pour les cas où topic_1 est aussi vide
        df[['topic_1', 'topic_2']] = df[['topic_1', 'topic_2']].fillna('')
        df[['topic_1_score', 'topic_2_score']] = df[['topic_1_score', 'topic_2_score']].fillna(0.0)
        return df

    def aggregate(self) -> pd.DataFrame:
        """GOLD: SILVER + sentiment"""
        df = self.aggregate_silver()
        # S'assurer que source_type est présent
        if 'source_type' not in df.columns:
            df['source_type'] = df['source'].apply(lambda x: 'academic' if 'zzdb' in str(x).lower() else 'real')
        sentiment = pd.read_sql_query("SELECT raw_data_id, label as sentiment, score as sentiment_score FROM model_output WHERE model_name = 'sentiment_keyword'", self.conn)
        df = df.merge(sentiment, left_on='id', right_on='raw_data_id', how='left')
        df = df.drop(columns=[c for c in df.columns if 'raw_data_id' in c], errors='ignore')
        df['sentiment'] = df['sentiment'].fillna('neutre')
        df['sentiment_score'] = df['sentiment_score'].fillna(0.5)
        return df

    def close(self):
        self.conn.close()

