"""Force la migration SQLite (index UNIQUE document_topic) sur la base existante."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from src.e1.repository import Repository

db = str(Path.home() / "datasens_project" / "datasens.db")
print(f"Connexion: {db}")
r = Repository(db)

# Verifier que l'index est bien la maintenant
idx = r.cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_doc_topic_unique'"
).fetchone()
print(f"idx_doc_topic_unique: {idx}")
fk = r.cursor.execute("PRAGMA foreign_keys").fetchone()[0]
print(f"foreign_keys: {fk}")
r.conn.close()
print("Migration OK")
