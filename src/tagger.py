"""Topic Tagger - max 2 topics → DOCUMENT_TOPIC"""
import sqlite3

class TopicTagger:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.keywords = {
            'finance': ['prix', 'coût', 'économie', 'fiscal', 'budget', 'taux', 'inflation'],
            'politique': ['gouvernement', 'élection', 'loi', 'parlement', 'ministre', 'débat'],
            'technologie': ['tech', 'logiciel', 'internet', 'app', 'cloud', 'IA', 'robot'],
            'santé': ['santé', 'médecin', 'hôpital', 'maladie', 'vaccin', 'virus'],
            'société': ['social', 'culture', 'éducation', 'jeunes', 'famille', 'immigration'],
            'environnement': ['climat', 'pollution', 'énergie', 'recyclage', 'nature'],
            'sport': ['sport', 'football', 'tennis', 'rugby', 'équipe', 'match'],
        }
        self._ensure_topics()
    
    def _ensure_topics(self):
        c = self.conn.cursor()
        for name in self.keywords:
            c.execute("SELECT topic_id FROM topic WHERE name = ?", (name,))
            if not c.fetchone():
                c.execute("INSERT INTO topic (name, keywords, category, active) VALUES (?, ?, ?, ?)",
                         (name, ','.join(self.keywords[name]), 'general', 1))
        self.conn.commit()
    
    def tag(self, raw_data_id: int, title: str, content: str) -> bool:
        text = f"{title} {content}".lower()
        scores = {name: min(sum(1 for kw in kws if kw in text) / len(kws), 1.0) 
                 for name, kws in self.keywords.items() if any(kw in text for kw in kws)}
        
        c = self.conn.cursor()
        c.execute("DELETE FROM document_topic WHERE raw_data_id = ?", (raw_data_id,))
        
        # Si aucun topic trouvé, assigner "autre" par défaut
        if not scores:
            c.execute("SELECT topic_id FROM topic WHERE name = ?", ('autre',))
            tid = c.fetchone()
            if not tid:
                c.execute("INSERT INTO topic (name, keywords, category, active) VALUES (?, ?, ?, ?)",
                         ('autre', 'divers,general', 'general', 1))
                self.conn.commit()
                c.execute("SELECT topic_id FROM topic WHERE name = ?", ('autre',))
                tid = c.fetchone()
            if tid:
                c.execute("INSERT INTO document_topic (raw_data_id, topic_id, confidence_score, tagger) VALUES (?, ?, ?, ?)",
                         (raw_data_id, tid[0], 0.3, 'keyword_default'))
                self.conn.commit()
                return True
            return False
        
        # Assigner max 2 topics avec meilleure confiance
        for topic_name, conf in sorted(scores.items(), key=lambda x: -x[1])[:2]:
            c.execute("SELECT topic_id FROM topic WHERE name = ?", (topic_name,))
            tid = c.fetchone()
            if tid:
                c.execute("INSERT INTO document_topic (raw_data_id, topic_id, confidence_score, tagger) VALUES (?, ?, ?, ?)",
                         (raw_data_id, tid[0], conf, 'keyword'))
        self.conn.commit()
        return True
    
    def close(self):
        self.conn.close()

