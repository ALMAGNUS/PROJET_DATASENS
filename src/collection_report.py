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
    
    def _is_foundation_source(self, source_name: str) -> bool:
        """Détermine si une source est statique (fondation) : Kaggle, GDELT_events, ZZDB (toutes)
        Ces sources sont en local et intégrées UNE SEULE FOIS, puis exclues des rapports quotidiens
        
        ZZDB (synthetic + CSV) : Jeu de données synthétiques créé avec Faker pour le projet
        → TOUTES les sources ZZDB sont statiques (fondation), pas dynamiques"""
        source_lower = source_name.lower()
        # Sources fondation : Kaggle (tous), GDELT_events (seulement celui-ci), ZZDB (toutes)
        return ('kaggle' in source_lower or 
                (source_lower == 'gdelt_events') or  # Seulement gdelt_events (local), pas GDELT_Last15_English (dynamique)
                ('zzdb' in source_lower))  # TOUTES les sources ZZDB (synthetic + CSV) sont fondation
    
    def _is_foundation_integrated(self, source_name: str) -> bool:
        """Vérifie si une source fondation est déjà intégrée (via sync_log ou articles existants)"""
        c = self.conn.cursor()
        try:
            # Vérifier sync_log avec status FOUNDATION_INTEGRATED
            c.execute("""
                SELECT COUNT(*) 
                FROM sync_log sl
                JOIN source s ON sl.source_id = s.source_id
                WHERE s.name = ? AND sl.status = 'FOUNDATION_INTEGRATED'
            """, (source_name,))
            if c.fetchone()[0] > 0:
                return True
        except:
            pass
        
        # Fallback: vérifier si des articles existent déjà pour cette source
        try:
            c.execute("""
                SELECT COUNT(*) 
                FROM raw_data r
                JOIN source s ON r.source_id = s.source_id
                WHERE s.name = ?
            """, (source_name,))
            return c.fetchone()[0] > 0
        except:
            return False
    
    def collect_session_stats(self):
        """Collecte les stats de la session actuelle (EXCLUT les sources fondation déjà intégrées)"""
        c = self.conn.cursor()
        
        # Articles collectés dans cette session (après session_start)
        # EXCLURE les sources fondation déjà intégrées (Kaggle, GDELT_events, ZZDB CSV)
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
            source_name = r[0]
            
            # EXCLURE les sources fondation déjà intégrées (ne plus les afficher dans les rapports quotidiens)
            if self._is_foundation_source(source_name) and self._is_foundation_integrated(source_name):
                continue  # Skip cette source (déjà intégrée, ne plus l'afficher)
            
            self.stats['by_source'].append({
                'source': source_name,
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
        
        # Détail par source avec classification
        if self.stats['by_source']:
            print(f"\n[SOURCES] DÉTAIL PAR SOURCE")
            print(f"   {'Source':<30s} {'Collectés':>10s} {'Taggés':>10s} {'Analysés':>10s} {'Type':>15s}")
            print(f"   {'-'*30} {'-'*10} {'-'*10} {'-'*10} {'-'*15}")
            zzdb_found = False
            kaggle_found = False
            zzdb_total = 0
            zzdb_sources = []
            self.zzdb_total = 0  # Pour utilisation dans les notes
            for s in self.stats['by_source']:
                source_name = s['source']
                source_lower = source_name.lower()
                
                # Regrouper les sources ZZDB
                if 'zzdb' in source_lower:
                    zzdb_found = True
                    zzdb_total += s['collected']
                    self.zzdb_total = zzdb_total  # Stocker pour les notes
                    zzdb_sources.append((source_name, s))
                    continue  # On affichera après
                
                # Classification des autres sources
                if 'kaggle' in source_lower:
                    source_type = "[FICHIERS PLATS]"
                    marker = ""
                    kaggle_found = True
                else:
                    source_type = "[SOURCE RÉELLE]"
                    marker = ""
                
                print(f"   {source_name:<30s} {s['collected']:>10d} {s['tagged']:>10d} {s['analyzed']:>10d} {source_type:>15s}{marker}")
            
            # Afficher ZZDB regroupé
            if zzdb_sources:
                print(f"   {'ZZDB (TOTAL)':<30s} {zzdb_total:>10d} {'':>10s} {'':>10s} {'[DB NON-REL]':>15s} [DONNÉES SYNTHÈSE] [LAB IA]")
                for source_name, s in zzdb_sources:
                    status = "(désactivé)" if 'synthetic' in source_name.lower() else "(actif)"
                    print(f"      └─ {source_name:<27s} {s['collected']:>10d} {s['tagged']:>10d} {s['analyzed']:>10d} {status}")
            
            # Notes explicatives
            print(f"\n   [CLASSIFICATION DES SOURCES]")
            print(f"   • Sources FONDATION (statiques, locales) : Intégrées UNE SEULE FOIS, puis EXCLUES des rapports quotidiens")
            print(f"     - Kaggle : Fichiers plats (CSV/JSON) - Datasets locaux")
            print(f"     - GDELT_events : Événements globaux - Fichiers locaux")
            print(f"     - ZZDB (toutes) : Données synthétiques académiques créées avec Faker pour le projet")
            print(f"       → zzdb_synthetic (SQLite DB) + zzdb_csv (CSV export) = TOUTES statiques (fondation)")
            if kaggle_found:
                print(f"   • Kaggle : Fichiers plats (CSV/JSON) - Datasets locaux (intégration unique)")
            if zzdb_found:
                print(f"   • ZZDB : Base de données non relationnelle (SQLite) + CSV export - DONNÉES DE SYNTHÈSE [LAB IA]")
                print(f"   • ZZDB permet d'enrichir l'analyse des sentiments français dans un contexte de recherche.")
                print(f"   • DONNÉES DE SYNTHÈSE spécialisées en climat social, politique, économique et financier français.")
                print(f"   • Sources ZZDB :")
                print(f"     - zzdb_synthetic (SQLite DB) : DÉSACTIVÉ (articles historiques uniquement)")
                print(f"     - zzdb_csv (CSV export) : ACTIF (source principale, intégration unique comme fondation)")
                print(f"   • Total ZZDB dans datasens.db : {self.zzdb_total} articles (données de synthèse)")
                print(f"   • Les données de synthèse ZZDB sont intégrées comme fondation statique pour structurer le dataset.")
                print(f"   • NOTE : Les sources fondation (Kaggle, GDELT_events, ZZDB CSV) n'apparaissent plus dans les rapports")
                print(f"     quotidiens une fois intégrées (elles sont dans la DB mais ne sont plus collectées).")
        
        # Distribution topics
        if self.stats['topics']:
            print(f"\n[TOPICS] DISTRIBUTION DES TOPICS (SESSION)")
            for topic, count in sorted(self.stats['topics'].items(), key=lambda x: -x[1])[:10]:
                pct = (count / max(session['tagged'], 1)) * 100
                print(f"   • {topic:25s}: {count:4d} articles ({pct:5.1f}%)")
        
        # Distribution sentiment - AFFICHAGE COMPLET (positif, négatif, neutre)
        print(f"\n[SENTIMENT] DISTRIBUTION DU SENTIMENT (SESSION)")
        if self.stats['sentiment']:
            total_sent = sum(self.stats['sentiment'].values())
            # Afficher dans l'ordre : positif, négatif, neutre (même si 0)
            sentiment_order = ['positif', 'négatif', 'neutre']
            for label in sentiment_order:
                count = self.stats['sentiment'].get(label, 0)
                pct = (count / max(total_sent, 1)) * 100
                marker = " ⚠️" if label == 'négatif' and count == 0 else ""
                print(f"   • {label:10s}: {count:4d} articles ({pct:5.1f}%){marker}")
            
            # Afficher aussi les autres labels s'il y en a
            for label, count in sorted(self.stats['sentiment'].items(), key=lambda x: -x[1]):
                if label not in sentiment_order:
                    pct = (count / max(total_sent, 1)) * 100
                    print(f"   • {label:10s}: {count:4d} articles ({pct:5.1f}%)")
        else:
            print(f"   ⚠️  Aucun sentiment analysé dans cette session")
        
        # Note sur la vision du projet
        print(f"\n[VISION] FINALITÉ DU PROJET")
        print(f"   Analyser l'état des sentiments des français pour alimenter :")
        print(f"   • Acteurs politiques : Faire ressortir les préoccupations des français")
        print(f"   • Acteurs financiers : Guider les décisions d'investissements")
        print(f"   Voir docs/VISION_ACADEMIQUE.md pour plus de détails.")
        
        print("\n" + "="*80 + "\n")
    
    def close(self):
        self.conn.close()

