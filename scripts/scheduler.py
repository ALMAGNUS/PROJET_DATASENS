"""E1 Pipeline scheduling with versioned GOLD aggregation."""
from datetime import datetime
from pathlib import Path

import pandas as pd


class ScheduledPipeline:
    """Manage E1 collections with versioning and data lake aggregation."""

    def __init__(self, exports_dir: str | None = None, lake_dir: str | None = None) -> None:
        base = Path(__file__).parent.parent
        self.exports_dir = Path(exports_dir) if exports_dir else base / 'exports'
        self.lake_dir = Path(lake_dir) if lake_dir else base / 'data' / 'lake'
        self.lake_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.lake_dir / "collection_log.txt"

    def run_collection(self, source: str = "all") -> None:
        """Run E1 pipeline and version GOLD exports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Read current GOLD export
        gold_path = self.exports_dir / "gold.csv"
        if not gold_path.exists():
            print(f"[WARN] No GOLD export found at {gold_path}")
            return

        df = pd.read_csv(gold_path)
        print(f"[{timestamp}] Collection '{source}': {len(df)} records -> aggregating to lake")

        # Store versioned export
        versioned_dir = self.lake_dir / f"version_{timestamp}"
        versioned_dir.mkdir(exist_ok=True)
        df.to_csv(versioned_dir / "gold.csv", index=False)
        df.to_parquet(versioned_dir / "gold.parquet", index=False)

        # Update consolidated lake
        consolidated = self.lake_dir / "consolidated.parquet"
        if consolidated.exists():
            existing = pd.read_parquet(consolidated)
            combined = pd.concat([existing, df], ignore_index=True).drop_duplicates(subset=['id'], keep='last')
            combined.to_parquet(consolidated, index=False)
        else:
            df.to_parquet(consolidated, index=False)

        # Log collection
        with open(self.log_file, "a") as f:
            f.write(f"{timestamp} | {source} | {len(df)} records\n")

        print(f"[OK] Versioned export: {versioned_dir}")
        print(f"[OK] Consolidated lake: {consolidated} ({len(df)} records)")


if __name__ == "__main__":
    # Example usage
    scheduler = ScheduledPipeline()
    scheduler.run_collection("daily_09:00")

