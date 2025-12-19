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
            schema_exists = self.cursor.fetchone()
            
            if not schema_exists:
                # Create 6 core tables E1
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
            
            # Migration : Ajouter table PROFILS si elle n'existe pas (compatible avec schéma existant)
            self._ensure_profils_table()
            
        except Exception as e:
            print(f"   ⚠️  Schema initialization error: {str(e)[:60]}")
    
    def _ensure_sources(self):
        """Load sources from sources_config.json - Add missing sources even if some exist"""
        try:
            # Load from config file
            config_path = Path(__file__).parent.parent / 'sources_config.json'
            if not config_path.exists():
                return  # Config file doesn't exist
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Get existing source names
            self.cursor.execute("SELECT name FROM source")
            existing_names = {row[0] for row in self.cursor.fetchall()}
            
            # Insert missing sources
            for source_data in config.get('sources', []):
                source = Source(**source_data)
                
                # Skip if source already exists
                if source.source_name in existing_names:
                    continue
                
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
                return None  # Duplicate (déduplication normale)
            
            # GARDE-FOU ZZDB: Qualité réduite pour données synthétiques (0.3 au lieu de 0.5)
            quality_score = 0.3 if article.source_name and 'zzdb' in article.source_name.lower() else 0.5
            
            self.cursor.execute("""
                INSERT INTO raw_data (source_id, title, content, url, fingerprint, published_at, collected_at, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (source_id, article.title, article.content, article.url, fp, 
                  article.published_at, datetime.now().isoformat(), quality_score))
            self.conn.commit()
            
            # Get inserted ID
            self.cursor.execute("SELECT raw_data_id FROM raw_data WHERE fingerprint = ?", (fp,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except sqlite3.IntegrityError as e:
            # UNIQUE constraint failed sur fingerprint = déduplication normale (race condition)
            # Ne pas afficher l'erreur, c'est attendu
            if 'fingerprint' in str(e).lower() or 'unique' in str(e).lower():
                return None  # Duplicate (silencieux)
            # Autre erreur d'intégrité : afficher
            print(f"   ⚠️  DB integrity error: {str(e)[:40]}")
            return None
        except Exception as e:
            # Autre erreur : afficher
            print(f"   ⚠️  DB error: {str(e)[:40]}")
            return None
    
    def log_foundation_integration(self, source_id: int, source_name: str, source_type: str, 
                                   file_path: str = None, file_size: int = None, 
                                   rows_integrated: int = 0, status: str = 'INTEGRATED', 
                                   notes: str = None) -> bool:
        """Log l'intégration d'une source statique (fondation) via sync_log (table E1)"""
        try:
            # Utiliser sync_log avec status='FOUNDATION_INTEGRATED' pour les fondations
            notes_full = f"FONDATION: {source_name} ({source_type})"
            if file_path:
                notes_full += f" | File: {file_path}"
            if notes:
                notes_full += f" | {notes}"
            
            self.log_sync(source_id, rows_integrated, 'FOUNDATION_INTEGRATED', notes_full)
            return True
        except Exception as e:
            print(f"   ⚠️  Foundation log error: {str(e)[:40]}")
            return False
    
    def is_foundation_integrated(self, source_name: str) -> bool:
        """Vérifie si une source statique (fondation) a déjà été intégrée via sync_log"""
        try:
            self.cursor.execute("""
                SELECT COUNT(*) 
                FROM sync_log sl
                JOIN source s ON sl.source_id = s.source_id
                WHERE s.name = ? AND sl.status = 'FOUNDATION_INTEGRATED'
            """, (source_name,))
            count = self.cursor.fetchone()[0]
            return count > 0
        except:
            # Fallback: vérifier si des articles existent déjà pour cette source
            try:
                self.cursor.execute("""
                    SELECT COUNT(*) 
                    FROM raw_data r
                    JOIN source s ON r.source_id = s.source_id
                    WHERE s.name = ?
                """, (source_name,))
                count = self.cursor.fetchone()[0]
                return count > 0
            except:
                return False
    
    def _ensure_profils_table(self):
        """Create PROFILS table if it doesn't exist (migration-safe, isolated from E1 tables)"""
        try:
            # Check if profils table already exists
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profils'")
            if self.cursor.fetchone():
                return  # Table already exists
            
            # Create PROFILS table (isolated, no FK in E1 tables)
            sql_profils = """
            CREATE TABLE IF NOT EXISTS profils (
                profil_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                firstname VARCHAR(100) NOT NULL,
                lastname VARCHAR(100) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK(role IN ('reader', 'writer', 'deleter', 'admin')),
                active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                username VARCHAR(50) UNIQUE
            );
            
            CREATE INDEX IF NOT EXISTS idx_profils_email ON profils(email);
            CREATE INDEX IF NOT EXISTS idx_profils_role ON profils(role);
            CREATE INDEX IF NOT EXISTS idx_profils_active ON profils(active);
            
            CREATE TABLE IF NOT EXISTS user_action_log (
                action_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                profil_id INTEGER NOT NULL REFERENCES profils(profil_id) ON DELETE CASCADE,
                action_type VARCHAR(50) NOT NULL,
                resource_type VARCHAR(50) NOT NULL,
                resource_id INTEGER,
                action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                details TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_action_log_profil ON user_action_log(profil_id);
            CREATE INDEX IF NOT EXISTS idx_action_log_date ON user_action_log(action_date);
            CREATE INDEX IF NOT EXISTS idx_action_log_type ON user_action_log(action_type);
            """
            
            self.cursor.executescript(sql_profils)
            self.conn.commit()
        except Exception as e:
            print(f"   ⚠️  Profils table creation error: {str(e)[:60]}")
    
    def log_user_action(self, profil_id: int, action_type: str, 
                       resource_type: str, resource_id: int | None = None,
                       ip_address: str | None = None, details: str | None = None) -> bool:
        """Log user action in USER_ACTION_LOG (audit trail) - Isolated from E1 tables"""
        try:
            self.cursor.execute("""
                INSERT INTO user_action_log 
                (profil_id, action_type, resource_type, resource_id, ip_address, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (profil_id, action_type, resource_type, resource_id, ip_address, details))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"   ⚠️  Action log error: {str(e)[:60]}")
            return False

