"""Display database tables for jury presentation."""
import sqlite3
from pathlib import Path

import pandas as pd


class DatabaseViewer:
    """Minimal database viewer following SOLID & DRY principles."""

    def __init__(self, db_path: str) -> None:
        self.conn = sqlite3.connect(db_path)

    def show_table(self, table: str, limit: int | None = None) -> None:
        """Display table contents."""
        query = f"SELECT * FROM {table}" + (f" LIMIT {limit}" if limit else "")
        df = pd.read_sql(query, self.conn)
        print(f"\n{'='*80}\n{table.upper()} ({len(df)} rows)\n{'='*80}")
        print(df.to_string(index=False))

    def show_topics(self) -> None:
        """Display topics with tagged articles."""
        topics = pd.read_sql("SELECT topic_id, name FROM topic", self.conn)
        doc_topic = pd.read_sql(
            "SELECT topic_id, COUNT(DISTINCT raw_data_id) as count FROM document_topic GROUP BY topic_id",
            self.conn,
        )
        print(f"\n{'='*80}\nTOPICS WITH ARTICLES\n{'='*80}")
        for _, topic in topics.iterrows():
            tid = topic["topic_id"]
            tname = topic["name"]
            count = doc_topic[doc_topic["topic_id"] == tid]["count"].values[0]
            print(f"Topic {tid}: {tname:20s} -> {count:3d} articles")

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()


if __name__ == "__main__":
    db = DatabaseViewer(str(Path.home() / "datasens_project" / "datasens.db"))
    db.show_table("sync_log")
    db.show_topics()
    db.close()
