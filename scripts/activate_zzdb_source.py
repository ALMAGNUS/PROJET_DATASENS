#!/usr/bin/env python3
"""Activate zzdb_synthetic in SQLite source table."""
import os
import sqlite3
from pathlib import Path


def main() -> None:
    db_path = Path(os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db")))
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("UPDATE source SET active = 1 WHERE name = ?", ("zzdb_synthetic",))
    conn.commit()
    cur.execute("SELECT name, active FROM source WHERE name = ?", ("zzdb_synthetic",))
    print(cur.fetchone())
    conn.close()


if __name__ == "__main__":
    main()
