"""Rapport de collecte détaillé - Session actuelle"""
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class CollectionReport:
    def __init__(self, db_path: str, session_start_time: str = None):
        self.conn = sqlite3.connect(db_path)
        self.session_start = session_start_time or datetime.now().isoformat()
        self.stats = {}
    
    def collect_session_stats(self):
        """Collecte les stats de la session actuelle"""
        c = self.conn.cursor()
        
        # Articles collectés dans cette session (après session_start)
        c.execute("""
            SELECT s.name, COUNT(r.raw_data_id) as count,
                   COUNT(DISTINCT CASE WHEN dt.raw_data_id IS NOT NULL THEN r.raw_data_id END) as tagged,
                   COUNT(DISTINCT CASE WHEN mo.raw_data_id IS NOT NULL THEN r.raw_data_id END) as analyzed
            FROM source s
            LEFT JOIN raw_data r ON s.source_id = r.source_id 
                AND r.collected_at >= ?
            LEFT JOIN document_topic dt ON dt.raw_data_id = r.raw_data_id
            LEFT JOIN model_output mo ON mo.raw_data_id = r.raw_data_id 
                AND mo.model_name = 'sentiment_keyword'
            GROUP BY s.name
            HAVING COUNT(r.raw_data_id) > 0
            ORDER BY count DESC
        """, (self.session_start,))
        
        self.stats['by_source'] = []
        for r in c.fetchall():
            self.stats['by_source'].append({
                'source': r[0],
                'collected': r[1],
                'tagged': r[2] or 0,
                'analyzed': r[3] or 0
            })
        
        # Totaux session
        c.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT CASE WHEN dt.raw_data_id IS NOT NULL THEN r.raw_data_id END) as tagged,
                   COUNT(DISTINCT CASE WHEN mo.raw_data_id IS NOT NULL THEN r.raw_data_id END) as analyzed
            FROM raw_data r
            LEFT JOIN document_topic dt ON dt.raw_data_id = r.raw_data_id
            LEFT JOIN model_output mo ON mo.raw_data_id = r.raw_data_id 
                AND mo.model_name = 'sentiment_keyword'
            WHERE r.collected_at >= ?
        """, (self.session_start,))
        
        r = c.fetchone()
        self.stats['session'] = {
            'total': r[0] or 0,
            'tagged': r[1] or 0,
            'analyzed': r[2] or 0
        }
        
        # Distribution sentiment session
        c.execute("""
            SELECT mo.label, COUNT(*) as count
            FROM model_output mo
            JOIN raw_data r ON mo.raw_data_id = r.raw_data_id
            WHERE mo.model_name = 'sentiment_keyword'
            AND r.collected_at >= ?
            GROUP BY mo.label
        """, (self.session_start,))
        
        self.stats['sentiment'] = {r[0]: r[1] for r in c.fetchall()}
        
        # Distribution topics session
        c.execute("""
            SELECT t.name, COUNT(dt.raw_data_id) as count
            FROM topic t
            JOIN document_topic dt ON t.topic_id = dt.topic_id
            JOIN raw_data r ON dt.raw_data_id = r.raw_data_id
            WHERE r.collected_at >= ?
            GROUP BY t.name
            ORDER BY count DESC
        """, (self.session_start,))
        
        self.stats['topics'] = {r[0]: r[1] for r in c.fetchall()}
    
    def print_report(self):
        """Affiche le rapport de collecte détaillé"""
        print("\n" + "="*80)
        print("[RAPPORT] COLLECTE SESSION ACTUELLE")
        print("="*80)
        
        # Résumé session
        session = self.stats['session']
        print(f"\n[SESSION] RÉSUMÉ DE LA COLLECTE")
        print(f"   Articles collectés:     {session['total']:,}")
        print(f"   Articles taggés:        {session['tagged']:,} ({session['tagged']/max(session['total'],1)*100:.1f}%)")
        print(f"   Articles analysés:      {session['analyzed']:,} ({session['analyzed']/max(session['total'],1)*100:.1f}%)")
        print(f"   Heure de début:        {self.session_start[:19]}")
        
        # Détail par source
        if self.stats['by_source']:
            print(f"\n[SOURCES] DÉTAIL PAR SOURCE")
            print(f"   {'Source':<30s} {'Collectés':>10s} {'Taggés':>10s} {'Analysés':>10s}")
            print(f"   {'-'*30} {'-'*10} {'-'*10} {'-'*10}")
            for s in self.stats['by_source']:
                print(f"   {s['source']:<30s} {s['collected']:>10d} {s['tagged']:>10d} {s['analyzed']:>10d}")
        
        # Distribution topics
        if self.stats['topics']:
            print(f"\n[TOPICS] DISTRIBUTION DES TOPICS (SESSION)")
            for topic, count in sorted(self.stats['topics'].items(), key=lambda x: -x[1])[:10]:
                pct = (count / max(session['tagged'], 1)) * 100
                print(f"   • {topic:25s}: {count:4d} articles ({pct:5.1f}%)")
        
        # Distribution sentiment
        if self.stats['sentiment']:
            print(f"\n[SENTIMENT] DISTRIBUTION DU SENTIMENT (SESSION)")
            total_sent = sum(self.stats['sentiment'].values())
            for label, count in sorted(self.stats['sentiment'].items(), key=lambda x: -x[1]):
                pct = (count / max(total_sent, 1)) * 100
                print(f"   • {label:10s}: {count:4d} articles ({pct:5.1f}%)")
        
        print("\n" + "="*80 + "\n")
    
    def close(self):
        self.conn.close()

