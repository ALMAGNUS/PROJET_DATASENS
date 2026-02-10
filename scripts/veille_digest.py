"""
Veille C6 - agrégation RSS et génération de synthèse.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import feedparser


def load_sources(config_path: Path) -> dict:
    return json.loads(config_path.read_text(encoding="utf-8"))


def fetch_feed(url: str) -> list[dict]:
    feed = feedparser.parse(url)
    items: list[dict] = []
    for entry in feed.entries[:10]:
        items.append(
            {
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", "").strip(),
                "published": entry.get("published", "").strip(),
            }
        )
    return items


def build_digest(data: dict) -> str:
    lines = []
    lines.append("# Veille E2 - Synthèse")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    for src in data.get("sources", []):
        lines.append(f"## {src['name']} ({src['category']})")
        items = fetch_feed(src["url"])
        if not items:
            lines.append("- Aucun élément disponible")
        else:
            for item in items:
                title = item["title"] or "Titre indisponible"
                link = item["link"] or "Lien indisponible"
                lines.append(f"- {title} — {link}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    project_root = Path(__file__).parent.parent
    config_path = Path(__file__).with_name("veille_sources.json")
    output_dir = project_root / "docs" / "veille"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"veille_{datetime.now().strftime('%Y-%m-%d')}.md"

    config = load_sources(config_path)
    digest = build_digest(config)
    output_path.write_text(digest, encoding="utf-8")
    print(f"OK Veille générée: {output_path}")


if __name__ == "__main__":
    main()
