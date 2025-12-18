"""DataSens E1 - Repository Pattern (CRUD complet)"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from core import Article, DatabaseLoader, Source


class Repository(DatabaseLoader):
    """Extended DatabaseLoader with CRUD for topics and sentiment"""
    
    def __init__(self, db_path: str):
        """Initialize repository and ensure schema exists"""
        super().__init__(db_path)
        self._ensure_schema()
        self._ensure_sources()
    
    def _ensure_schema(self):
        """Create database schema if it doesn't exist"""
        try:
            # Check if tables exist
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='source'")
            if self.cursor.fetchone():
                return  # Schema already exists
            
            # Create 6 core tables
            sql_tables = """
            -- 1. SOURCE
            CREATE TABLE IF NOT EXISTS source (
                source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                source_type VARCHAR(50) NOT NULL,
                url VARCHAR(500),
                sync_frequency VARCHAR(50) DEFAULT 'DAILY',
                last_sync_date DATETIME,
                retry_policy VARCHAR(50) DEFAULT 'SKIP',
                active BOOLEAN DEFAULT 1,
                created_at DATETIME
            );
            
            -- 2. RAW_DATA
            CREATE TABLE IF NOT EXISTS raw_data (
                raw_data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL REFERENCES source(source_id),
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                url VARCHAR(500),
                fingerprint VARCHAR(64) UNIQUE,
                published_at DATETIME,
                collected_at DATETIME,
                quality_score FLOAT DEFAULT 0.5
            );
            CREATE INDEX IF NOT EXISTS idx_raw_data_source ON raw_data(source_id);
            CREATE INDEX IF NOT EXISTS idx_raw_data_collected ON raw_data(collected_at);
            
            -- 3. SYNC_LOG
            CREATE TABLE IF NOT EXISTS sync_log (
                sync_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL REFERENCES source(source_id),
                sync_date DATETIME,
                rows_synced INTEGER DEFAULT 0,
                status VARCHAR(50) NOT NULL,
                error_message TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sync_log_source ON sync_log(source_id);
            CREATE INDEX IF NOT EXISTS idx_sync_log_date ON sync_log(sync_date);
            
            -- 4. TOPIC
            CREATE TABLE IF NOT EXISTS topic (
                topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                keywords VARCHAR(500),
                category VARCHAR(50),
                active BOOLEAN DEFAULT 1
            );
            
            -- 5. DOCUMENT_TOPIC
            CREATE TABLE IF NOT EXISTS document_topic (
                doc_topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_data_id INTEGER NOT NULL REFERENCES raw_data(raw_data_id),
                topic_id INTEGER NOT NULL REFERENCES topic(topic_id),
                confidence_score FLOAT DEFAULT 0.5,
                tagger VARCHAR(100)
            );
            CREATE INDEX IF NOT EXISTS idx_doc_topic_raw ON document_topic(raw_data_id);
            CREATE INDEX IF NOT EXISTS idx_doc_topic_topic ON document_topic(topic_id);
            
            -- 6. MODEL_OUTPUT
            CREATE TABLE IF NOT EXISTS model_output (
                output_id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_data_id INTEGER NOT NULL REFERENCES raw_data(raw_data_id),
                model_name VARCHAR(100),
                label VARCHAR(100),
                score FLOAT DEFAULT 0.5,
                created_at DATETIME
            );
            CREATE INDEX IF NOT EXISTS idx_model_output_raw ON model_output(raw_data_id);
            """
            
            self.cursor.executescript(sql_tables)
            self.conn.commit()
        except Exception as e:
            print(f"   ⚠️  Schema initialization error: {str(e)[:60]}")
    
    def _ensure_sources(self):
        """Load sources from sources_config.json if they don't exist in DB"""
        try:
            # Check if sources already exist
            self.cursor.execute("SELECT COUNT(*) FROM source")
            if self.cursor.fetchone()[0] > 0:
                return  # Sources already exist
            
            # Load from config file
            config_path = Path(__file__).parent.parent / 'sources_config.json'
            if not config_path.exists():
                return  # Config file doesn't exist
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Insert sources
            for source_data in config.get('sources', []):
                source = Source(**source_data)
                try:
                    self.cursor.execute("""
                        INSERT INTO source (name, source_type, url, sync_frequency, active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        source.source_name,
                        source.acquisition_type,
                        source.url,
                        source.refresh_frequency or 'DAILY',
                        1 if source.active else 0,
                        datetime.now().isoformat()
                    ))
                except sqlite3.IntegrityError:
                    pass  # Source already exists
            
            self.conn.commit()
        except Exception as e:
            print(f"   ⚠️  Sources initialization error: {str(e)[:60]}")
    
    def load_article_with_id(self, article: Article, source_id: int) -> int | None:
        """Load article and return raw_data_id (or None if duplicate)"""
        try:
            fp = article.fingerprint()
            self.cursor.execute("SELECT raw_data_id FROM raw_data WHERE fingerprint = ?", (fp,))
            existing = self.cursor.fetchone()
            if existing:
                return None  # Duplicate
            
            self.cursor.execute("""
                INSERT INTO raw_data (source_id, title, content, url, fingerprint, published_at, collected_at, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (source_id, article.title, article.content, article.url, fp, 
                  article.published_at, datetime.now().isoformat(), 0.5))
            self.conn.commit()
            
            # Get inserted ID
            self.cursor.execute("SELECT raw_data_id FROM raw_data WHERE fingerprint = ?", (fp,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"   ⚠️  DB error: {str(e)[:40]}")
            return None

