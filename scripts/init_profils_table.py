"""
Script pour initialiser la table PROFILS
=========================================
Crée la table PROFILS si elle n'existe pas
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings, get_data_dir

settings = get_settings()
db_path = settings.db_path
if not db_path.startswith("/") and not db_path.startswith("C:"):
    db_path = str(get_data_dir().parent / db_path)

print(f"Initialisation table PROFILS dans: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Vérifier si la table existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profils'")
    if cursor.fetchone():
        print("Table PROFILS existe deja.")
    else:
        print("Creation table PROFILS...")
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
        cursor.executescript(sql_profils)
        conn.commit()
        print("OK: Table PROFILS et user_action_log creees.")
except Exception as e:
    print(f"ERREUR: {e}")
    conn.rollback()
finally:
    conn.close()
