"""Rapport de collecte détaillé - Session actuelle"""
import sqlite3
from datetime import datetime

from loguru import logger

from .e1.console import ConsolePrinter
from .e1.ui_messages import UiMessages


class CollectionReport:
    def __init__(self, db_path: str, session_start_time: str | None = None, console: ConsolePrinter | None = None):
        self.conn = sqlite3.connect(db_path)
        self.session_start = session_start_time or datetime.now().isoformat()
        self.stats = {}
        self.console = console or ConsolePrinter()

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
        logger.info("CollectionReport stats collected for session {}", self.session_start)

    def print_report(self):
        """Affiche un rapport de collecte concis (chiffres uniquement)"""
        logger.info("CollectionReport print start")
        console_write = self.console.write
        console_write("\n" + UiMessages.report_title()[0])
        console_write(UiMessages.report_title()[1])
        console_write(UiMessages.report_title()[2])

        # Résumé session (chiffres uniquement)
        session = self.stats['session']
        console_write("\n" + UiMessages.session_resume_title())
        console_write(f"   Articles collectés: {session['total']:,}")
        console_write(f"   Articles taggés:    {session['tagged']:,}")
        console_write(f"   Articles analysés:  {session['analyzed']:,}")
        console_write(f"   Début session:      {self.session_start[:19]}")

        # Détail par source (chiffres uniquement)
        if self.stats['by_source']:
            console_write("\n" + UiMessages.sources_detail_title())
            console_write(f"   {'Source':<30s} {'Collectés':>10s} {'Taggés':>10s} {'Analysés':>10s}")
            console_write(f"   {'-'*30} {'-'*10} {'-'*10} {'-'*10}")
            zzdb_total = 0
            zzdb_sources = []
            self.zzdb_total = 0  # Pour utilisation dans les notes
            for s in self.stats['by_source']:
                source_name = s['source']
                source_lower = source_name.lower()

                # Regrouper les sources ZZDB
                if 'zzdb' in source_lower:
                    zzdb_total += s['collected']
                    self.zzdb_total = zzdb_total  # Stocker pour les notes
                    zzdb_sources.append((source_name, s))
                    continue  # On affichera après

                console_write(f"   {source_name:<30s} {s['collected']:>10d} {s['tagged']:>10d} {s['analyzed']:>10d}")

            # Afficher ZZDB regroupé
            if zzdb_sources:
                console_write(f"   {'ZZDB (TOTAL)':<30s} {zzdb_total:>10d} {'':>10s} {'':>10s}")
                for source_name, s in zzdb_sources:
                    status = "(désactivé)" if 'synthetic' in source_name.lower() else "(actif)"
                    console_write(
                        f"      └─ {source_name:<27s} {s['collected']:>10d} {s['tagged']:>10d} {s['analyzed']:>10d} {status}"
                    )

        # IA - Sentiment (session)
        console_write("\n" + UiMessages.sentiment_distribution_title())
        total_sent = sum(self.stats.get('sentiment', {}).values())
        sentiment_order = ['positif', 'négatif', 'neutre']
        for label in sentiment_order:
            count = self.stats.get('sentiment', {}).get(label, 0)
            pct = (count / max(total_sent, 1)) * 100
            console_write(f"   {label:10s}: {count:4d} ({pct:5.1f}%)")

        # IA - Topics (Top 5 session)
        if self.stats.get('topics'):
            console_write("\n" + UiMessages.topics_distribution_title())
            for topic, count in sorted(self.stats['topics'].items(), key=lambda x: -x[1])[:5]:
                pct = (count / max(self.stats['session']['tagged'], 1)) * 100
                console_write(f"   • {topic:25s}: {count:4d} ({pct:5.1f}%)")

        console_write("\n" + "="*80 + "\n")
        logger.info("CollectionReport print complete")

    def close(self):
        self.conn.close()

