"""DataSens E1 - CORE ENGINE (SENIOR MODE - DRY/SOLID - 220 LIGNES)"""
import hashlib, re, sqlite3, csv, warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
import feedparser, requests
from bs4 import BeautifulSoup

# Suppress BeautifulSoup warnings
warnings.filterwarnings('ignore', category=UserWarning, module='bs4')
warnings.filterwarnings('ignore', message='.*looks more like a filename.*', category=UserWarning)

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
                print(f"   ⚠️  {self.name}: RSS parse error - {str(feed.bozo_exception)[:40]}")
            for entry in feed.entries[:50]:
                title = entry.get('title', '').strip()
                content = entry.get('summary', '') or entry.get('description', '')
                url = entry.get('link', '')
                if title and (content or title):
                    a = Article(title=title[:500], content=content[:2000] if content else title[:2000], 
                               url=url, source_name=self.name, published_at=entry.get('published', ''))
                    if a.is_valid(): articles.append(a)
        except Exception as e:
            print(f"   ❌ {self.name}: {str(e)[:40]}")
        return articles

class APIExtractor(BaseExtractor):
    def extract(self) -> list[Article]:
        articles, src_low = [], self.name.lower()
        try:
            if 'reddit' in src_low:
                for sr in ['france', 'actualites']:
                    try:
                        # Try JSON API first
                        resp = requests.get(f'https://www.reddit.com/r/{sr}/top.json?t=week&limit=25', 
                                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=10)
                        if resp.status_code == 200:
                            data = resp.json().get('data', {}).get('children', [])
                            for post in data[:15]:
                                pd = post.get('data', {})
                                if pd.get('title') and pd.get('score', 0) > 5:
                                    a = Article(title=f"[{sr.upper()}] {pd['title']}"[:500], 
                                               content=pd.get('selftext', '')[:2000] or f"Discussion #{pd['score']}", 
                                               url=f"https://www.reddit.com{pd.get('permalink', '')}", source_name=self.name)
                                    if a.is_valid() and a.url: articles.append(a)
                        else:
                            # Fallback: HTML scraping
                            html_resp = requests.get(f'https://www.reddit.com/r/{sr}/top/?t=week', 
                                                     headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=10)
                            if html_resp.status_code == 200:
                                soup = BeautifulSoup(html_resp.text, 'html.parser')
                                for item in soup.find_all(['a'], {'data-testid': 'post-title'})[:15]:
                                    title = item.get_text().strip()
                                    href = item.get('href', '')
                                    if title and href:
                                        a = Article(title=f"[{sr.upper()}] {title}"[:500], 
                                                   content=f"Reddit post from r/{sr}"[:2000], 
                                                   url=f"https://www.reddit.com{href}" if href.startswith('/') else href, source_name=self.name)
                                        if a.is_valid(): articles.append(a)
                    except Exception as e:
                        print(f"   ⚠️  Reddit {sr}: {str(e)[:40]}")
            elif 'insee' in src_low or 'citoyen' in src_low:
                soup = BeautifulSoup(requests.get('https://www.monaviscitoyen.fr/', 
                                                 headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).text, 'html.parser')
                for item in soup.find_all(['article', 'div'], class_=re.compile(r'.*avis|opinion.*', re.I))[:30]:
                    text = item.get_text(separator=' ').strip()
                    if len(text) > 20:
                        a = Article(title=text[:100], content=text[:2000], url='https://www.monaviscitoyen.fr/', source_name=self.name)
                        if a.is_valid(): articles.append(a)
            elif 'weather' in src_low or 'meteo' in src_low:
                for city in ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice']:
                    try:
                        g_r = requests.get(f'https://geocoding-api.open-meteo.com/v1/search?name={city}&country=France&language=fr&limit=1', timeout=8).json()
                        if g_r.get('results'):
                            g = g_r['results'][0]
                            w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={g['latitude']}&longitude={g['longitude']}&current=temperature_2m,weather_code&timezone=auto", timeout=8).json()
                            c = w.get('current', {})
                            a = Article(title=f"Météo {city}: {c.get('temperature_2m', 'N/A')}C", 
                                       content=f"Condition: {c.get('weather_code', 'N/A')}, {g.get('name', city)}", 
                                       url=f"https://www.weather.com/weather/today/l/{g['latitude']},{g['longitude']}", source_name=self.name)
                            if a.is_valid(): articles.append(a)
                    except: pass
            else:
                resp = requests.get(self.url, timeout=5)
                if resp.status_code == 200 and 'json' in resp.headers.get('content-type', ''):
                    for item in (resp.json().get('articles') or resp.json().get('items') or resp.json().get('results') or [])[:50]:
                        a = Article(title=item.get('title', '')[:500], content=item.get('content', '')[:2000], 
                                   url=item.get('url', ''), source_name=self.name)
                        if a.is_valid(): articles.append(a)
        except Exception as e:
            print(f"   ❌ {self.name}: {str(e)[:40]}")
        return articles[:50]

