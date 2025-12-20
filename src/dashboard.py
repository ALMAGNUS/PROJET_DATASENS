"""DataSens Dashboard - Visualisation enrichissement dataset"""
import sqlite3
from datetime import datetime


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
        print("\n[RESUME] RÉSUMÉ GLOBAL")
        print(f"   Total articles:        {self.stats['total']:,}")
        print(f"   Articles uniques:      {self.stats['unique']:,}")
        print(f"   Nouveaux aujourd'hui:  {self.stats['new_today']:,}")
        print(f"   Articles enrichis:     {self.stats['enriched']:,} ({self.stats['enriched']/max(self.stats['total'],1)*100:.1f}%)")

        # Nouveaux articles par source aujourd'hui
        if self.stats['new_by_source']:
            print("\n[NOUVEAUX] NOUVEAUX ARTICLES AUJOURD'HUI PAR SOURCE")
            for source, count in sorted(self.stats['new_by_source'].items(), key=lambda x: -x[1]):
                source_lower = source.lower()
                if 'zzdb' in source_lower:
                    marker = " [DB NON-REL] [DONNÉES SYNTHÈSE] [LAB IA]"
                elif 'kaggle' in source_lower:
                    marker = " [FICHIERS PLATS]"
                else:
                    marker = ""
                print(f"   • {source:30s}: {count:4d} articles{marker}")

        # Enrichissement Topics
        print("\n[TOPICS] ENRICHISSEMENT TOPICS")
        print(f"   Articles taggés:        {self.stats['topics']['tagged']:,}")
        print(f"   Topics utilisés:       {self.stats['topics']['topics_used']}")
        print(f"   Confiance moyenne:     {self.stats['topics']['avg_confidence']:.2f}")
        if self.stats['topics_dist']:
            print("   Distribution:")
            for topic, count in sorted(self.stats['topics_dist'].items(), key=lambda x: -x[1])[:5]:
                print(f"      • {topic:20s}: {count:4d} articles")

        # Enrichissement Sentiment - AFFICHAGE COMPLET (positif, négatif, neutre)
        print("\n[SENTIMENT] ENRICHISSEMENT SENTIMENT")
        total_sent = sum(s['count'] for s in self.stats['sentiment'].values())
        if total_sent > 0:
            # Afficher dans l'ordre : positif, négatif, neutre (même si 0)
            sentiment_order = ['positif', 'négatif', 'neutre']
            for label in sentiment_order:
                data = self.stats['sentiment'].get(label, {'count': 0, 'avg_score': 0.0})
                pct = (data['count'] / max(total_sent, 1)) * 100
                marker = " ⚠️" if label == 'négatif' and data['count'] == 0 else ""
                print(f"   {label:10s}: {data['count']:4d} articles ({pct:5.1f}%) - Score moyen: {data['avg_score']:.2f}{marker}")

            # Afficher aussi les autres labels s'il y en a
            for label, data in sorted(self.stats['sentiment'].items(), key=lambda x: -x[1]['count']):
                if label not in sentiment_order:
                    pct = (data['count'] / max(total_sent, 1)) * 100
                    print(f"   {label:10s}: {data['count']:4d} articles ({pct:5.1f}%) - Score moyen: {data['avg_score']:.2f}")
        else:
            print("   ⚠️  Aucun sentiment analysé")

        # Par source avec classification
        print("\n[SOURCES] ARTICLES PAR SOURCE")
        print(f"   {'Source':<30s} {'Total':>8s} {'Unique':>8s} {'Dernière collecte':>20s} {'Type':>15s}")
        print(f"   {'-'*30} {'-'*8} {'-'*8} {'-'*20} {'-'*15}")
        zzdb_found = False
        kaggle_found = False
        zzdb_total = 0
        zzdb_unique = 0
        zzdb_sources = []
        for s in self.stats['by_source'][:15]:
            last = s['last'][:19] if s['last'] else 'Jamais'
            source_name = s['source']
            source_lower = source_name.lower()

            # Regrouper les sources ZZDB
            if 'zzdb' in source_lower:
                zzdb_found = True
                zzdb_total += s['total']
                zzdb_unique += s['unique']
                zzdb_sources.append((source_name, s, last))
                continue  # On affichera après

            # Classification des autres sources
            if 'kaggle' in source_lower:
                source_type = "[FICHIERS PLATS]"
                marker = ""
                kaggle_found = True
            else:
                source_type = "[SOURCE RÉELLE]"
                marker = ""

            print(f"   {source_name:<30s} {s['total']:>8d} {s['unique']:>8d} {last:>20s} {source_type:>15s}{marker}")

        # Afficher ZZDB regroupé
        if zzdb_sources:
            last_zzdb = max((s[2] for s in zzdb_sources), key=lambda x: x if x != 'Jamais' else '')
            print(f"   {'ZZDB (TOTAL)':<30s} {zzdb_total:>8d} {zzdb_unique:>8d} {last_zzdb[:19] if last_zzdb != 'Jamais' else 'Jamais':>20s} {'[DB NON-REL]':>15s} [DONNÉES SYNTHÈSE] [LAB IA]")
            for source_name, s, last in zzdb_sources:
                status = "(désactivé)" if 'synthetic' in source_name.lower() else "(actif)"
                print(f"      └─ {source_name:<27s} {s['total']:>8d} {s['unique']:>8d} {last[:19] if last != 'Jamais' else 'Jamais':>20s} {status}")

        # Notes explicatives
        print("\n   [CLASSIFICATION DES SOURCES]")
        if kaggle_found:
            print("   • Kaggle : Fichiers plats (CSV/JSON) - Datasets locaux en format plat")
        if zzdb_found:
            print("   • ZZDB : Base de données non relationnelle (SQLite) + CSV export - DONNÉES DE SYNTHÈSE [LAB IA]")
            print("   • ZZDB enrichit l'analyse des sentiments français dans un contexte de recherche.")
            print("   • DONNÉES DE SYNTHÈSE spécialisées en climat social, politique, économique et financier français.")
            print("   • Sources ZZDB :")
            print("     - zzdb_synthetic (SQLite DB) : DÉSACTIVÉ (articles historiques uniquement)")
            print("     - zzdb_csv (CSV export) : ACTIF (source principale, intégration unique comme fondation)")
            print(f"   • Total ZZDB dans datasens.db : {zzdb_total if zzdb_found else 0} articles (données de synthèse)")
            print("   • Les données de synthèse ZZDB sont intégrées comme fondation statique pour structurer le dataset.")

        # Évaluation dataset pour IA
        print("\n[IA] ÉVALUATION DATASET POUR IA")
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
            print("   [INFO] Solution: Lancer 'python scripts/enrich_all_articles.py' pour enrichir tous les articles")

        # Note sur la vision du projet
        print("\n[VISION] FINALITÉ DU PROJET")
        print("   Analyser l'état des sentiments des français pour alimenter :")
        print("   • Acteurs politiques : Faire ressortir les préoccupations des français")
        print("   • Acteurs financiers : Guider les décisions d'investissements")
        print("   Voir docs/VISION_ACADEMIQUE.md pour plus de détails.")

        print("\n" + "="*80 + "\n")

    def close(self):
        self.conn.close()

