"""Topic Tagger v2 — dictionnaire bilingue FR+EN, pondération titre,
règles par source et normalisation d'accents.

Contrats conservés :
- Classe `TopicTagger(db_path: str)` instanciée identiquement à la v1.
- Méthode `tag(raw_data_id, title, content, source_name=None) -> bool` :
  la v1 appelait `tag(raw_data_id, title, content)` ; l'argument optionnel
  `source_name` permet à l'orchestrateur de re-tag d'injecter la source,
  sinon elle est résolue depuis SQLite (léger overhead mais robuste).
- Écrit dans `document_topic` (même schéma que v1), topic_1 + topic_2
  (topic_2 omis si score trop faible → plus de "autre" artificiel).
"""

from __future__ import annotations

import sqlite3
import unicodedata
from typing import Iterable


# ---------------------------------------------------------------------------
# Dictionnaire bilingue FR + EN
# ---------------------------------------------------------------------------
#
# Chaque topic possède deux listes de mots-clés : une francophone et une
# anglophone. Le matching est effectué sur la forme normalisée (sans accents,
# minuscules), donc les entrées FR sont écrites sans se soucier des accents.
# L'extension est simple : ajouter une clé au dict ou une entrée aux listes.

TOPIC_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "finance": {
        "fr": [
            "prix", "cout", "economie", "fiscal", "budget", "taux",
            "inflation", "deflation", "bourse", "marche boursier", "action",
            "obligation", "credit", "dette", "banque", "banquier",
            "financement", "capital", "patrimoine", "revenu", "salaire",
            "impot", "taxe", "cotisation", "pension", "allocation",
            "prestation", "benefice", "chiffre d affaires", "rentabilite",
            "dividende", "trader", "investissement", "investisseur",
        ],
        "en": [
            "stock", "stocks", "market", "markets", "shares", "earnings",
            "revenue", "profit", "loss", "economy", "economic", "finance",
            "financial", "inflation", "deflation", "bond", "bonds",
            "interest rate", "rate hike", "tax", "taxes", "budget", "debt",
            "credit", "bank", "banking", "banker", "dividend", "trader",
            "trading", "investor", "investment", "wall street", "nasdaq",
            "dow jones", "s&p", "forex", "currency", "dollar", "euro",
        ],
    },
    "entreprise": {
        "fr": [
            "entreprise", "societe", "compagnie", "firme", "startup", "pme",
            "multinationale", "dirigeant", "pdg", "patron", "employe",
            "salarie", "travailleur", "emploi", "recrutement", "licenciement",
            "demission", "carriere", "metier", "secteur", "industrie",
            "production", "fabrication", "commerce", "vente", "acquisition",
            "fusion", "faillite",
        ],
        "en": [
            "company", "corporation", "enterprise", "startup", "firm", "ceo",
            "cfo", "cto", "executive", "employee", "worker", "layoff",
            "layoffs", "hiring", "recruiting", "merger", "acquisition",
            "bankruptcy", "bankrupt", "ipo", "earnings call", "quarterly",
        ],
    },
    "politique": {
        "fr": [
            "gouvernement", "election", "loi", "parlement", "ministre",
            "debat politique", "depute", "senateur", "president",
            "premier ministre", "ministere", "parti", "politique", "campagne",
            "vote", "scrutin", "referendum", "assemblee", "senat", "conseil",
            "municipal", "regional", "diplomatie", "reforme", "presidentielle",
            "legislative", "elysee", "matignon",
        ],
        "en": [
            "government", "election", "elections", "parliament", "minister",
            "prime minister", "president", "senator", "senate", "congress",
            "congressman", "congresswoman", "democrat", "republican",
            "trump", "biden", "vote", "voting", "ballot", "referendum",
            "white house", "diplomat", "diplomacy", "policy", "political",
            "politics", "politician", "campaign", "capitol", "legislation",
        ],
    },
    "technologie": {
        "fr": [
            "tech", "technologie", "logiciel", "internet", "app",
            "application", "cloud", "ia", "intelligence artificielle",
            "robot", "robotique", "automatisation", "numerique", "digital",
            "informatique", "ordinateur", "smartphone", "tablette", "reseau",
            "cybersecurite", "donnees", "big data", "blockchain", "crypto",
            "bitcoin", "ethereum", "algorithme", "modele", "chatbot",
        ],
        "en": [
            "tech", "technology", "software", "hardware", "internet",
            "application", "cloud", "ai", "artificial intelligence",
            "machine learning", "deep learning", "robot", "robotics",
            "automation", "digital", "computer", "computing", "smartphone",
            "tablet", "network", "cybersecurity", "data", "big data",
            "blockchain", "crypto", "cryptocurrency", "bitcoin", "ethereum",
            "algorithm", "chatbot", "openai", "google", "apple", "microsoft",
            "meta", "nvidia", "amazon", "ios", "android", "windows", "linux",
        ],
    },
    "santé": {
        "fr": [
            "sante", "medecin", "docteur", "hopital", "clinique", "maladie",
            "vaccin", "virus", "epidemie", "pandemie", "traitement",
            "medicament", "therapie", "soin", "patient", "malade",
            "symptome", "diagnostic", "operation", "chirurgie", "urgence",
            "ambulance", "covid", "cancer", "diabete",
        ],
        "en": [
            "health", "healthcare", "doctor", "physician", "hospital",
            "clinic", "disease", "illness", "vaccine", "virus", "epidemic",
            "pandemic", "treatment", "medication", "drug", "therapy",
            "patient", "symptom", "diagnosis", "surgery", "emergency",
            "ambulance", "covid", "cancer", "diabetes", "mental health",
        ],
    },
    "société": {
        "fr": [
            "social", "societe", "immigration", "immigre", "refugie",
            "integration", "diversite", "egalite", "discrimination",
            "racisme", "sexisme", "feminisme", "droits", "liberte",
            "democratie", "citoyen", "civisme", "manifestation", "greve",
            "protestation",
        ],
        "en": [
            "society", "social", "immigration", "immigrant", "refugee",
            "integration", "diversity", "equality", "discrimination",
            "racism", "sexism", "feminism", "rights", "freedom", "democracy",
            "citizen", "protest", "protesters", "strike", "activism",
        ],
    },
    "environnement": {
        "fr": [
            "climat", "environnement", "ecologie", "pollution", "energie",
            "renouvelable", "nucleaire", "solaire", "eolien", "recyclage",
            "biodiversite", "deforestation", "rechauffement",
            "gaz a effet de serre", "co2", "carbone", "durable", "transition",
            "ecologique",
        ],
        "en": [
            "climate", "environment", "ecology", "ecological", "pollution",
            "renewable", "nuclear", "solar", "wind power", "recycling",
            "biodiversity", "deforestation", "warming", "global warming",
            "greenhouse", "carbon", "sustainable", "sustainability",
            "emissions", "green energy",
        ],
    },
    "meteo": {
        "fr": [
            "meteo", "temperature", "degre", "pluie", "averse", "neige",
            "orage", "vent", "rafale", "nuage", "nuageux", "ensoleille",
            "canicule", "gel", "humidite", "precipitation", "bulletin meteo",
            "temps",
        ],
        "en": [
            "weather", "temperature", "rain", "rainfall", "snow", "snowfall",
            "storm", "thunderstorm", "hurricane", "tornado", "wind", "gust",
            "cloud", "cloudy", "sunny", "overcast", "heatwave", "frost",
            "humidity", "precipitation", "forecast", "meteorological",
        ],
    },
    "sport": {
        "fr": [
            "sport", "football", "tennis", "rugby", "basket", "handball",
            "volley", "equipe", "match", "competition", "championnat",
            "coupe", "tournoi", "athlete", "joueur", "entraineur", "stade",
            "olympique", "paralympique", "sportif",
        ],
        "en": [
            "sport", "sports", "football", "soccer", "tennis", "rugby",
            "basketball", "nba", "nfl", "mlb", "nhl", "hockey", "baseball",
            "team", "match", "championship", "cup", "tournament", "athlete",
            "player", "coach", "stadium", "olympic", "olympics",
        ],
    },
    "média": {
        "fr": [
            "media", "journal", "journaliste", "presse", "television",
            "radio", "reseau social", "facebook", "twitter", "instagram",
            "tiktok", "youtube", "actualite", "reportage", "enquete",
            "interview", "emission", "documentaire",
        ],
        "en": [
            "newspaper", "journalist", "press release", "television",
            "podcast", "social media", "facebook", "twitter", "instagram",
            "tiktok", "youtube", "reporter", "reporting", "broadcast",
            "interview",
        ],
    },
    "culture": {
        "fr": [
            "culture", "art", "musique", "cinema", "film", "theatre",
            "spectacle", "concert", "exposition", "musee", "galerie",
            "livre", "roman", "auteur", "ecrivain", "peinture", "sculpture",
            "danse", "festival", "evenement culturel", "creation",
        ],
        "en": [
            "culture", "cultural", "art", "music", "movie", "cinema", "film",
            "theater", "theatre", "show", "concert", "exhibition", "museum",
            "gallery", "book", "novel", "author", "writer", "painting",
            "sculpture", "dance", "festival",
        ],
    },
    "transport": {
        "fr": [
            "transport", "voiture", "automobile", "train", "metro", "bus",
            "avion", "aeroport", "gare", "route", "autoroute", "trafic",
            "embouteillage", "mobilite", "velo", "pieton", "marchandise",
            "logistique", "livraison",
        ],
        "en": [
            "transport", "transportation", "car", "automobile", "vehicle",
            "train", "subway", "metro", "bus", "plane", "airplane",
            "aircraft", "airport", "highway", "traffic", "mobility",
            "bicycle", "bike", "pedestrian", "logistics", "shipping",
            "delivery",
        ],
    },
    "logement": {
        "fr": [
            "logement", "habitation", "maison", "appartement", "immobilier",
            "proprietaire", "locataire", "loyer", "achat immobilier",
            "vente immobiliere", "construction", "renovation", "isolation",
            "chauffage", "logement social", "hlm", "crise du logement",
        ],
        "en": [
            "housing", "house", "home", "apartment", "real estate",
            "property", "mortgage", "landlord", "tenant", "rent", "rental",
            "construction", "renovation", "insulation", "heating",
        ],
    },
    "sécurité": {
        "fr": [
            "securite", "police", "gendarmerie", "pompier", "incendie",
            "accident", "attentat", "terrorisme", "violence", "agression",
            "criminalite", "delinquance", "justice", "tribunal", "juge",
            "avocat", "prison", "meurtre", "homicide", "braquage",
        ],
        "en": [
            "security", "police", "officer", "firefighter", "fire",
            "accident", "attack", "terrorism", "terrorist", "violence",
            "assault", "crime", "criminal", "justice", "court", "judge",
            "lawyer", "prison", "jail", "murder", "homicide", "robbery",
            "shooting", "mass shooting",
        ],
    },
    "éducation": {
        "fr": [
            "education", "ecole", "college", "lycee", "universite",
            "etudiant", "eleve", "professeur", "enseignant", "formation",
            "apprentissage", "diplome", "bac", "licence", "master",
            "doctorat", "recherche", "scientifique", "laboratoire",
        ],
        "en": [
            "education", "school", "college", "university", "student",
            "pupil", "teacher", "professor", "training", "learning",
            "degree", "bachelor", "master", "phd", "research", "scientist",
            "laboratory", "academic",
        ],
    },
    "travail": {
        "fr": [
            "travail", "emploi", "chomage", "employeur", "syndicat", "greve",
            "negociation", "convention", "contrat", "cdi", "cdd", "stage",
            "competence", "qualification", "profession", "teletravail",
        ],
        "en": [
            "work", "workplace", "employment", "unemployment", "employer",
            "union", "strike", "negotiation", "contract", "internship",
            "skill", "profession", "remote work", "work from home",
        ],
    },
    "retraite": {
        "fr": [
            "retraite", "retraite anticipee", "retraite par capitalisation",
            "retraite par repartition", "pension", "pensionne", "senior",
            "age de depart", "vieillissement", "dependance", "ehpad",
            "maison de retraite", "minimum vieillesse", "reforme des retraites",
        ],
        "en": [
            "retirement", "pension", "pensioner", "retiree", "elderly",
            "aging", "nursing home", "social security", "medicare",
        ],
    },
    "jeunesse": {
        "fr": [
            "jeunesse", "jeune", "adolescent", "lyceen", "collegien",
            "orientation", "alternance", "premier emploi", "insertion",
            "mineur",
        ],
        "en": [
            "youth", "young people", "teenager", "teen", "adolescent",
            "apprenticeship", "first job",
        ],
    },
    "international": {
        "fr": [
            "diplomatie", "diplomatique", "traite", "accord bilateral",
            "accord international", "cooperation internationale",
            "conflit arme", "guerre", "cessez-le-feu", "paix",
            "onu", "otan", "union europeenne", "commission europeenne",
            "ambassade", "ambassadeur", "geopolitique", "geopolitical",
            "sommet", "g7", "g20",
        ],
        "en": [
            "diplomacy", "diplomatic", "diplomat", "treaty", "bilateral",
            "international cooperation", "armed conflict", "ceasefire",
            "united nations", "nato", "european union", "eu commission",
            "embassy", "ambassador", "geopolitics", "geopolitical",
            "summit", "g7", "g20",
        ],
    },
}