class ScrapingExtractor(BaseExtractor):
    def extract(self) -> list[Article]:
        articles, src_low = [], self.name.lower()
        try:
            if 'trustpilot' in src_low:
                soup = BeautifulSoup(requests.get('https://www.trustpilot.com', headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).text, 'html.parser')
                for review in soup.find_all(['article', 'div'], class_=re.compile(r'.*review|rating.*', re.I))[:30]:
                    title = review.find(['h2', 'h3', 'h1'])
                    if title:
                        a = Article(title=f"[TRUSTPILOT] {title.get_text().strip()}"[:500], content=review.get_text().strip()[:2000], 
                                   url='https://www.trustpilot.com', source_name=self.name)
                        if a.is_valid(): articles.append(a)
            elif 'ifop' in src_low:
                soup = BeautifulSoup(requests.get('https://www.ifop.com/?rubrique=fiches-signalitiques', 
                                                 headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).text, 'html.parser')
                for item in soup.find_all(['div', 'article', 'li'], class_=re.compile(r'.*sondage|barometre.*', re.I))[:30]:
                    title_e = item.find(['h2', 'h3', 'h4', 'a'])
                    if title_e and title_e.get_text().strip():
                        a = Article(title=f"[IFOP] {title_e.get_text().strip()}"[:500], content=item.get_text().strip()[:2000], 
                                   url=title_e.get('href', '') if title_e.name == 'a' else 'https://www.ifop.com', source_name=self.name)
                        if a.is_valid(): articles.append(a)
            else:
                resp = requests.get(self.url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                if not resp.text or len(resp.text) < 10:
                    return articles
                soup = BeautifulSoup(resp.text, 'html.parser')
                for item in soup.find_all(['article', 'div'], class_=re.compile(r'.*post|entry|news.*', re.I))[:30]:
                    title_e = item.find(['h1', 'h2', 'h3', 'a'])
                    content_e = item.find(['p', 'div'], class_=re.compile(r'.*content|summary.*', re.I))
                    if title_e and content_e:
                        a = Article(title=title_e.get_text().strip()[:500], content=content_e.get_text().strip()[:2000], 
                                   url=title_e.get('href', '') if title_e.name == 'a' else '', source_name=self.name)
                        if a.is_valid(): articles.append(a)
        except Exception as e:
            print(f"   ❌ {self.name}: {str(e)[:40]}")
        return articles[:50]

class GDELTExtractor(BaseExtractor):
    def extract(self) -> list[Article]:
        articles, seen = [], set()
        try:
            for keyword in ['France', 'economie', 'technologie', 'politique']:
                try:
                    soup = BeautifulSoup(requests.get(f'https://news.google.com/search?q={keyword}+France&hl=fr&gl=FR&ceid=FR:fr', 
                                                      headers={'User-Agent': 'Mozilla/5.0'}, timeout=8).text, 'html.parser')
                    for item in soup.find_all('article')[:10]:
                        title_e = item.find('h3')
                        link_e = item.find('a', href=True)
                        if title_e and link_e and link_e.get('href') not in seen:
                            seen.add(link_e.get('href'))
                            a = Article(title=title_e.get_text().strip()[:500], content=title_e.get_text().strip()[:2000], 
                                       url=link_e.get('href', ''), source_name=self.name)
                            if a.is_valid(): articles.append(a)
                except: pass
        except Exception as e:
            print(f"   ❌ {self.name}: {str(e)[:40]}")
        return articles[:50]

class GDELTFileExtractor(BaseExtractor):
    def extract(self) -> list[Article]:
        articles = []
        try:
            resp = requests.get('http://data.gdeltproject.org/gdeltv2/lastupdate.txt', timeout=10)
            for line in resp.text.strip().split('\n')[:3]:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        csv_resp = requests.get(parts[2], timeout=10)
                        for row_num, row in enumerate(csv.reader(StringIO(csv_resp.text), delimiter='\t')):
                            if row_num > 50: break
                            if len(row) >= 2:
                                a = Article(title=row[1][:500] if len(row) > 1 else 'GDELT', 
                                           content=f"Code: {row[0]}, Date: {row[2] if len(row) > 2 else 'N/A'}"[:2000], 
                                           url=row[57] if len(row) > 57 else '', source_name=self.name)
                                if a.is_valid(): articles.append(a)
                    except: pass
        except Exception as e:
            print(f"   ❌ {self.name}: {str(e)[:40]}")
        return articles[:100]

class KaggleExtractor(BaseExtractor):
    """Extract articles from Kaggle datasets (CSV/JSON)"""
    def extract(self) -> list[Article]:
        from pathlib import Path
        articles = []
        try:
            # Chercher dans DEUX emplacements (PROJECT et HOME)
            base_dirs = [
                Path.home() / 'Desktop' / 'DEV IA 2025' / 'PROJET_DATASENS' / 'data' / 'raw' / self.name,
                Path.home() / 'datasens_project' / 'data' / 'raw' / self.name,
            ]
            
            for base in base_dirs:
                if not base.exists():
                    continue
                
                # Chercher TOUS les CSV récursivement (peu importe le sous-dossier date)
                for csv_file in base.rglob('*.csv'):
                    try:
                        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                            for row_num, row in enumerate(csv.reader(f)):
                                if row_num > 100 or row_num == 0: continue
                                if len(row) >= 2:
                                    title = row[0][:500] if row[0] else 'Kaggle'
                                    content = ' '.join(row[1:])[:2000] if len(row) > 1 else title
                                    if len(title) > 3 and len(content) > 10:
                                        a = Article(title=title, content=content, url=self.url, source_name=self.name)
                                        articles.append(a)
                    except Exception as e:
                        pass
                
                # Chercher TOUS les JSON récursivement aussi
                for json_file in base.rglob('*.json'):
                    try:
                        import json as json_lib
                        with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                            data = json_lib.load(f)
                            if isinstance(data, list):
                                for item in data[:50]:
                                    if isinstance(item, dict):
                                        title = str(item.get('title', item.get('headline', 'Kaggle')))[:500]
                                        content = str(item.get('content', item.get('text', item.get('description', title))))[:2000]
                                        if len(title) > 3 and len(content) > 10:
                                            a = Article(title=title, content=content, url=self.url, source_name=self.name)
                                            articles.append(a)
                    except Exception as e:
                        pass
        except Exception as e:
            print(f"   ❌ {self.name}: {str(e)[:40]}")
        return articles[:50]

def create_extractor(source: Source) -> BaseExtractor:
    """Factory - route source to correct extractor"""
    acq_type, src_low = source.acquisition_type.lower(), source.source_name.lower()
    if acq_type == "rss": return RSSExtractor(source.source_name, source.url)
    elif acq_type == "bigdata": return GDELTFileExtractor(source.source_name, source.url)
    elif acq_type == "dataset":
        if 'kaggle' in src_low: return KaggleExtractor(source.source_name, source.url)
        return KaggleExtractor(source.source_name, source.url)
    elif acq_type in ["api", "api_scraping"]:
        if any(k in src_low for k in ['reddit', 'weather', 'meteo']): return APIExtractor(source.source_name, source.url)
        elif any(k in src_low for k in ['insee', 'citoyen', 'opinion']): return ScrapingExtractor(source.source_name, source.url)
        return APIExtractor(source.source_name, source.url)
    elif acq_type == "scraping": return ScrapingExtractor(source.source_name, source.url)
    return RSSExtractor(source.source_name, source.url)

class ContentTransformer:
    @staticmethod
    def clean_html(text: str) -> str:
        if not text or len(text.strip()) < 5:
            return text or ''
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text(separator=' ').strip()
    @staticmethod
    def normalize(text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    @staticmethod
    def transform(article: Article) -> Article:
        article.content = ContentTransformer.clean_html(article.content)
        article.content = ContentTransformer.normalize(article.content)
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
            if self.cursor.fetchone(): return False
            self.cursor.execute("""INSERT INTO raw_data (source_id, title, content, url, fingerprint, published_at, collected_at, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                (source_id, article.title, article.content, article.url, fp, article.published_at, datetime.now().isoformat(), 0.5))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"   ⚠️  DB error: {str(e)[:40]}")
            return False
    
    def get_stats(self) -> dict:
        stats = {}
        self.cursor.execute("SELECT name, COUNT(*) FROM raw_data JOIN source ON raw_data.source_id = source.source_id GROUP BY name")
        for name, count in self.cursor.fetchall():
            stats[name] = count
        return stats
    
    def log_sync(self, source_id: int, rows: int, status: str = 'OK', error: str = None):
        try:
            self.cursor.execute("INSERT INTO sync_log (source_id, sync_date, rows_synced, status, error_message) VALUES (?, ?, ?, ?, ?)",
                (source_id, datetime.now().isoformat(), rows, status, error))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"   ⚠️  Sync log error: {str(e)[:40]}")
            return False
