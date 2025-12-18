"""Sentiment Analyzer → MODEL_OUTPUT"""
import sqlite3
import re
from datetime import datetime

class SentimentAnalyzer:
    # Liste de mots-clés positifs (forts et modérés)
    POS_STRONG = ['excellent', 'fantastique', 'génial', 'parfait', 'merveilleux', 'formidable', 
                  'extraordinaire', 'remarquable', 'exceptionnel', 'splendide', 'magnifique',
                  'brillant', 'superbe', 'idéal', 'optimal', 'optimal', 'réussi', 'victoire',
                  'succès', 'triomphe', 'gagnant', 'champion', 'meilleur', 'supérieur']
    
    POS_MODERATE = ['bien', 'bon', 'super', 'agréable', 'satisfaisant', 'positif', 'favorable',
                    'prometteur', 'encourageant', 'optimiste', 'constructif', 'utile', 'efficace',
                    'performant', 'solide', 'stable', 'croissance', 'hausse', 'augmentation',
                    'amélioration', 'progrès', 'développement', 'expansion', 'montée', 'gain',
                    'profit', 'bénéfice', 'avantage', 'opportunité', 'espoir', 'confiance']
    
    # Liste de mots-clés négatifs (forts et modérés)
    NEG_STRONG = ['horrible', 'terrible', 'catastrophe', 'désastre', 'tragédie', 'crise',
                  'échec', 'défaite', 'perte', 'chute', 'effondrement', 'faillite', 'ruine',
                  'désastreux', 'dramatique', 'grave', 'critique', 'urgent', 'danger',
                  'menace', 'risque', 'alarme', 'alerte', 'panique', 'chaos', 'désordre']
    
    NEG_MODERATE = ['mal', 'mauvais', 'nul', 'déçu', 'problème', 'difficile', 'compliqué',
                    'inquiétant', 'préoccupant', 'décevant', 'décevant', 'décevant', 'faible',
                    'insuffisant', 'limité', 'réduit', 'baisse', 'diminution', 'réduction',
                    'déclin', 'chute', 'baisse', 'baisse', 'déficit', 'perte', 'manque',
                    'absence', 'défaut', 'erreur', 'faute', 'difficulté', 'obstacle', 'barrière',
                    'contrainte', 'limitation', 'restriction', 'pénalité', 'sanction', 'amende']
    
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        # Compiler les regex pour recherche de mots entiers
        self.pos_patterns = [re.compile(r'\b' + re.escape(w) + r'\b', re.IGNORECASE) 
                            for w in self.POS_STRONG + self.POS_MODERATE]
        self.neg_patterns = [re.compile(r'\b' + re.escape(w) + r'\b', re.IGNORECASE) 
                            for w in self.NEG_STRONG + self.NEG_MODERATE]
    
    def analyze(self, text: str) -> tuple[str, float]:
        if not text or len(text.strip()) < 10:
            return ('neutre', 0.5)
        
        t = text.lower()
        
        # Compter les occurrences avec poids (fort = 2, modéré = 1)
        pos_score = 0
        for i, pattern in enumerate(self.pos_patterns):
            matches = len(pattern.findall(t))
            if i < len(self.POS_STRONG):
                pos_score += matches * 2  # Poids fort
            else:
                pos_score += matches * 1  # Poids modéré
        
        neg_score = 0
        for i, pattern in enumerate(self.neg_patterns):
            matches = len(pattern.findall(t))
            if i < len(self.NEG_STRONG):
                neg_score += matches * 2  # Poids fort
            else:
                neg_score += matches * 1  # Poids modéré
        
        # Calculer le score total et la différence
        total_score = pos_score + neg_score
        
        if total_score == 0:
            # Aucun mot-clé trouvé → neutre avec score bas
            return ('neutre', 0.5)
        
        # Calculer le ratio
        pos_ratio = pos_score / total_score
        neg_ratio = neg_score / total_score
        
        # Seuil pour classification
        if pos_ratio > 0.6 and pos_score >= 2:
            # Positif si > 60% et au moins 2 points
            confidence = min(0.5 + (pos_ratio - 0.6) * 1.25, 0.95)
            return ('positif', round(confidence, 3))
        elif neg_ratio > 0.6 and neg_score >= 2:
            # Négatif si > 60% et au moins 2 points
            confidence = min(0.5 + (neg_ratio - 0.6) * 1.25, 0.95)
            return ('négatif', round(confidence, 3))
        elif pos_score > neg_score and pos_score >= 1:
            # Positif si plus de positifs (même si < 60%)
            confidence = min(0.5 + (pos_ratio - 0.5) * 0.8, 0.85)
            return ('positif', round(confidence, 3))
        elif neg_score > pos_score and neg_score >= 1:
            # Négatif si plus de négatifs (même si < 60%)
            confidence = min(0.5 + (neg_ratio - 0.5) * 0.8, 0.85)
            return ('négatif', round(confidence, 3))
        else:
            # Neutre si équilibré ou scores trop faibles
            # Score varie selon l'équilibre
            if abs(pos_score - neg_score) <= 1:
                return ('neutre', 0.5)
            elif pos_score > neg_score:
                return ('neutre', 0.55)  # Légèrement positif mais pas assez
            else:
                return ('neutre', 0.45)  # Légèrement négatif mais pas assez
    
    def save(self, raw_data_id: int, title: str, content: str) -> bool:
        sent, score = self.analyze(f"{title} {content}")
        c = self.conn.cursor()
        c.execute("DELETE FROM model_output WHERE raw_data_id = ? AND model_name = 'sentiment_keyword'", (raw_data_id,))
        c.execute("INSERT INTO model_output (raw_data_id, model_name, label, score, created_at) VALUES (?, ?, ?, ?, ?)",
                 (raw_data_id, 'sentiment_keyword', sent, round(score, 3), datetime.now().isoformat()))
        self.conn.commit()
        return True
    
    def close(self):
        self.conn.close()

