"""Topic Tagger - max 2 topics → DOCUMENT_TOPIC"""
import sqlite3

class TopicTagger:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.keywords = {
            # Économie & Finance
            'finance': ['prix', 'coût', 'économie', 'fiscal', 'budget', 'taux', 'inflation', 'déflation',
                       'bourse', 'marché', 'investissement', 'action', 'obligation', 'crédit', 'dette',
                       'banque', 'banquier', 'financement', 'capital', 'patrimoine', 'revenu', 'salaire',
                       'impôt', 'taxe', 'cotisation', 'retraite', 'pension', 'allocation', 'prestation'],
            'entreprise': ['entreprise', 'société', 'compagnie', 'firme', 'boîte', 'startup', 'PME',
                          'multinationale', 'dirigeant', 'PDG', 'patron', 'employé', 'salarié', 'travailleur',
                          'emploi', 'recrutement', 'licenciement', 'démission', 'carrière', 'métier',
                          'secteur', 'industrie', 'production', 'fabrication', 'commerce', 'vente'],
            'politique': ['gouvernement', 'élection', 'loi', 'parlement', 'ministre', 'débat', 'député',
                         'sénateur', 'président', 'premier ministre', 'ministère', 'parti', 'politique',
                         'campagne', 'vote', 'scrutin', 'référendum', 'assemblée', 'sénat', 'conseil',
                         'municipal', 'régional', 'national', 'européen', 'international', 'diplomatie'],
            'technologie': ['tech', 'technologie', 'logiciel', 'internet', 'app', 'application', 'cloud',
                          'IA', 'intelligence artificielle', 'robot', 'robotique', 'automatisation',
                          'numérique', 'digital', 'informatique', 'ordinateur', 'smartphone', 'tablette',
                          'réseau', 'cybersécurité', 'données', 'big data', 'blockchain', 'crypto'],
            'santé': ['santé', 'médecin', 'docteur', 'hôpital', 'clinique', 'maladie', 'vaccin', 'virus',
                     'épidémie', 'pandémie', 'traitement', 'médicament', 'thérapie', 'soin', 'patient',
                     'malade', 'symptôme', 'diagnostic', 'opération', 'chirurgie', 'urgence', 'ambulance'],
            'société': ['social', 'société', 'culture', 'éducation', 'école', 'université', 'étudiant',
                       'jeunes', 'jeunesse', 'famille', 'parent', 'enfant', 'immigration', 'immigré',
                       'réfugié', 'intégration', 'diversité', 'égalité', 'discrimination', 'racisme',
                       'sexisme', 'féminisme', 'droits', 'liberté', 'démocratie', 'citoyen', 'civisme'],
            'environnement': ['climat', 'environnement', 'écologie', 'pollution', 'énergie', 'renouvelable',
                            'nucléaire', 'solaire', 'éolien', 'recyclage', 'nature', 'biodiversité',
                            'déforestation', 'réchauffement', 'gaz à effet de serre', 'CO2', 'carbone',
                            'durable', 'transition', 'écologique', 'vert', 'bio', 'organique'],
            'sport': ['sport', 'football', 'soccer', 'tennis', 'rugby', 'basket', 'handball', 'volley',
                     'équipe', 'match', 'compétition', 'championnat', 'coupe', 'tournoi', 'athlète',
                     'joueur', 'entraîneur', 'stade', 'olympique', 'paralympique', 'sportif'],
            'média': ['média', 'journal', 'journaliste', 'presse', 'télévision', 'radio', 'internet',
                     'réseau social', 'facebook', 'twitter', 'instagram', 'information', 'actualité',
                     'nouvelle', 'reportage', 'enquête', 'interview', 'émission', 'documentaire'],
            'culture': ['culture', 'art', 'musique', 'cinéma', 'film', 'théâtre', 'spectacle', 'concert',
                       'exposition', 'musée', 'galerie', 'livre', 'roman', 'auteur', 'écrivain',
                       'peinture', 'sculpture', 'danse', 'festival', 'événement', 'création'],
            'transport': ['transport', 'voiture', 'automobile', 'train', 'métro', 'bus', 'avion',
                         'aéroport', 'gare', 'route', 'autoroute', 'trafic', 'embouteillage',
                         'mobilité', 'vélo', 'piéton', 'marchandise', 'logistique', 'livraison'],
            'logement': ['logement', 'habitation', 'maison', 'appartement', 'immobilier', 'propriétaire',
                        'locataire', 'loyer', 'prix', 'achat', 'vente', 'construction', 'rénovation',
                        'isolation', 'énergie', 'chauffage', 'logement social', 'HLM', 'crise'],
            'sécurité': ['sécurité', 'police', 'gendarmerie', 'sécurité civile', 'pompier', 'urgence',
                        'incendie', 'accident', 'attentat', 'terrorisme', 'violence', 'agression',
                        'criminalité', 'délinquance', 'justice', 'tribunal', 'juge', 'avocat', 'prison'],
            'éducation': ['éducation', 'école', 'collège', 'lycée', 'université', 'étudiant', 'élève',
                          'professeur', 'enseignant', 'formation', 'apprentissage', 'diplôme', 'bac',
                          'licence', 'master', 'doctorat', 'recherche', 'scientifique', 'laboratoire'],
            'travail': ['travail', 'emploi', 'chômage', 'salarié', 'employeur', 'syndicat', 'grève',
                       'manifestation', 'négociation', 'convention', 'contrat', 'CDI', 'CDD', 'stage',
                       'formation', 'compétence', 'qualification', 'métier', 'profession', 'carrière'],
            'retraite': ['retraite', 'pension', 'retraité', 'senior', 'âge', 'vieillissement', 'dépendance',
                        'EHPAD', 'maison de retraite', 'allocation', 'minimum vieillesse', 'réforme'],
            'jeunesse': ['jeunesse', 'jeune', 'adolescent', 'étudiant', 'lycéen', 'collégien', 'orientation',
                        'formation', 'apprentissage', 'alternance', 'stage', 'premier emploi', 'insertion'],
            'international': ['international', 'monde', 'pays', 'nation', 'diplomatie', 'relations', 'traité',
                            'accord', 'commerce', 'échange', 'coopération', 'conflit', 'guerre', 'paix',
                            'ONU', 'UE', 'Europe', 'Union européenne', 'OTAN', 'migration', 'réfugié'],
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

