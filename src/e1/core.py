"""DataSens E1 - CORE ENGINE (SENIOR MODE - DRY/SOLID - 220 LIGNES)"""
import csv
import hashlib
import re
import sqlite3
import unicodedata
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from io import StringIO

import feedparser
import requests
from bs4 import BeautifulSoup
from loguru import logger

# Suppress BeautifulSoup warnings
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")
warnings.filterwarnings("ignore", message=".*looks more like a filename.*", category=UserWarning)


@dataclass
class Article:
    title: str
    content: str
    url: str | None = None
    source_name: str | None = None
    published_at: str | None = None

    def fingerprint(self) -> str:
        return hashlib.sha256(f"{self.title}|{self.content}".lower().encode()).hexdigest()

    def is_valid(self) -> bool:
        return len(self.title.strip()) > 3 and len(self.content.strip()) > 10


@dataclass
class Source:
    source_name: str
    acquisition_type: str
    url: str
    description: str = ""
    theme: str = "general"
    partition_path: str = ""
    file_naming: str = ""
    refresh_frequency: str = ""
    active: bool = True


class BaseExtractor(ABC):
    def __init__(self, name: str, url: str):
        self.name, self.url = name, url

    @abstractmethod
    def extract(self) -> list[Article]:
        pass


class RSSExtractor(BaseExtractor):
    def extract(self) -> list[Article]:
        articles = []
        try:
            feed = feedparser.parse(self.url)
            if feed.bozo and feed.bozo_exception:
                logger.warning(
                    "RSS parse error for {}: {}", self.name, str(feed.bozo_exception)[:40]
                )
            for entry in feed.entries[:50]:
                title = entry.get("title", "").strip()
                content = entry.get("summary", "") or entry.get("description", "")
                url = entry.get("link", "")
                if title and (content or title):
                    a = Article(
                        title=title[:500],
                        content=content[:2000] if content else title[:2000],
                        url=url,
                        source_name=self.name,
                        published_at=entry.get("published", ""),
                    )
                    if a.is_valid():
                        articles.append(a)
        except Exception as e:
            logger.error("RSS extraction error for {}: {}", self.name, str(e)[:40])
        return articles


