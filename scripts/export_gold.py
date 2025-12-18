"""Gold dataset export & PySpark integration demo."""
import pandas as pd
from pathlib import Path


class GoldDatasetManager:
    """Handle GOLD zone export and PySpark simulation."""

    def __init__(self, gold_path: str) -> None:
        self.gold_path = Path(gold_path)
        self.export_dir = Path(__file__).parent.parent / 'exports'
        self.export_dir.mkdir(exist_ok=True)

    def export_for_download(self) -> str:
        """Export GOLD dataset to CSV for transmission."""
        df = pd.read_parquet(self.gold_path)
        export_file = self.export_dir / "gold_articles.csv"
        df.to_csv(export_file, index=False)
        return str(export_file)

    def show_stats(self) -> None:
        """Show GOLD dataset statistics."""
        df = pd.read_parquet(self.gold_path)
        print(f"\n{'='*60}\nGOLD DATASET STATS\n{'='*60}")
        print(f"Total articles:  {len(df)}")
        print(f"Columns:         {len(df.columns)}")
        print(f"File size:       {self.gold_path.stat().st_size / 1024:.1f} KB")
        print(f"Export file:     {self.export_dir / 'gold_articles.csv'}")

    def simulate_enrichment(self, new_records: int = 200) -> None:
        """Simulate new collection + enrichment."""
        df = pd.read_parquet(self.gold_path)
        initial = len(df)
        
        # Simulate 200 new articles
        new_df = df.head(new_records).copy()
        enriched = pd.concat([df, new_df], ignore_index=True)
        
        print(f"\n{'='*60}\nENRICHMENT SIMULATION\n{'='*60}")
        print(f"Initial GOLD:    {initial} articles")
        print(f"New collection:  {new_records} articles")
        print(f"After merge:     {len(enriched)} articles")
        print(f"Growth:          +{len(enriched) - initial} ({100*(len(enriched)-initial)/initial:.1f}%)")


if __name__ == "__main__":
    gold_path = Path(__file__).parent.parent / 'data' / 'gold' / 'date=2025-12-18' / 'articles.parquet'
    if gold_path.exists():
        mgr = GoldDatasetManager(str(gold_path))
        mgr.show_stats()
    else:
        print(f"[ERROR] Gold file not found: {gold_path}")