# Règles prioritaires par source : associe un nom de source (substring,
# insensible à la casse) à un topic avec une confiance fixe. Appliquées
# AVANT le matching lexical. Permet de rattraper les sources typées
# (ex: bulletins Open-Meteo qui ne mentionnent pas toujours "meteo").
SOURCE_RULES: list[tuple[str, str, float]] = [
    ("openweather", "meteo", 1.0),
    ("weather_openmeteo", "meteo", 1.0),
    ("open-meteo", "meteo", 1.0),
    ("weather_api", "meteo", 1.0),
    ("openweathermap", "meteo", 1.0),
]


# Seuil minimal pour accepter un second topic. En dessous on n'écrit pas
# de topic_2 plutôt que de retomber sur "autre" par défaut.
MIN_TOPIC2_SCORE: float = 0.03


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_accents(text: str) -> str:
    """Retire accents et normalise en minuscules — matching insensible."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accent = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_accent.lower()


def _count_occurrences(haystack: str, needles: Iterable[str]) -> int:
    """Compte le nombre de mots-clés distincts présents dans le texte."""
    return sum(1 for kw in needles if kw and kw in haystack)


# ---------------------------------------------------------------------------
# TopicTagger
# ---------------------------------------------------------------------------


class TopicTagger:
    """Tagger bilingue FR+EN avec pondération titre et règles par source."""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.keywords = TOPIC_KEYWORDS
        self.source_rules = SOURCE_RULES
        self._ensure_topics()

    # ------------------------------------------------------------------ DB

    def _ensure_topics(self) -> None:
        """Assure la présence de tous les topics (incl. 'autre') en base."""
        c = self.conn.cursor()
        names = list(self.keywords.keys()) + ["autre"]
        for name in names:
            c.execute("SELECT topic_id FROM topic WHERE name = ?", (name,))
            if c.fetchone():
                continue
            if name == "autre":
                c.execute(
                    "INSERT INTO topic (name, keywords, category, active) "
                    "VALUES (?, ?, ?, ?)",
                    ("autre", "divers,general", "general", 1),
                )
            else:
                kw_flat = self.keywords[name]["fr"] + self.keywords[name]["en"]
                c.execute(
                    "INSERT INTO topic (name, keywords, category, active) "
                    "VALUES (?, ?, ?, ?)",
                    (name, ",".join(kw_flat), "general", 1),
                )
        self.conn.commit()

    def _topic_id(self, name: str) -> int | None:
        c = self.conn.cursor()
        c.execute("SELECT topic_id FROM topic WHERE name = ?", (name,))
        row = c.fetchone()
        return int(row[0]) if row else None

    def _lookup_source_name(self, raw_data_id: int) -> str:
        c = self.conn.cursor()
        c.execute(
            "SELECT s.name FROM raw_data r "
            "LEFT JOIN source s ON r.source_id = s.source_id "
            "WHERE r.raw_data_id = ?",
            (raw_data_id,),
        )
        row = c.fetchone()
        return str(row[0]) if row and row[0] else ""

    # ------------------------------------------------------------------ Scoring

    def _source_rule(self, source_name: str) -> tuple[str, float] | None:
        if not source_name:
            return None
        src_low = source_name.lower()
        for pattern, topic, score in self.source_rules:
            if pattern in src_low:
                return topic, score
        return None

    def _score_topics(self, title: str, content: str) -> dict[str, float]:
        """Score chaque topic en pondérant titre (×3) et contenu (×1).

        Retourne un dict topic → score borné [0, 1].
        """
        title_n = _strip_accents(title or "")
        content_n = _strip_accents(content or "")
        scores: dict[str, float] = {}

        for topic, bundle in self.keywords.items():
            all_kw = bundle["fr"] + bundle["en"]
            n_total = len(all_kw) or 1
            title_hits = _count_occurrences(title_n, all_kw)
            content_hits = _count_occurrences(content_n, all_kw)
            weighted = title_hits * 3 + content_hits
            if weighted == 0:
                continue
            raw_score = weighted / n_total
            scores[topic] = min(raw_score, 1.0)
        return scores

    # ------------------------------------------------------------------ Public

    def tag(
        self,
        raw_data_id: int,
        title: str,
        content: str,
        source_name: str | None = None,
    ) -> bool:
        """Assigne topic_1 (toujours) et topic_2 (optionnel) à raw_data_id.

        Ordre de décision :
          1) Règles par source (ex: openweather_api → meteo)
          2) Matching lexical FR+EN pondéré (titre × 3)
          3) Fallback "autre" si rien ne matche
        """
        if source_name is None:
            source_name = self._lookup_source_name(raw_data_id)

        c = self.conn.cursor()
        c.execute("DELETE FROM document_topic WHERE raw_data_id = ?", (raw_data_id,))

        scores = self._score_topics(title, content)
        rule = self._source_rule(source_name or "")

        # Injecter la règle source comme topic "virtuel" à score élevé.
        if rule is not None:
            rule_topic, rule_score = rule
            scores[rule_topic] = max(scores.get(rule_topic, 0.0), rule_score)

        sorted_topics = sorted(scores.items(), key=lambda x: -x[1])

        # --- topic_1 -----------------------------------------------------
        if sorted_topics:
            t1_name, t1_score = sorted_topics[0]
            tagger_label = "source_rule" if (rule and t1_name == rule[0] and t1_score == rule[1]) else "keyword"
            tid1 = self._topic_id(t1_name)
            if tid1:
                c.execute(
                    "INSERT OR IGNORE INTO document_topic "
                    "(raw_data_id, topic_id, confidence_score, tagger) "
                    "VALUES (?, ?, ?, ?)",
                    (raw_data_id, tid1, float(t1_score), tagger_label),
                )
        else:
            # Aucun topic trouvé → fallback "autre"
            tid_autre = self._topic_id("autre")
            if tid_autre:
                c.execute(
                    "INSERT OR IGNORE INTO document_topic "
                    "(raw_data_id, topic_id, confidence_score, tagger) "
                    "VALUES (?, ?, ?, ?)",
                    (raw_data_id, tid_autre, 0.3, "keyword_default"),
                )
            self.conn.commit()
            return True

        # --- topic_2 (optionnel) ----------------------------------------
        # On n'écrit un topic_2 QUE s'il a un score significatif.
        # Plus de "autre" artificiel en seconde position.
        if len(sorted_topics) >= 2:
            t2_name, t2_score = sorted_topics[1]
            if t2_score >= MIN_TOPIC2_SCORE:
                tid2 = self._topic_id(t2_name)
                if tid2:
                    c.execute(
                        "INSERT OR IGNORE INTO document_topic "
                        "(raw_data_id, topic_id, confidence_score, tagger) "
                        "VALUES (?, ?, ?, ?)",
                        (raw_data_id, tid2, float(t2_score), "keyword"),
                    )

        self.conn.commit()
        return True

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