class APIExtractor(BaseExtractor):
    def extract(self) -> list[Article]:
        articles, src_low = [], self.name.lower()
        try:
            if "reddit" in src_low:
                for sr in ["france", "actualites"]:
                    try:
                        # Try JSON API first
                        resp = requests.get(
                            f"https://www.reddit.com/r/{sr}/top.json?t=week&limit=25",
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                            },
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            data = resp.json().get("data", {}).get("children", [])
                            for post in data[:15]:
                                pd = post.get("data", {})
                                if pd.get("title") and pd.get("score", 0) > 5:
                                    a = Article(
                                        title=f"[{sr.upper()}] {pd['title']}"[:500],
                                        content=pd.get("selftext", "")[:2000]
                                        or f"Discussion #{pd['score']}",
                                        url=f"https://www.reddit.com{pd.get('permalink', '')}",
                                        source_name=self.name,
                                    )
                                    if a.is_valid() and a.url:
                                        articles.append(a)
                        else:
                            # Fallback: HTML scraping
                            html_resp = requests.get(
                                f"https://www.reddit.com/r/{sr}/top/?t=week",
                                headers={
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                                },
                                timeout=10,
                            )
                            if html_resp.status_code == 200:
                                soup = BeautifulSoup(html_resp.text, "html.parser")
                                for item in soup.find_all(["a"], {"data-testid": "post-title"})[
                                    :15
                                ]:
                                    title = item.get_text().strip()
                                    href = item.get("href", "")
                                    if title and href:
                                        a = Article(
                                            title=f"[{sr.upper()}] {title}"[:500],
                                            content=f"Reddit post from r/{sr}"[:2000],
                                            url=f"https://www.reddit.com{href}"
                                            if href.startswith("/")
                                            else href,
                                            source_name=self.name,
                                        )
                                        if a.is_valid():
                                            articles.append(a)
                    except Exception as e:
                        logger.warning("Reddit {} extraction error: {}", sr, str(e)[:40])
            elif "insee" in src_low or "citoyen" in src_low:
                soup = BeautifulSoup(
                    requests.get(
                        "https://www.monaviscitoyen.fr/",
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=10,
                    ).text,
                    "html.parser",
                )
                for item in soup.find_all(
                    ["article", "div"], class_=re.compile(r".*avis|opinion.*", re.I)
                )[:30]:
                    text = item.get_text(separator=" ").strip()
                    if len(text) > 20:
                        a = Article(
                            title=text[:100],
                            content=text[:2000],
                            url="https://www.monaviscitoyen.fr/",
                            source_name=self.name,
                        )
                        if a.is_valid():
                            articles.append(a)
            elif "weather" in src_low or "meteo" in src_low:
                for city in ["Paris", "Lyon", "Marseille", "Toulouse", "Nice"]:
                    try:
                        g_r = requests.get(
                            f"https://geocoding-api.open-meteo.com/v1/search?name={city}&country=France&language=fr&limit=1",
                            timeout=8,
                        ).json()
                        if g_r.get("results"):
                            g = g_r["results"][0]
                            w = requests.get(
                                f"https://api.open-meteo.com/v1/forecast?latitude={g['latitude']}&longitude={g['longitude']}&current=temperature_2m,weather_code&timezone=auto",
                                timeout=8,
                            ).json()
                            c = w.get("current", {})
                            a = Article(
                                title=f"Météo {city}: {c.get('temperature_2m', 'N/A')}C",
                                content=f"Condition: {c.get('weather_code', 'N/A')}, {g.get('name', city)}",
                                url=f"https://www.weather.com/weather/today/l/{g['latitude']},{g['longitude']}",
                                source_name=self.name,
                            )
                            if a.is_valid():
                                articles.append(a)
                    except:
                        pass
            else:
                resp = requests.get(self.url, timeout=5)
                if resp.status_code == 200 and "json" in resp.headers.get("content-type", ""):
                    payload = resp.json()

                    # Source Agora (consultations citoyennes)
                    if "agora" in self.name.lower() or "agora" in self.url.lower():
                        for item in (payload.get("ongoing") or []) + (
                            payload.get("finished") or []
                        ):
                            title = item.get("title", "")
                            theme = (item.get("thematique") or {}).get("label", "")
                            territory = item.get("territory", "")
                            end_date = item.get("endDate", "")
                            slug = item.get("slug", "")
                            url = (
                                f"https://www.participation-citoyenne.gouv.fr/consultations/{slug}"
                                if slug
                                else self.url
                            )
                            content = f"Theme: {theme}. Territoire: {territory}. Fin: {end_date}."
                            a = Article(
                                title=f"[AGORA] {title}"[:500],
                                content=content[:2000],
                                url=url,
                                source_name=self.name,
                            )
                            if a.is_valid():
                                articles.append(a)
                    else:
                        for item in (
                            payload.get("articles")
                            or payload.get("items")
                            or payload.get("results")
                            or []
                        )[:50]:
                            a = Article(
                                title=item.get("title", "")[:500],
                                content=item.get("content", "")[:2000],
                                url=item.get("url", ""),
                                source_name=self.name,
                            )
                            if a.is_valid():
                                articles.append(a)
        except Exception as e:
            logger.error("API extraction error for {}: {}", self.name, str(e)[:40])
        return articles[:50]


