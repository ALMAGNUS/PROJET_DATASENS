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


def filter_items(items: list[dict], keywords: list[str]) -> list[dict]:
    if not keywords:
        return items
    lowered = [k.lower() for k in keywords]
    filtered: list[dict] = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('link', '')}".lower()
        if any(k in text for k in lowered):
            filtered.append(item)
    return filtered


def fetch_source_items(src: dict) -> tuple[list[dict], str]:
    if src.get("enabled", True) is False:
        return [], "source_disabled"

    urls: list[str] = []
    main_url = src.get("url", "").strip()
    if main_url:
        urls.append(main_url)
    urls.extend([u for u in src.get("fallback_urls", []) if isinstance(u, str) and u.strip()])

    if not urls:
        return [], "missing_url"

    keywords = src.get("keywords", [])
    for candidate in urls:
        raw_items = fetch_feed(candidate)
        filtered = filter_items(raw_items, keywords)
        if filtered:
            return filtered, candidate
    return [], urls[0]


def build_snapshot(data: dict) -> dict:
    snapshot = {
        "theme": data.get("theme", ""),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "sources": [],
    }
    for src in data.get("sources", []):
        items, used_url = fetch_source_items(src)
        snapshot["sources"].append(
            {
                "name": src.get("name", ""),
                "url": src.get("url", ""),
                "source_url_used": used_url,
                "category": src.get("category", ""),
                "reliability": src.get("reliability", ""),
                "keywords": src.get("keywords", []),
                "items": items,
            }
        )
    return snapshot


def build_digest(snapshot: dict) -> str:
    lines = []
    lines.append("# Veille E2 - Synthèse")
    lines.append(f"Date: {snapshot.get('generated_at', '')}")
    lines.append("")
    for src in snapshot.get("sources", []):
        lines.append(f"## {src['name']} ({src['category']})")
        source_used = src.get("source_url_used", src.get("url", ""))
        if source_used.startswith("http"):
            lines.append(f"Source utilisée: [{source_used}]({source_used})")
        else:
            lines.append(f"Source utilisée: {source_used}")
        items = src.get("items", [])
        if not items:
            lines.append("- Aucun élément disponible")
        else:
            lines.append(f"- Nombre d'éléments retenus: {len(items)}")
            for item in items:
                title = item["title"] or "Titre indisponible"
                link = item["link"] or "Lien indisponible"
                if link.startswith("http"):
                    lines.append(f"- [{title}]({link})")
                else:
                    lines.append(f"- {title} — {link}")
        lines.append("")
    return "\n".join(lines)


def build_sources_catalog(data: dict) -> str:
    lines = []
    lines.append("# Annexe C6 - Sources et mots-clés de veille")
    lines.append(f"Thématique: {data.get('theme', '')}")
    lines.append(f"Mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    for src in data.get("sources", []):
        lines.append(f"## {src.get('name', '')}")
        lines.append(f"- URL: {src.get('url', '')}")
        lines.append(f"- Catégorie: {src.get('category', '')}")
        lines.append(f"- Fiabilité: {src.get('reliability', '')}")
        lines.append(f"- Activée: {src.get('enabled', True)}")
        fallback = src.get("fallback_urls", [])
        if fallback:
            lines.append("- URLs de secours:")
            for url in fallback:
                lines.append(f"  - {url}")
        keywords = src.get("keywords", [])
        if keywords:
            lines.append(f"- Mots-clés: {', '.join(keywords)}")
        else:
            lines.append("- Mots-clés: (aucun filtre)")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    project_root = Path(__file__).parent.parent
    config_path = Path(__file__).with_name("veille_sources.json")
    output_dir = project_root / "docs" / "veille"
    annex_dir = project_root / "docs" / "e2"
    output_dir.mkdir(parents=True, exist_ok=True)
    annex_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    output_path_md = output_dir / f"veille_{stamp}.md"
    output_path_json = output_dir / f"veille_{stamp}.json"
    annex_path_json = annex_dir / f"ANNEXE_C6_VEILLE_{stamp}.json"
    annex_path_md = annex_dir / f"ANNEXE_C6_VEILLE_{stamp}.md"
    annex_catalog_md = annex_dir / "ANNEXE_C6_SOURCES_MOTS_CLES.md"
    annex_catalog_json = annex_dir / "ANNEXE_C6_SOURCES_MOTS_CLES.json"

    config = load_sources(config_path)
    snapshot = build_snapshot(config)
    digest = build_digest(snapshot)
    catalog_md = build_sources_catalog(config)

    output_path_md.write_text(digest, encoding="utf-8")
    snapshot_json = json.dumps(snapshot, ensure_ascii=False, indent=2)
    config_json = json.dumps(config, ensure_ascii=False, indent=2)
    output_path_json.write_text(snapshot_json, encoding="utf-8")
    annex_path_json.write_text(snapshot_json, encoding="utf-8")
    annex_path_md.write_text(digest, encoding="utf-8")
    annex_catalog_md.write_text(catalog_md, encoding="utf-8")
    annex_catalog_json.write_text(config_json, encoding="utf-8")
    print(f"OK Veille générée (MD): {output_path_md}")
    print(f"OK Veille générée (JSON): {output_path_json}")
    print(f"OK Copie annexe dossier (MD): {annex_path_md}")
    print(f"OK Copie annexe dossier (JSON): {annex_path_json}")
    print(f"OK Annexe sources+mots-clés (MD): {annex_catalog_md}")
    print(f"OK Annexe sources+mots-clés (JSON): {annex_catalog_json}")


if __name__ == "__main__":
    main()
