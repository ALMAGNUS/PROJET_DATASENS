"""DataSens Dashboard - Visualisation enrichissement dataset"""
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class DataSensDashboard:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.stats = {}
    
    def collect_stats(self):
        """Collecte toutes les statistiques d'enrichissement"""
        c = self.conn.cursor()
        
        # 1. Total par source
        c.execute("""
            SELECT s.name, COUNT(r.raw_data_id) as total, 
                   COUNT(DISTINCT r.fingerprint) as unique_count,
                   MAX(r.collected_at) as last_collect
            FROM source s 
            LEFT JOIN raw_data r ON s.source_id = r.source_id 
            GROUP BY s.name 
            ORDER BY total DESC
        """)
        self.stats['by_source'] = [{'source': r[0], 'total': r[1], 'unique': r[2], 'last': r[3]} for r in c.fetchall()]
        
        # 2. Enrichissement Topics
        c.execute("""
            SELECT COUNT(DISTINCT dt.raw_data_id) as tagged_count,
                   COUNT(DISTINCT dt.topic_id) as topics_used,
                   AVG(dt.confidence_score) as avg_confidence
            FROM document_topic dt
        """)
        r = c.fetchone()
        self.stats['topics'] = {'tagged': r[0] or 0, 'topics_used': r[1] or 0, 'avg_confidence': round(r[2] or 0, 2)}
        
        # 3. Enrichissement Sentiment
        c.execute("""
            SELECT label, COUNT(*) as count, AVG(score) as avg_score
            FROM model_output 
            WHERE model_name = 'sentiment_keyword'
            GROUP BY label
        """)
        self.stats['sentiment'] = {r[0]: {'count': r[1], 'avg_score': round(r[2], 2)} for r in c.fetchall()}
        
        # 4. Articles enrichis (avec topics ET sentiment)
        c.execute("""
            SELECT COUNT(DISTINCT r.raw_data_id) as enriched
            FROM raw_data r
            WHERE EXISTS (SELECT 1 FROM document_topic dt WHERE dt.raw_data_id = r.raw_data_id)
            AND EXISTS (SELECT 1 FROM model_output mo WHERE mo.raw_data_id = r.raw_data_id AND mo.model_name = 'sentiment_keyword')
        """)
        self.stats['enriched'] = c.fetchone()[0] or 0
        
        # 5. Nouveaux articles aujourd'hui
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute("""
            SELECT COUNT(*) FROM raw_data 
            WHERE DATE(collected_at) = ?
        """, (today,))
        self.stats['new_today'] = c.fetchone()[0] or 0
        
        # 6. Nouveaux articles aujourd'hui par source
        c.execute("""
            SELECT s.name, COUNT(r.raw_data_id) as count
            FROM source s
            LEFT JOIN raw_data r ON s.source_id = r.source_id AND DATE(r.collected_at) = ?
            GROUP BY s.name
            HAVING COUNT(r.raw_data_id) > 0
            ORDER BY count DESC
        """, (today,))
        self.stats['new_by_source'] = {r[0]: r[1] for r in c.fetchall()}
        
        # 7. Distribution par topic
        c.execute("""
            SELECT t.name, COUNT(dt.raw_data_id) as count
            FROM topic t
            LEFT JOIN document_topic dt ON t.topic_id = dt.topic_id
            GROUP BY t.name
            ORDER BY count DESC
        """)
        self.stats['topics_dist'] = {r[0]: r[1] for r in c.fetchall()}
        
        # 8. Total général
        c.execute("SELECT COUNT(*) FROM raw_data")
        self.stats['total'] = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(DISTINCT fingerprint) FROM raw_data WHERE fingerprint IS NOT NULL AND fingerprint != ''")
        self.stats['unique'] = c.fetchone()[0] or 0
    
    def print_dashboard(self):
        """Affiche le dashboard formaté"""
        print("\n" + "="*80)
        print("[DASHBOARD] DATASENS - ENRICHISSEMENT DATASET")
        print("="*80)
        
        # Résumé global
        print(f"\n[RESUME] RÉSUMÉ GLOBAL")
        print(f"   Total articles:        {self.stats['total']:,}")
        print(f"   Articles uniques:      {self.stats['unique']:,}")
        print(f"   Nouveaux aujourd'hui:  {self.stats['new_today']:,}")
        print(f"   Articles enrichis:     {self.stats['enriched']:,} ({self.stats['enriched']/max(self.stats['total'],1)*100:.1f}%)")
        
        # Nouveaux articles par source aujourd'hui
        if self.stats['new_by_source']:
            print(f"\n[NOUVEAUX] NOUVEAUX ARTICLES AUJOURD'HUI PAR SOURCE")
            for source, count in sorted(self.stats['new_by_source'].items(), key=lambda x: -x[1]):
                print(f"   • {source:30s}: {count:4d} articles")
        
        # Enrichissement Topics
        print(f"\n[TOPICS] ENRICHISSEMENT TOPICS")
        print(f"   Articles taggés:        {self.stats['topics']['tagged']:,}")
        print(f"   Topics utilisés:       {self.stats['topics']['topics_used']}")
        print(f"   Confiance moyenne:     {self.stats['topics']['avg_confidence']:.2f}")
        if self.stats['topics_dist']:
            print(f"   Distribution:")
            for topic, count in sorted(self.stats['topics_dist'].items(), key=lambda x: -x[1])[:5]:
                print(f"      • {topic:20s}: {count:4d} articles")
        
        # Enrichissement Sentiment
        print(f"\n[SENTIMENT] ENRICHISSEMENT SENTIMENT")
        total_sent = sum(s['count'] for s in self.stats['sentiment'].values())
        for label, data in sorted(self.stats['sentiment'].items(), key=lambda x: -x[1]['count']):
            pct = (data['count'] / max(total_sent, 1)) * 100
            print(f"   {label:10s}: {data['count']:4d} articles ({pct:5.1f}%) - Score moyen: {data['avg_score']:.2f}")
        
        # Par source
        print(f"\n[SOURCES] ARTICLES PAR SOURCE")
        print(f"   {'Source':<30s} {'Total':>8s} {'Unique':>8s} {'Dernière collecte':>20s}")
        print(f"   {'-'*30} {'-'*8} {'-'*8} {'-'*20}")
        for s in self.stats['by_source'][:15]:
            last = s['last'][:19] if s['last'] else 'Jamais'
            print(f"   {s['source']:<30s} {s['total']:>8d} {s['unique']:>8d} {last:>20s}")
        
        # Évaluation dataset pour IA
        print(f"\n[IA] ÉVALUATION DATASET POUR IA")
        total = self.stats['total']
        enriched = self.stats['enriched']
        pct_enriched = (enriched / max(total, 1)) * 100
        
        if total < 100:
            status = "[KO] INSUFFISANT"
            msg = "Minimum 100 articles requis"
        elif total < 500:
            status = "[WARN] LIMITÉ"
            msg = "Recommandé: 500+ articles"
        elif total < 1000:
            status = "[OK] BON"
            msg = "Recommandé: 1000+ articles"
        else:
            status = "[OK] EXCELLENT"
            msg = "Dataset prêt pour l'IA"
        
        print(f"   Status: {status} ({total:,} articles)")
        print(f"   Message: {msg}")
        print(f"   Taux d'enrichissement: {pct_enriched:.1f}%")
        
        if pct_enriched < 50:
            print(f"   [WARN] Attention: Seulement {pct_enriched:.1f}% des articles sont enrichis (topics + sentiment)")
            print(f"   [INFO] Solution: Lancer 'python scripts/enrich_all_articles.py' pour enrichir tous les articles")
        
        print("\n" + "="*80 + "\n")
    
    def close(self):
        self.conn.close()