class ScrapingExtractor(BaseExtractor):
    def extract(self) -> list[Article]:
        articles, src_low = [], self.name.lower()
        try:
            if "trustpilot" in src_low:
                soup = BeautifulSoup(
                    requests.get(
                        "https://www.trustpilot.com",
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=10,
                    ).text,
                    "html.parser",
                )
                for review in soup.find_all(
                    ["article", "div"], class_=re.compile(r".*review|rating.*", re.I)
                )[:30]:
                    title = review.find(["h2", "h3", "h1"])
                    if title:
                        a = Article(
                            title=f"[TRUSTPILOT] {title.get_text().strip()}"[:500],
                            content=review.get_text().strip()[:2000],
                            url="https://www.trustpilot.com",
                            source_name=self.name,
                        )
                        if a.is_valid():
                            articles.append(a)
            elif "ifop" in src_low:
                soup = BeautifulSoup(
                    requests.get(
                        "https://www.ifop.com/?rubrique=fiches-signalitiques",
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=10,
                    ).text,
                    "html.parser",
                )
                for item in soup.find_all(
                    ["div", "article", "li"], class_=re.compile(r".*sondage|barometre.*", re.I)
                )[:30]:
                    title_e = item.find(["h2", "h3", "h4", "a"])
                    if title_e and title_e.get_text().strip():
                        a = Article(
                            title=f"[IFOP] {title_e.get_text().strip()}"[:500],
                            content=item.get_text().strip()[:2000],
                            url=title_e.get("href", "")
                            if title_e.name == "a"
                            else "https://www.ifop.com",
                            source_name=self.name,
                        )
                        if a.is_valid():
                            articles.append(a)
            elif "monaviscitoyen" in src_low:
                base_url = "https://www.monaviscitoyen.fr"
                seen = set()

                def add_item(title_text: str, content_text: str, link: str):
                    if not link:
                        return
                    if link.startswith("/"):
                        link = f"{base_url}{link}"
                    if link in seen:
                        return
                    seen.add(link)
                    a = Article(
                        title=f"[MONAVIS] {title_text}"[:500],
                        content=content_text[:2000],
                        url=link,
                        source_name=self.name,
                    )
                    if a.is_valid():
                        articles.append(a)

                def parse_from_soup(soup):
                    for item in soup.find_all(["article", "div", "li"]):
                        title_e = item.find(["h1", "h2", "h3"])
                        link_e = item.find("a", href=True)
                        if title_e and link_e:
                            content_text = item.get_text(" ", strip=True)
                            add_item(
                                title_e.get_text().strip(), content_text, link_e.get("href", "")
                            )
                        if len(articles) >= 30:
                            break
                    if len(articles) < 10:
                        for link_e in soup.find_all("a", href=True):
                            text = link_e.get_text(" ", strip=True)
                            if len(text) < 20:
                                continue
                            href = link_e.get("href", "")
                            if "monaviscitoyen" not in href and not href.startswith("/"):
                                continue
                            add_item(text, text, href)
                            if len(articles) >= 30:
                                break

                # Try Botasaurus first (if installed)
                try:
                    from botasaurus.request import Request, request
                    from botasaurus.soupify import soupify

                    @request
                    def _botasaurus_request(req: Request, _data):
                        resp = req.get(self.url)
                        return {
                            "status": getattr(resp, "status_code", None),
                            "text": getattr(resp, "text", ""),
                        }

                    payload = _botasaurus_request()
                    if isinstance(payload, list):
                        payload = payload[0] if payload else {}
                    if payload and payload.get("status") == 200:
                        soup = soupify(payload.get("text", ""))
                        parse_from_soup(soup)
                except Exception as e:
                    logger.warning("Botasaurus request failed for {}: {}", self.name, str(e)[:40])

                # Try Botasaurus browser (JS/anti-bot)
                if not articles:
                    try:
                        import time as _time

                        from botasaurus.browser import Driver, browser

                        @browser
                        def _botasaurus_browser(driver: Driver, _data):
                            driver.get(self.url)
                            _time.sleep(2)
                            return driver.page_source

                        html = _botasaurus_browser()
                        if isinstance(html, list):
                            html = html[0] if html else ""
                        if html:
                            soup = BeautifulSoup(html, "html.parser")
                            parse_from_soup(soup)
                    except Exception as e:
                        logger.warning(
                            "Botasaurus browser failed for {}: {}", self.name, str(e)[:40]
                        )

                # Fallback: classic requests
                if not articles:
                    resp = requests.get(self.url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code != 200:
                        logger.warning(
                            "Scraping blocked for {}: HTTP {}", self.name, resp.status_code
                        )
                        return articles
                    if not resp.text or len(resp.text) < 10:
                        return articles
                    soup = BeautifulSoup(resp.text, "html.parser")
                    parse_from_soup(soup)
            else:
                resp = requests.get(self.url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                if not resp.text or len(resp.text) < 10:
                    return articles
                soup = BeautifulSoup(resp.text, "html.parser")
                for item in soup.find_all(
                    ["article", "div"], class_=re.compile(r".*post|entry|news.*", re.I)
                )[:30]:
                    title_e = item.find(["h1", "h2", "h3", "a"])
                    content_e = item.find(
                        ["p", "div"], class_=re.compile(r".*content|summary.*", re.I)
                    )
                    if title_e and content_e:
                        a = Article(
                            title=title_e.get_text().strip()[:500],
                            content=content_e.get_text().strip()[:2000],
                            url=title_e.get("href", "") if title_e.name == "a" else "",
                            source_name=self.name,
                        )
                        if a.is_valid():
                            articles.append(a)
        except Exception as e:
            logger.error("Scraping extraction error for {}: {}", self.name, str(e)[:40])
        return articles[:50]


class GDELTExtractor(BaseExtractor):
    def extract(self) -> list[Article]:
        articles, seen = [], set()
        try:
            for keyword in ["France", "economie", "technologie", "politique"]:
                try:
                    soup = BeautifulSoup(
                        requests.get(
                            f"https://news.google.com/search?q={keyword}+France&hl=fr&gl=FR&ceid=FR:fr",
                            headers={"User-Agent": "Mozilla/5.0"},
                            timeout=8,
                        ).text,
                        "html.parser",
                    )
                    for item in soup.find_all("article")[:10]:
                        title_e = item.find("h3")
                        link_e = item.find("a", href=True)
                        if title_e and link_e and link_e.get("href") not in seen:
                            seen.add(link_e.get("href"))
                            a = Article(
                                title=title_e.get_text().strip()[:500],
                                content=title_e.get_text().strip()[:2000],
                                url=link_e.get("href", ""),
                                source_name=self.name,
                            )
                            if a.is_valid():
                                articles.append(a)
                except:
                    pass
        except Exception as e:
            logger.error("GDELT extraction error for {}: {}", self.name, str(e)[:40])
        return articles[:50]


class GDELTFileExtractor(BaseExtractor):
    def extract(self) -> list[Article]:
        articles = []
        try:
            resp = requests.get("http://data.gdeltproject.org/gdeltv2/lastupdate.txt", timeout=10)
            for line in resp.text.strip().split("\n")[:3]:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        csv_resp = requests.get(parts[2], timeout=10)
                        for row_num, row in enumerate(
                            csv.reader(StringIO(csv_resp.text), delimiter="\t")
                        ):
                            if row_num > 50:
                                break
                            if len(row) >= 2:
                                a = Article(
                                    title=row[1][:500] if len(row) > 1 else "GDELT",
                                    content=f"Code: {row[0]}, Date: {row[2] if len(row) > 2 else 'N/A'}"[
                                        :2000
                                    ],
                                    url=row[57] if len(row) > 57 else "",
                                    source_name=self.name,
                                )
                                if a.is_valid():
                                    articles.append(a)
                    except:
                        pass
        except Exception as e:
            logger.error("GDELT file extraction error for {}: {}", self.name, str(e)[:40])
        return articles[:100]


class MongoExtractor(BaseExtractor):
    """Extract articles from MongoDB (ZZDB synthetic data) - WITH SAFEGUARDS"""

    def extract(self) -> list[Article]:
        articles = []
        try:
            import os
            from datetime import timedelta

            from pymongo import MongoClient

            # GARDE-FOU 1: Vérifier variable d'environnement pour désactiver ZZDB
            if os.getenv("DISABLE_ZZDB", "false").lower() == "true":
                return articles

            # GARDE-FOU 2: Limite max d'articles synthétiques par exécution
            max_synth = int(os.getenv("ZZDB_MAX_ARTICLES", "50"))

            mongo_uri = os.getenv(
                "ZZDB_MONGO_URI", os.getenv("MONGO_URI", "mongodb://localhost:27017")
            )
            db_name = os.getenv("ZZDB_MONGO_DB", "zzdb")
            collection_name = os.getenv("ZZDB_MONGO_COLLECTION", "synthetic_articles")

            client = MongoClient(mongo_uri)
            coll = client[db_name][collection_name]

            # GARDE-FOU 3: Filtrer les documents trop récents (si published_at existe)
            cutoff = datetime.now() - timedelta(hours=1)
            sample = coll.find_one({}, {"published_at": 1})
            if sample and "published_at" in sample:
                query = {"published_at": {"$lt": cutoff}}
                sort_field = "published_at"
            else:
                query = {}
                sort_field = "_id"

            cursor = (
                coll.find(
                    query,
                    {
                        "title": 1,
                        "content": 1,
                        "url": 1,
                        "sentiment": 1,
                        "theme": 1,
                        "published_at": 1,
                    },
                )
                .sort(sort_field, -1)
                .limit(max_synth)
            )

            for doc in cursor:
                title = (doc.get("title") or "").strip()
                content = (doc.get("content") or "").strip()
                url = doc.get("url")
                published_at = doc.get("published_at")

                # GARDE-FOU 4: Validation stricte du contenu
                if not title or not content:
                    continue

                # GARDE-FOU 5: Vérifier longueur minimale et maximale
                if len(title) < 10 or len(title) > 500:
                    continue
                if len(content) < 50 or len(content) > 5000:
                    continue

                # GARDE-FOU 6: Vérifier que le contenu n'est pas trop répétitif
                words = content.split()
                if words and len(set(words)) < len(words) * 0.3:
                    continue

                a = Article(
                    title=title[:500],
                    content=content[:2000],
                    url=url or self.url,
                    source_name=self.name,
                    published_at=str(published_at) if published_at else datetime.now().isoformat(),
                )

                # GARDE-FOU 7: Validation finale avec is_valid()
                if a.is_valid():
                    articles.append(a)
                    if len(articles) >= max_synth:
                        break

            client.close()
        except Exception as e:
            logger.warning("Mongo extraction error for {}: {}", self.name, str(e)[:40])
        return articles


class CSVExtractor(BaseExtractor):
    """Extract articles from CSV file (ZZDB export) - INTÉGRATION UNIQUE (comme Kaggle/GDELT)"""

    def extract(self) -> list[Article]:
        articles = []
        try:
            import os
            import sqlite3
            from pathlib import Path

            # GARDE-FOU 1: Vérifier variable d'environnement pour désactiver ZZDB CSV
            if os.getenv("DISABLE_ZZDB_CSV", "false").lower() == "true":
                return articles

            # CSV path - try multiple locations (comme Kaggle/GDELT dans data/raw/)
            possible_paths = [
                # Emplacement standard dans data/raw/ (comme Kaggle/GDELT)
                Path(__file__).parent.parent.parent
                / "data"
                / "raw"
                / "zzdb_csv"
                / "zzdb_dataset.csv",
                Path.cwd() / "data" / "raw" / "zzdb_csv" / "zzdb_dataset.csv",
                Path.home() / "datasens_project" / "data" / "raw" / "zzdb_csv" / "zzdb_dataset.csv",
                # Emplacements alternatifs (zzdb/export/)
                Path(__file__).parent.parent.parent / "zzdb" / "export" / "zzdb_dataset.csv",
                Path(__file__).parent.parent.parent / "zzdb" / "zzdb_dataset.csv",
                Path.cwd() / "zzdb" / "export" / "zzdb_dataset.csv",
                Path.cwd() / "zzdb" / "zzdb_dataset.csv",
                # URL configurée
                Path(self.url) if Path(self.url).is_absolute() else Path.cwd() / self.url,
            ]

            csv_path = None
            for p in possible_paths:
                if p.exists():
                    csv_path = p
                    break

            if not csv_path or not csv_path.exists():
                return articles

            # GARDE-FOU 0: Vérifier si la source est déjà intégrée COMPLÈTEMENT (comme Kaggle/GDELT)
            # Si le CSV a été intégré en totalité, on ne re-collecte plus (source statique)
            # Sinon, on continue pour compléter l'import (déduplication automatique via fingerprint)
            # IMPORTANT: La déduplication via fingerprint (SHA256(title|content)) empêche les doublons
            # même si les articles existent déjà dans la DB (toutes sources confondues)
            #
            # OPTION: FORCE_ZZDB_REIMPORT=true permet de forcer la réimportation même si déjà intégré
            # (utile pour améliorer le dataset et réinjecter les versions améliorées)
            force_reimport = os.getenv("FORCE_ZZDB_REIMPORT", "false").lower() == "true"

            db_path = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
            if Path(db_path).exists() and not force_reimport:
                try:
                    # Compter les lignes valides dans le CSV
                    csv_valid_count = 0
                    with open(csv_path, encoding="utf-8", errors="ignore") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            title = row.get("title", "").strip()
                            content = row.get("content", "").strip()
                            if not title or not content:
                                continue
                            title_clean = title[:500].strip()
                            content_clean = content[:2000].strip()
                            if len(title_clean) < 10 or len(title_clean) > 500:
                                continue
                            if len(content_clean) < 50 or len(content_clean) > 5000:
                                continue
                            words = content_clean.split()
                            if len(set(words)) < len(words) * 0.3:
                                continue
                            csv_valid_count += 1

                    # Compter les articles existants dans la DB pour cette source uniquement
                    conn_check = sqlite3.connect(db_path)
                    cursor_check = conn_check.cursor()
                    cursor_check.execute(
                        """
                        SELECT COUNT(*)
                        FROM raw_data r
                        JOIN source s ON r.source_id = s.source_id
                        WHERE s.name = ?
                    """,
                        (self.name,),
                    )
                    existing_count = cursor_check.fetchone()[0]
                    conn_check.close()

                    # Si le nombre d'articles dans la DB >= nombre d'articles valides dans le CSV
                    # → Import complet, on ne re-collecte plus (fondation statique)
                    # SAUF si FORCE_ZZDB_REIMPORT=true (permet amélioration continue du dataset)
                    # NOTE: La déduplication via fingerprint dans load_article_with_id() empêche
                    # les doublons même si on re-collecte (même article = même fingerprint = rejeté)
                    if existing_count >= csv_valid_count:
                        return articles
                except:
                    pass  # Si erreur, on continue quand même

            # Lire le CSV - IMPORT COMPLET (comme Kaggle/GDELT, pas de limite artificielle)
            with open(csv_path, encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Extraire les colonnes du CSV
                    title = row.get("title", "").strip()
                    content = row.get("content", "").strip()
                    url = row.get("url", self.url or "https://zzdb.datasens.fr")
                    published_at = row.get("published_at", "") or datetime.now().isoformat()

                    # GARDE-FOU 3: Validation stricte du contenu
                    if not title or not content:
                        continue

                    # GARDE-FOU 4: Vérifier longueur minimale et maximale
                    title_clean = title[:500].strip()
                    content_clean = content[:2000].strip()

                    if len(title_clean) < 10 or len(title_clean) > 500:
                        continue
                    if len(content_clean) < 50 or len(content_clean) > 5000:
                        continue

                    # GARDE-FOU 5: Vérifier que le contenu n'est pas trop répétitif
                    words = content_clean.split()
                    if len(set(words)) < len(words) * 0.3:
                        continue

                    a = Article(
                        title=title_clean,
                        content=content_clean,
                        url=url,
                        source_name=self.name,
                        published_at=published_at,
                    )

                    # GARDE-FOU 6: Validation finale avec is_valid()
                    # Déduplication via fingerprint dans load_article_with_id()
                    if a.is_valid():
                        articles.append(a)
        except Exception as e:
            logger.warning("{}: {}", self.name, str(e)[:40])
        return articles


class KaggleExtractor(BaseExtractor):
    """Extract articles from Kaggle datasets (CSV/JSON) - Support dossier unique sans partitionnement"""

    def extract(self) -> list[Article]:
        from pathlib import Path

        articles = []
        try:
            # Chercher dans DEUX emplacements (PROJECT et HOME)
            base_dirs = [
                Path.home()
                / "Desktop"
                / "DEV IA 2025"
                / "PROJET_DATASENS"
                / "data"
                / "raw"
                / self.name,
                Path.home() / "datasens_project" / "data" / "raw" / self.name,
                Path(__file__).parent.parent.parent / "data" / "raw" / self.name,
                Path.cwd() / "data" / "raw" / self.name,
            ]

            for base in base_dirs:
                if not base.exists():
                    continue

                # Chercher TOUS les CSV récursivement (peu importe le sous-dossier date ou directement dans le dossier)
                for csv_file in base.rglob("*.csv"):
                    try:
                        # Ignorer les fichiers vides ou trop petits
                        if csv_file.stat().st_size < 100:
                            continue

                        with open(csv_file, encoding="utf-8", errors="ignore") as f:
                            reader = csv.reader(f)
                            header = next(reader, None)  # Skip header

                            for row in reader:
                                if not row or len(row) < 2:
                                    continue

                                # Essayer de détecter les colonnes title/content
                                title = ""
                                content = ""

                                # Si header existe, essayer de trouver title/content
                                if header:
                                    try:
                                        header_lower = [h.lower() if h else "" for h in header]
                                        title_idx = next(
                                            (
                                                i
                                                for i, h in enumerate(header_lower)
                                                if "title" in h or "headline" in h
                                            ),
                                            0,
                                        )
                                        content_idx = next(
                                            (
                                                i
                                                for i, h in enumerate(header_lower)
                                                if "content" in h or "text" in h or "body" in h
                                            ),
                                            1,
                                        )
                                        title = str(
                                            row[title_idx]
                                            if title_idx < len(row)
                                            else row[0]
                                            if row
                                            else ""
                                        )[:500].strip()
                                        content = str(
                                            row[content_idx]
                                            if content_idx < len(row)
                                            else " ".join(row[1:])
                                            if len(row) > 1
                                            else ""
                                        )[:2000].strip()
                                    except:
                                        title = str(row[0])[:500].strip() if row else ""
                                        content = (
                                            " ".join(str(v) for v in row[1:] if v)[:2000].strip()
                                            if len(row) > 1
                                            else title
                                        )
                                else:
                                    # Pas de header, utiliser les colonnes par position
                                    title = str(row[0])[:500].strip() if row else ""
                                    content = (
                                        " ".join(str(v) for v in row[1:] if v)[:2000].strip()
                                        if len(row) > 1
                                        else title
                                    )

                                if len(title) > 3 and len(content) > 10:
                                    a = Article(
                                        title=title,
                                        content=content,
                                        url=self.url,
                                        source_name=self.name,
                                    )
                                    if a.is_valid():
                                        articles.append(a)
                    except Exception:
                        pass

                # Chercher TOUS les JSON récursivement aussi
                for json_file in base.rglob("*.json"):
                    if "manifest" in json_file.name.lower():
                        continue
                    try:
                        if json_file.stat().st_size < 100:
                            continue

                        import json as json_lib

                        with open(json_file, encoding="utf-8", errors="ignore") as f:
                            data = json_lib.load(f)
                            items = (
                                data
                                if isinstance(data, list)
                                else (data.get("items", []) if isinstance(data, dict) else [])
                            )

                            for item in items:
                                if isinstance(item, dict):
                                    title = str(
                                        item.get(
                                            "title",
                                            item.get("headline", item.get("Title", "Kaggle")),
                                        )
                                    )[:500].strip()
                                    content = str(
                                        item.get(
                                            "content",
                                            item.get(
                                                "text",
                                                item.get(
                                                    "description",
                                                    item.get("Content", item.get("Text", title)),
                                                ),
                                            ),
                                        )
                                    )[:2000].strip()
                                    if len(title) > 3 and len(content) > 10:
                                        a = Article(
                                            title=title,
                                            content=content,
                                            url=self.url,
                                            source_name=self.name,
                                        )
                                        if a.is_valid():
                                            articles.append(a)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning("{}: {}", self.name, str(e)[:40])
        return articles  # Retourner TOUS les articles (pas de limite artificielle)


def create_extractor(source: Source) -> BaseExtractor:
    """Factory - route source to correct extractor"""
    acq_type, src_low = source.acquisition_type.lower(), source.source_name.lower()
    if acq_type == "rss":
        return RSSExtractor(source.source_name, source.url)
    elif acq_type == "bigdata":
        return GDELTFileExtractor(source.source_name, source.url)
    elif acq_type == "mongodb" or ("zzdb" in src_low and "csv" not in src_low):
        return MongoExtractor(source.source_name, source.url)
    elif acq_type == "csv" or ("zzdb" in src_low and "csv" in src_low):
        return CSVExtractor(source.source_name, source.url)
    elif acq_type == "dataset":
        if "kaggle" in src_low:
            return KaggleExtractor(source.source_name, source.url)
        return KaggleExtractor(source.source_name, source.url)
    elif acq_type in ["api", "api_scraping"]:
        if any(k in src_low for k in ["reddit", "weather", "meteo"]):
            return APIExtractor(source.source_name, source.url)
        elif any(k in src_low for k in ["insee", "citoyen", "opinion"]):
            return ScrapingExtractor(source.source_name, source.url)
        return APIExtractor(source.source_name, source.url)
    elif acq_type == "scraping":
        return ScrapingExtractor(source.source_name, source.url)
    return RSSExtractor(source.source_name, source.url)


def sanitize_text(text: str | None) -> str:
    """Remove null bytes, control chars, BOM, and problematic special chars.
    Normalizes Unicode (NFC) to avoid duplicate char representations."""
    if text is None or not isinstance(text, str):
        return ""
    text = str(text)
    text = text.replace("\ufeff", "")  # BOM
    text = text.replace("\x00", "")  # null bytes
    text = "".join(c for c in text if ord(c) >= 32 or c in " \t\n\r")  # control chars
    text = text.replace("\ufffd", "")  # Unicode replacement
    text = unicodedata.normalize("NFC", text)
    return text.strip()


def sanitize_url(url: str | None) -> str:
    """Sanitize URL for safe storage/export (same rules as text)."""
    if not url:
        return ""
    return sanitize_text(str(url))


class ContentTransformer:
    @staticmethod
    def clean_html(text: str) -> str:
        if not text or len(text.strip()) < 5:
            return text or ""
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(separator=" ").strip()

    @staticmethod
    def normalize(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def transform(article: Article) -> Article:
        article.title = sanitize_text(article.title)
        article.content = sanitize_text(article.content)
        article.content = ContentTransformer.clean_html(article.content)
        article.content = ContentTransformer.normalize(article.content)
        if article.url:
            article.url = sanitize_url(article.url)
        return article


class DatabaseLoader:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def get_source_id(self, name: str) -> int | None:
        self.cursor.execute("SELECT source_id FROM source WHERE name = ?", (name,))
        r = self.cursor.fetchone()
        return r[0] if r else None

    def load_article(self, article: Article, source_id: int) -> bool:
        try:
            fp = article.fingerprint()
            self.cursor.execute("SELECT raw_data_id FROM raw_data WHERE fingerprint = ?", (fp,))
            if self.cursor.fetchone():
                return False
            self.cursor.execute(
                """INSERT INTO raw_data (source_id, title, content, url, fingerprint, published_at, collected_at, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    source_id,
                    article.title,
                    article.content,
                    article.url,
                    fp,
                    article.published_at,
                    datetime.now().isoformat(),
                    0.5,
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error("DB error: {}", str(e)[:40])
            return False

    def get_stats(self) -> dict:
        stats = {}
        self.cursor.execute(
            "SELECT name, COUNT(*) FROM raw_data JOIN source ON raw_data.source_id = source.source_id GROUP BY name"
        )
        for name, count in self.cursor.fetchall():
            stats[name] = count
        return stats

    def log_sync(self, source_id: int, rows: int, status: str = "OK", error: str | None = None):
        try:
            self.cursor.execute(
                "INSERT INTO sync_log (source_id, sync_date, rows_synced, status, error_message) VALUES (?, ?, ?, ?, ?)",
                (source_id, datetime.now().isoformat(), rows, status, error),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.warning("Sync log error: {}", str(e)[:40])
            return False
