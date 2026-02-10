"""
Audit E1 coverage from scripts only (no docs).
Scans scripts/*.py and reports evidence for each criterion.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Criterion:
    code: str
    label: str
    patterns: list[str]


CRITERIA: list[Criterion] = [
    Criterion(
        code="C1.HTTP",
        label="Requetes HTTP service web (REST)",
        patterns=[r"requests\.get\(", r"httpx\.", r"feedparser\.parse\("],
    ),
    Criterion(
        code="C1.HTML",
        label="Telechargement HTML + scraping",
        patterns=[r"BeautifulSoup", r"\.text", r"lxml"],
    ),
    Criterion(
        code="C1.FILES",
        label="Lecture fichiers donnees (CSV/JSON/Parquet)",
        patterns=[r"read_csv\(", r"read_json\(", r"read_parquet\("],
    ),
    Criterion(
        code="C1.DB",
        label="Connexion DB (SQLite/Mongo)",
        patterns=[r"sqlite3\.connect\(", r"MongoClient\("],
    ),
    Criterion(
        code="C1.BIGDATA",
        label="Connexion systeme Big Data (PySpark)",
        patterns=[r"pyspark", r"SparkSession", r"spark\.read\.parquet"],
    ),
    Criterion(
        code="C1.PARSE",
        label="Parsing/filtrage donnees (API/fichiers/HTML)",
        patterns=[r"find_all\(", r"select\(", r"json\.load", r"filter\(", r"\.get\("],
    ),
    Criterion(
        code="C1.SQL",
        label="Requetes SQL d'extraction (SQLite)",
        patterns=[r"SELECT ", r"read_sql_query\(", r"execute\("],
    ),
    Criterion(
        code="C2.SQL_DOC",
        label="Requetes SQL documentees (dans scripts)",
        patterns=[r"--", r"EXPLAIN QUERY PLAN"],
    ),
    Criterion(
        code="C3.AGG",
        label="Agrégation multi-sources",
        patterns=[r"aggregate_raw", r"aggregate_silver", r"aggregate\("],
    ),
    Criterion(
        code="C3.CLEAN",
        label="Nettoyage / suppression entrees corrompues",
        patterns=[r"is_valid", r"drop", r"fillna", r"len\("],
    ),
    Criterion(
        code="C3.NORMALIZE",
        label="Homogeneisation formats (dates/units)",
        patterns=[r"to_datetime\(", r"normalize", r"strftime"],
    ),
    Criterion(
        code="C4.DB_CREATE",
        label="Creation base + schema",
        patterns=[r"CREATE TABLE", r"setup_with_sql", r"_ensure_schema"],
    ),
    Criterion(
        code="C4.IMPORT",
        label="Script d'import en base",
        patterns=[r"INSERT INTO", r"load_article", r"load_article_with_id"],
    ),
    Criterion(
        code="C5.API",
        label="API REST (CRUD)",
        patterns=[r"FastAPI", r"APIRouter", r"@router\."],
    ),
    Criterion(
        code="C5.RBAC",
        label="Autorisation / RBAC",
        patterns=[r"require_reader", r"require_writer", r"require_deleter"],
    ),
]


def iter_project_files(project_root: Path) -> Iterable[Path]:
    targets = [
        project_root / "scripts",
        project_root / "src",
    ]
    for base in targets:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if path.name in {"dossier_e1_examples.py", "audit_e1_coverage.py"}:
                continue
            yield path


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def main() -> None:
    project_root = Path(__file__).parent.parent
    files = list(iter_project_files(project_root))
    texts = {p: load_text(p) for p in files}

    print("E1 AUDIT (project-wide)")
    print("=" * 70)
    print(f"Python files scanned: {len(files)}")
    print()

    for criterion in CRITERIA:
        matched_files: list[str] = []
        for path, text in texts.items():
            if not text:
                continue
            for pattern in criterion.patterns:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    matched_files.append(path.name)
                    break
        status = "OK" if matched_files else "MISSING"
        print(f"[{status}] {criterion.code} - {criterion.label}")
        if matched_files:
            print(f"   -> {', '.join(sorted(set(matched_files)))}")
        print()


if __name__ == "__main__":
    main()
