# 🎯 DATASENS - Roadmap Agile & Scrum

**Date**: 16 décembre 2025  
**Product Owner**: [Toi]  
**Team Size**: 1 dev (MVP)  
**Tools**: Taiga (Backlog) + Trello (Sprint) + Miro (User Stories)

---

## 👥 Personas & Utilisateurs Finaux

### Persona 1: **Décideur Politique** 🏛️
- **Besoin**: Comprendre les sentiments français en temps réel
- **Valeur**: Prendre des décisions politiques éclairées
- **Actions**: Consulter dashboards, comparer sources, exporter rapports

### Persona 2: **Investisseur Financier** 💰
- **Besoin**: Intelligence stratégique sur le sentiment du marché
- **Valeur**: Identifier tendances avant la concurrence
- **Actions**: API real-time, alertes, tracking tendances

### Persona 3: **Chercheur/Analyste** 📊
- **Besoin**: Accès aux données brutes et traitées
- **Valeur**: Conduire analyses approfondies
- **Actions**: Télécharger datasets, interroger DB, reproduire analyses

---

## 🎭 Epics (Grandes Fonctionnalités)

### EPIC 1: **Collecte Omnicanale** 📡
**Valeur**: Aggréger 10 sources hétérogènes en 1 dataset unifié
- Ingérer RSS feeds (presse)
- Ingérer APIs (GDELT, INSEE, OpenWeather)
- Ingérer web scraping (sondages, avis)
- Ingérer datasets CSV/Parquet
- **Résultat**: ~5000 articles/jour

### EPIC 2: **Qualité & Nettoyage** ✨
**Valeur**: Assurer fiabilité des données pour IA
- Scorer qualité (0-1)
- Dédupliquer (fingerprinting SHA256)
- Normaliser formats
- Détecter anomalies
- **Résultat**: Dataset clean, qualité ≥ 0.5

### EPIC 3: **Intelligence de Sentiment** 🧠
**Valeur**: Transformer texte brut en insights actionnables
- Analyser sentiment (positif/négatif/neutre)
- Détecter topics (politique, économie, climat...)
- NER: Extraire entités (personnalités, organisations)
- Scorer confiance ML
- **Résultat**: Labels enrichis prêts pour IA

### EPIC 4: **Dashboards & Visualisation** 📈
**Valeur**: Voir patterns au coup d'œil
- Dashboard synthétique (KPIs)
- Graphiques par source
- Timeline sentiment
- Heatmaps par région/topic
- **Résultat**: Décisions 10x plus rapides

### EPIC 5: **API & Intégration** 🔌
**Valeur**: Intégrer DATASENS dans écosystème externe
- REST API (queries, exports)
- Webhooks (alertes temps réel)
- GraphQL (flexible queries)
- Python SDK
- **Résultat**: Adoptable par tiers

### EPIC 6: **Monitoring & Observabilité** 🔍
**Valeur**: Garantir uptime 99.9% + trust
- Alertes ingestion (erreurs source)
- Healthchecks (DB, APIs)
- Audit trail complet
- SLA tracking
- **Résultat**: Transparence totale

### EPIC 7: **Fine-tuning IA** 🤖
**Valeur**: Modèles sentiments customisés pour français
- Entraîner FlauBERT/CamemBERT
- Évaluer F1/Precision/Recall
- Versionner modèles (MLflow)
- A/B testing
- **Résultat**: Accuracy +25%

### EPIC 8: **Gouvernance & Conformité** ⚖️
**Valeur**: RGPD + Confiance
- Anonymisation données
- Retention policies
- Access control (roles)
- Compliance reports
- **Résultat**: Certifiable RGPD

---

## 📋 User Stories par Epic (Orientées Utilisateur)

### **EPIC 1: Collecte Omnicanale** 
*Bénéfice utilisateur: Avoir une vue complète de ce qui se dit en France, sans manquer de sources*

#### US 1.1: Surveiller l'actualité presse en continu [5 pts]
```
👤 En tant que [Décideur politique/Journaliste]
🎯 Je veux recevoir automatiquement tous les articles presse du jour
💎 Afin de rester informé de l'actualité sans passer 2h à chercher manuellement

Valeur utilisateur:
✅ Économise 2h/jour de recherche manuelle
✅ Ne rate aucune information importante
✅ Peut réagir rapidement aux news

Critères de succès:
- Je vois >= 500 articles presse/jour dans mon dashboard
- Les articles apparaissent dans les 30 min après publication
- Si une source presse est down, je suis alerté
- Je peux filtrer par source (Le Monde, Figaro, etc.)
```

#### US 1.2: Contextualiser l'opinion avec événements géopolitiques [8 pts]
```
👤 En tant que [Analyste politique/Investisseur]
🎯 Je veux corréler sentiment français + événements majeurs (élections, crises, conflits)
💎 Afin de comprendre POURQUOI le sentiment change (ne pas juste voir la courbe)

Valeur utilisateur:
✅ Comprends les causes derrière les variations de sentiment
✅ Anticipes réactions avant qu'elles explosent (early warning)
✅ Explique à mon boss "le sentiment a baissé car..."

Critères de succès:
- Vois événements géopolitiques France dans mon timeline
- Événements sont horodatés précisément
- Peux voir "avant/après événement" impact sentiment
- Détecte crises (attentats, grèves, scandales, élections)
```

#### US 1.3: Valider avec données officielles gouvernement [13 pts]
```
👤 En tant que [Économiste/Think Tank]
🎯 Je veux croiser sentiment + données officielles INSEE (chômage, inflation, salaires)
💎 Afin de valider hypothèses avec "source de vérité" gouvernement

Valeur utilisateur:
✅ Justifie mes analyses avec stats officielles
✅ Crédibilité: "Ce n'est pas mon opinion, c'est INSEE"
✅ Détecte décalages (sentiment ≠ réalité stats)

Exemple concret:
"Sentiment chômage = très négatif (-80%) 
 MAIS INSEE dit chômage à 7.2% (baisse 0.3%)
 → Insight: Français pessimistes malgré amélioration réelle"

Critères de succès:
- Vois chiffres INSEE (chômage, inflation, PIB) dans dashboard
- Mis à jour automatiquement (mensuel)
- Peux comparer sentiment vs réalité (graphique dual axis)
```

#### US 1.4: Suivre sondages en temps réel [8 pts]
```
👤 En tant que [Sondeur/Chercheur en sciences politiques]
🎯 Je veux capturer sondages IFOP/TNS/Sofres automatiquement
💎 Afin de ne pas me caler sur des vieilles données (j'ai toujours les derniers sondages)

Valeur utilisateur:
✅ Toujours à jour (pas de sondage "oublié")
✅ Détecte quand sondages changent significativement
✅ Historique complet pour analyses tendances

Critères de succès:
- Vois derniers sondages IFOP/TNS dans dashboard
- Alerté si sondage bouge > 3%
- Peux comparer 2 sondages côte à côte
```

#### US 1.5: Importer mes propres données historiques [5 pts]
```
👤 En tant que [Chercheur]
🎯 Je veux uploader mes datasets personnels (CSV historique 2020-2025)
💎 Afin de créer une baseline et analyser évolution long-terme

Valeur utilisateur:
✅ Utilise données passées pour comparer
✅ Une import simple (pas besoin dev)
✅ Données historiques + nouvelles intégrées

Critères de succès:
- Glisse-dépose un CSV/Excel → intégré
- Je vois "3000 articles historiques importés" confirmation
- Peux interroger données mélangées (historique + nouveau)
```

**Epic 1 Bénéfice Global**: 🎯 **Une source unique de vérité** (presse + événements + stats + sondages) = **Économise 5h/semaine de recherche manuelle**

**Epic 1 Total**: 39 pts | **Sprint Mapping**: Sprint 1-2

---

---

### **EPIC 2: Qualité & Nettoyage**
*Bénéfice utilisateur: Faire confiance aux données (pas de doublons, pas de poubelle, scoring transparent)*

#### US 2.1: Voir qualité chaque article (scoring transparent) [5 pts]
```
👤 En tant que [Analyste/Data scientist]
🎯 Je veux une note qualité 0-10 sur chaque article (comme Note Rotten Tomatoes)
💎 Afin de savoir IMMÉDIATEMENT si je peux faire confiance à cet article

Valeur utilisateur:
✅ Rapidement = "qualité 2/10? Je l'ignore"
✅ Comprends POURQUOI (scoré sur: longueur, complétude, source fiable)
✅ Filtre articles de confiance (j'accepte >= 5/10)

Exemple concret:
Article 1: "Politique ⭐⭐⭐⭐⭐ (5/5) - Source: Le Monde, 800 mots, complet"
Article 2: "Politique ⭐☆☆☆☆ (1/5) - Source inconnue, 50 mots, vide"

Critères de succès:
- Chaque article a couleur (🟢 bon, 🟡 moyen, 🔴 mauvais)
- Je vois le breakdown (source reliability +50%, longueur +30%, etc.)
- Peux exporter "articles >= 7/10" pour analyses
```

#### US 2.2: Éliminer automatiquement les doublons [8 pts]
```
👤 En tant que [Utilisateur]
🎯 Je veux voir chaque article UNE FOIS (pas 5x le même)
💎 Afin de ne pas perdre du temps sur des doublons

Valeur utilisateur:
✅ Efficacité: 100 articles uniques vs 150 avec doublons
✅ Confiance: "Si j'ai 100, j'analyse 100, pas 60 réels"
✅ Transparence: Je vois combien supprimés (audit)

Exemple concret:
❌ Sans dedup: "Macron élection" → vois 5x même article (Monde, France3, LCI, etc.)
✅ Avec dedup: Vois 1x + notation "5 sources rapportent" = plus fort signal

Critères de succès:
- Détecte même article partagé sur 10 sources
- Marque duplicatas sans les supprimer (je peux revenir)
- Dashboard: "100 articles → 8 doublons supprimés → 92 uniques"
```

#### US 2.3: Texte lisible (sans caractères bizarres) [5 pts]
```
👤 En tant que [Utilisateur]
🎯 Je veux articles propres (pas d'HTML, accents français corrects, sans caractères cassés)
💎 Afin de pouvoir les lire sans décoder

Valeur utilisateur:
✅ Articles prêts à lire (pas de post-traitement)
✅ Sentiment analysis marche mieux (pas confuse par caractères cassés)
✅ Export PDF/Excel impeccable

Critères de succès:
- Aucun HTML tag visible
- Caractères français (é, è, ê, ç, œ) corrects
- Pas de caractères de contrôle (©, ®, avec emojis cassés)
```

#### US 2.4: Alerte si données suspectes [13 pts]
```
👤 En tant que [SRE/Data Engineer]
🎯 Je veux être alerté si articles bizarres arrivent (vides, futurs, URL cassée)
💎 Afin d'intercepter les problèmes AVANT qu'ils polluent mon analyse

Valeur utilisateur:
✅ Confiance: Je sais qu'il y a un système de garde-fou
✅ Réactivité: Alerté en 5 min si source panne
✅ Audit: Vois exactement ce qui a été rejeté + pourquoi

Alertes concrètes:
🚨 "100 articles texte vide de Reuters → CHECK SOURCE PARSING"
🚨 "50 articles datés 2099 → CHECK DATE EXTRACTION"
🚨 "URL cassée sur 30% LE MONDE → CHECK FEED"

Critères de succès:
- Alerté immédiatement si > 10% anomalies
- Peux voir "pourquoi article rejeté" (dropdown)
- SLA: Alerte dans inbox dans 5 min
```

#### US 2.5: Audit trail (traçabilité décision filtrage) [8 pts]
```
👤 En tant que [Responsable conformité/Avocat]
🎯 Je veux LOG IMMUABLE de chaque article (avant/après nettoyage)
💎 Afin de prouver légalement "on a pas supprimé articles pour des raisons politiques"

Valeur utilisateur:
✅ Légal: "Regardez, voici la règle appliquée, pas de discrimination"
✅ Audit: "Le 15 déc, article X supprimé car longueur < 50 car (règle objective)"
✅ Transparence: Clients peuvent vérifier "pas de censure"

Critères de succès:
- Chaque action loggée: [timestamp, article_id, action, raison]
- Export rapport: "100 articles nettoyés le 15/12 - règles appliquées"
- Impossible modifier logs (immutable)
```

**Epic 2 Bénéfice Global**: 🎯 **Données que je peux utiliser** (nettoyées, sans doublons, tracées légalement) = **Confiance +80% dans analyses**

**Epic 2 Total**: 39 pts | **Sprint Mapping**: Sprint 2-3

---

---

### **EPIC 3: Intelligence de Sentiment**
*Bénéfice utilisateur: Comprendre ce que les Français pensent VRAIMENT (pas juste compter articles)*

#### US 3.1: Voir sentiment positif/négatif/neutre [13 pts]
```
👤 En tant que [Décideur politique/Investisseur]
🎯 Je veux savoir en 10 sec: Les Français sont-ils contents? Fâchés? Indifférents?
💎 Afin de prendre décisions rapides sans lire 10 000 articles

Valeur utilisateur:
✅ Rapidité: Un graphique = sentiment du pays entier
✅ Contexte: "Sentiment économie = -75%" → Je dois agir
✅ Historique: Vois tendance (improving? worsening?)

Exemple concret:
Dashboard principal:
📊 SENTIMENT GLOBAL FRANCE
🟢 Positif: 25% (montré en vert)
⚪ Neutre: 45% (gris)
🔴 Négatif: 30% (rouge) ← 📈 en hausse vs hier

Critères de succès:
- Vois sentiment par jour/semaine/mois
- Peux filtrer par topic (sentiment politique, économie, climat)
- Peux comparer 2 dates ("début mars vs fin mars = +15% négatif")
- Accuracy >= 85% (validé manuellement sur 500 articles)
```

#### US 3.2: Classifier articles par 22 topics [13 pts]
```
👤 En tant que [Analyste thématique/PDG]
🎯 Je veux savoir: "Quels SUJETS les Français discutent le plus?"
💎 Afin de prioritizer où action (l'inflation monopolise ou le climat?)

Valeur utilisateur:
✅ Focus: "Climat 60% discussions = ma priorité #1"
✅ Émergence: Détecte nouveaux sujets (avant qu'ils explosent)
✅ Allocation ressources: "Économie monte → renforce équipe éco"

Sujets tracés:
1. Politique/Élections 2. Économie/Finance 3. Emploi 4. Climat 5. Santé
6. Éducation 7. Transport 8. Culture 9. Sport 10. Immigration 11. Europe
12. Technologie 13. Énergie 14. Agriculture 15. Justice 16. Défense
17. Logement 18. Tourisme 19. Environnement 20. Régional 21. Autres

Exemple concret:
Top Topics 📊:
1️⃣ Économie (2500 articles, +15% sentim negatif) 📈 ALERT
2️⃣ Politique (2000 articles, neutre)
3️⃣ Climat (1500 articles, +5% positif) ← Niche moins visible

Critères de succès:
- Chaque article taggé avec 1-3 topics (article peut être "Éco + Finance")
- Accuracy >= 80% par topic (cross-validé)
- Vois trends: "Climat montait lentement, explosion hier"
```

#### US 3.3: Extraire noms/organisations clés [8 pts]
```
👤 En tant que [Journaliste/Analyste politique]
🎯 Je veux savoir: "Qui parle de moi?" et "Qui est critiqué?"
💎 Afin de monitorer réputation + détecter crises relationnelles

Valeur utilisateur:
✅ Reputation: "Macron mentionné 5000x, sentiment -60%"
✅ Competitive: "Competitor X en hausse sur ce topic"
✅ Crise detection: Article mention "Macron + scandale" explode

Exemple concret:
TOP PERSONNALITÉS MENTIONNÉES:
1. Emmanuel Macron (5000 mentions, -60% sentiment)
2. Jean-Luc Mélenchon (2000 mentions, -40% sentiment)
3. Marine Le Pen (1800 mentions, +20% sentiment)

TOP ORGANISATIONS:
1. Gouvernement (6000 mentions, -70% sentiment)
2. Assemblée Nationale (2000 mentions, -40%)
3. Total Energies (800 mentions, -50% [pollution])

Critères de succès:
- Detecte noms français (pas "John Smith")
- Groupe variations ("Macron" = "Emmanuel Macron" = "E. Macron")
- Accuracy >= 90% (FlauBERT)
```

#### US 3.4: Confidence level (savoir quand ne pas faire confiance) [5 pts]
```
👤 En tant que [Decision maker prudent]
🎯 Je veux voir si IA est sûre de sa prédiction (pas juste "positif/négatif")
💎 Afin de décider: "Use this insight" vs "Wait for more data"

Valeur utilisateur:
✅ Risk mitigation: "sentiment 80% confidence? Je décide / 40% confidence? J'attends"
✅ Context: "Article ambigu?" → Je lis original
✅ Trust: "IA says 99% confident + positif" = Peux décider vite

Exemple concret:
Article sentiment result:
Sentiment: POSITIF 🟢
Confidence: 95% ← Je peux décider vite
Breakdown: "Texte très positif (vocabulaire clair)"

vs.

Sentiment: POSITIF 🟢
Confidence: 52% ⚠️ ← Je dois lire original
Breakdown: "Texte ambigu (sarcasme? Ironique?)"

Critères de succès:
- Confiance 0-100% sur chaque prédiction
- Peux filtrer "show only >= 80% confidence"
- Explique pourquoi confiance basse
```

**Epic 3 Bénéfice Global**: 🎯 **Comprendre l'opinion réelle des Français** (vs juste compter articles) = **Décisions basées sur faits, pas intuition**

**Epic 3 Total**: 39 pts | **Sprint Mapping**: Sprint 3-4

---

### **EPIC 4: Dashboards & Visualisation**
*Bénéfice utilisateur: Voir l'essentiel en 30 secondes (pas besoin Excel/SQL)*

#### US 4.1: One-page executive summary (pour mon PDG) [8 pts]
```
👤 En tant que [PDG/Décideur C-level]
🎯 Je veux 1 page avec 5 KPIs clés (pas plus, pas moins)
💎 Afin de briefer en 5 min (pas 30 min avec slides)

Valeur utilisateur:
✅ Rapidité: "Sentiment ↓ 15%, 3 topics en crise, 50 articles/jour"
✅ Contexte: Vois tout en glance (pas descendre dans détails)
✅ Décision: Basé sur ce brief, je décide "crisis management activated?"

Les 5 KPIs clés:
1. Overall sentiment (%) + trend (↑/↓) + couleur
2. Top 3 topics trending (avec volume + sentiment)
3. Articles/jour (vs yesterday)
4. Source reliability score (overall 0-100)
5. Anomalies flagged (red alerts)

Exemple concret:
[DATASENS EXECUTIVE BRIEF]
Overall Sentiment: 35% Positive ↓ (was 40% yesterday)
Top Topics: Économie (60% mentions, -80% sentiment) 🔴 ALERT
          Politique (30% mentions, neutral)
          Emploi (20% mentions, +10% sentiment)
Volume: 2,500 articles today (vs 2,200 yesterday)
Alerts: 12 anomalies detected
[BUTTON: Deep Dive] [BUTTON: Export PDF]

Critères de succès:
- Load < 3 sec
- Update every 15 min (automatic)
- Peux exporter PDF signature-ready (brief client)
- Mobile friendly (lire sur phone)
```

#### US 4.2: Sentiment over time (voir la courbe) [5 pts]
```
👤 En tant que [Analyste]
🎯 Je veux graphique: sentiment en courbe depuis 1 an
💎 Afin de voir patterns (montée/baisse, cycles, events)

Valeur utilisateur:
✅ Tendance: "Sentiment was stable, explosion en déc"
✅ Causation: "Vois crises annotées (élections, attentats)"
✅ Projection: "Trend down → Prepare for -20% next month"

Exemple concret:
[LINE CHART]
Y-axis: % sentiment positif
X-axis: Date (2024 → 2025)
Line: Courbe rouge (baisse 60% → 35% en 3 mois)
Events annotated: "Élection mars" "Crise juillet" "Récession déc"
Selector: Monthly/Weekly/Daily granularity

Critères de succès:
- Zoom/pan interactive (Plotly)
- Breakdown: sentiment par topic (toggle)
- Export: Download CSV "sentiment_history.csv"
```

#### US 4.3: Compare 10 sources (matrice) [5 pts]
```
👤 En tant que [Chercheur en médias]
🎯 Je veux tableau: chaque source vs tous les autres
💎 Afin d'identifier biases médias (qui exagère? qui cache?)

Valeur utilisateur:
✅ Bias detection: "France3 + 40% négatif vs Monde -10%"
✅ Source selection: "Source X trop biaisée → l'ignorer"
✅ Credibility ranking: Classement sources par fiabilité

Exemple concret:
[MATRIX TABLE]
              Volume  Avg Sentiment  Reliability  Top Topics
Reuters       1200    +20%           ⭐⭐⭐⭐⭐     Politics, Economy
Le Monde      1500    -10%           ⭐⭐⭐⭐⭐     Politics
France3       800     -40%           ⭐⭐⭐⭐      Politics, Econ
...           ...     ...            ...          ...

Heatmap colors: Green = positive, Red = negative

Critères de succès:
- Peux trier (volume, sentiment, reliability)
- Peux filtrer par topic
- Hover = voir breakdown (why -40%?)
```

#### US 4.4: Geographic heatmap (sentiment par région) [13 pts]
```
👤 En tant que [Gouverneur/Maire]
🎯 Je veux voir sentiment par région/ville sur une carte
💎 Afin d'adapter politiques localement ("Nord en crise? Investir là")

Valeur utilisateur:
✅ Localization: "Sentiment Île-de-France -70% vs Provence +10%"
✅ Response: "Sais où agir prioritaire (région en crise)"
✅ Equity: "Fair distribution aide par region (pas juste Paris)"

Exemple concret:
[MAP FRANCE]
Colors: 🔴 Rouge = très négatif (-80%)
        🟡 Orange = négatif (-30%)
        ⚪ Gris = neutre
        🟢 Vert = positif (+20%)

Click region → Zoom
See: Sentiment heatmap + top articles pour cette région

Critères de succès:
- Gps tagging articles (NER pour lieux)
- Drill-down: France → Région → Département → Ville
- Tooltip: "Île-de-France: 2500 articles, -60% sentiment"
- Mobile: Pinch to zoom
```

#### US 4.5: Trending topics (ce qui monte/descend) [8 pts]
```
👤 En tant que [Journaliste/Trend spotter]
🎯 Je veux savoir: "Quels topics explosent? Lesquels meurent?"
💎 Afin d'être premier rapporter la nouvelle (scoop!)

Valeur utilisateur:
✅ Early warning: "Climat monte 200% → Écris article avant la presse"
✅ Counter-trends: "Politique descend = Perte intérêt"
✅ Credibility: "Je vois trend avant TF1 → Je décide si cover"

Exemple concret:
[TRENDING WIDGET]
📈 RISING (cette semaine):
1. AI/Technologie +300% (articles/semaine: 50 → 200)
2. Électricité +150% (articles/semaine: 30 → 75) ⚡
3. Retraite +80% (articles/semaine: 100 → 180)

➡️ STABLE:
1. Sport (30 articles/semaine, steady)

📉 DECLINING:
1. Football -50% (articles/semaine: 100 → 50)
2. Cinéma -40% (articles/semaine: 40 → 24)

Critères de succès:
- Update daily
- Sparkline trend (visual 7-day history)
- Color sentiment (article montant = vert si positif)
- Peux click → voir articles driving trend
```

**Epic 4 Bénéfice Global**: 🎯 **Décisions faciles** (dashboards font le boulot, pas Excel/SQL) = **Leadership agile**

**Epic 4 Total**: 39 pts | **Sprint Mapping**: Sprint 4-5

---

---

### **EPIC 5: API & Intégration**
*Bénéfice utilisateur: Intégrer DATASENS dans mon appli/système (je ne suis pas obligé d'utiliser ton interface)*

#### US 5.1: Query API (chercherait articles façon Google) [8 pts]
```
👤 En tant que [Développeur tiers/Startup]
🎯 Je veux API simple: "Donne-moi articles (sentiment + topic + date)"
💎 Afin d'intégrer DATASENS dans mon appli

Valeur utilisateur:
✅ Flexibilité: Pas obligé utiliser ton interface
✅ Speed: Répond en < 2 sec
✅ Power: Peux combiner filtres (économie + négatif + décembre)

Exemple concret:
```
GET /api/v1/articles?
  topic=économie
  sentiment=negative
  date_from=2025-12-01
  limit=50
  
Response: JSON
[
  {
    "id": "1",
    "title": "Inflation ...",
    "sentiment": "negative",
    "confidence": 0.95,
    "topics": ["économie", "finance"],
    "url": "...",
    "published_at": "2025-12-15"
  },
  ...
]
```

Critères de succès:
- Répond < 2 sec (même 10,000 articles)
- Filtres: query_text, topic, sentiment, date_range, source
- Pagination: limit + offset
- Rate limit: 100 req/min (fair pour tous)
- Errors: clairs (400 = bad query, 403 = rate limit, etc.)
```

#### US 5.2: Export datasets (télécharger raw data) [5 pts]
```
👤 En tant que [Data scientist]
🎯 Je veux télécharger 100k articles en Parquet/CSV
💎 Afin d'analyser localement dans mon Python/R

Valeur utilisateur:
✅ Parquet: 10x plus rapide + compact que CSV
✅ Batch job: Démarrage automatique (pas attendant)
✅ Monitoring: Je vois % téléchargement

Exemple concret:
```
POST /api/v1/export
{
  "format": "parquet",
  "filters": {
    "date_from": "2025-12-01",
    "topic": "économie"
  }
}

Response:
{
  "job_id": "export_abc123",
  "status": "queued",
  "download_url": "/download/abc123",
  "progress": 0
}

[2 min later...]
GET /api/v1/export/abc123
→ status: "ready"
→ download_url: "https://datasens.com/files/export_abc123.parquet" (direct S3)
```

Critères de succès:
- Formats: Parquet (défaut), CSV, JSON
- Compression: Auto gzip
- Job async (tu peux fermer browser, job continue)
- Email notif: "Your export is ready" + lien
```

#### US 5.3: Real-time alerts (webhooks) [8 pts]
```
👤 En tant que [Decision maker]
🎯 Je veux être notifié immédiatement quand sentiment crash (ou topic explose)
💎 Afin de réagir vite (pas attendre dashboard update)

Valeur utilisateur:
✅ Real-time: Notification en < 30 sec
✅ Actionable: "Sentiment économie ↓ 40%" + lien article
✅ Silence: Filter alerts (pas veux 100/jour)

Exemple concret:
```
POST /api/v1/webhooks/subscribe
{
  "event": "sentiment_shift",
  "topic": "économie",
  "threshold": 0.2,  // 20% change
  "webhook_url": "https://my-app.com/datasens-alerts",
  "frequency": "realtime"
}

Quand ça arrive:
POST https://my-app.com/datasens-alerts
{
  "event": "sentiment_shift",
  "message": "Sentiment économie dropped 25% (was 60%, now 35%)",
  "articles_count": 120,
  "top_article": {
    "title": "Récession...",
    "sentiment": "negative"
  }
}
```

Critères de succès:
- Events: sentiment_shift, topic_trending, anomaly_detected
- Retry logic: 3x exponential backoff (webhook fail? Réessaye)
- Security: HMAC-SHA256 signature (tu vérifies pas fake)
- Manageable: Dashboard pour activer/désactiver alerts
```

#### US 5.4: GraphQL (queries ultra-flexibles) [13 pts]
```
👤 En tant que [Advanced user/ML engineer]
🎯 Je veux requête GraphQL (ultra-flexible, prends exactement ce que je veux)
💎 Afin de réduire bande passante (pas télécharger colonnes inutiles)

Valeur utilisateur:
✅ Flexible: Prends titres + sentiments vs tout champs
✅ Nested: Query articles + sources + metrics en 1 appel
✅ Graphiql: Playground web = auto-discovery API

Exemple concret:
```
query {
  articles(
    where: {
      sentiment: "negative"
      topic: "économie"
      date_from: "2025-12-01"
    }
    first: 10
  ) {
    id
    title
    sentiment {
      label
      confidence
    }
    topics {
      name
    }
    source {
      name
      reliability
    }
  }
}
```

Critères de succès:
- Full schema: query (read) + mutations (write) optionnels
- Playground: https://api.datasens.com/graphql (GraphiQL)
- Subscriptions: Real-time queries (optional)
- Introspection: Auto-generated docs
```

#### US 5.5: SDK Python (import datasens, utiliser) [5 pts]
```
👤 En tant que [Python developer]
🎯 Je veux `pip install datasens` + utiliser nativement
💎 Afin d'intégrer DATASENS sans coder REST calls

Valeur utilisateur:
✅ Simple: `from datasens import Client`
✅ Type hints: IDE autocomplete fonctionne
✅ Async: Peux utiliser asyncio pour parallélisation

Exemple concret:
```python
from datasens import Client

client = Client(api_key="xxx")

# Simple query
articles = client.articles.filter(
    sentiment="positive",
    topic="politique",
    limit=100
)

# Export
job = client.export.create(
    format="parquet",
    filters={"date_from": "2025-12-01"}
)
job.wait()  # Attend résultat
articles_df = pd.read_parquet(job.download())

# Real-time alerts
client.webhooks.subscribe(
    event="sentiment_shift",
    topic="économie",
    callback=lambda alert: print(f"Alert: {alert}")
)
```

Critères de succès:
- PyPI package: `pip install datasens-sdk`
- Type hints + docstrings (IDE help)
- Async/await support
- Docs + examples (GitHub)
```

**Epic 5 Bénéfice Global**: 🎯 **Intégrer DATASENS partout** (ton app, mon app, startup app) = **Effet réseau**

**Epic 5 Total**: 39 pts | **Sprint Mapping**: Sprint 5-6

---

### **EPIC 6: Monitoring & Observabilité**

#### US 6.1: Ingestion Health Checks [5 pts]
```
En tant que [SRE]
Je veux alertes quand source échoue
Afin de détecter outages

Critères d'acceptation:
- [ ] Health check chaque source (5 min)
- [ ] Log: status, latency, error_rate
- [ ] Alert si > 3 failures consécutifs
- [ ] Slack/Email notifications

Tasks:
- [ ] Build health checker
- [ ] Implement exponential backoff
- [ ] Add alerting rules
- [ ] Dashboard health status
```

#### US 6.2: Database Monitoring [8 pts]
```
En tant que [Database admin]
Je veux voir perf DB (CPU, RAM, queries lentes)
Afin d'optimiser

Critères d'acceptation:
- [ ] Slowlog queries (> 1sec)
- [ ] Index usage analysis
- [ ] Table sizes
- [ ] Replication lag (if cluster)

Tasks:
- [ ] Setup Prometheus exporters
- [ ] Query performance dashboard
- [ ] Implement auto-indexing
- [ ] Baseline + alerting
```

#### US 6.3: API Metrics & SLA [8 pts]
```
Latency: p50 < 100ms, p99 < 1sec
Availability: 99.9% uptime
Error rate: < 0.1%

Critères d'acceptation:
- [ ] Metrics: requests, latency (histogram), errors
- [ ] Tracing (Jaeger/Zipkin)
- [ ] SLA dashboard
- [ ] Incidents tracking

Tasks:
- [ ] Setup Prometheus
- [ ] Add OpenTelemetry
- [ ] Build Grafana dashboards
- [ ] Alert rules (PagerDuty)
```

#### US 6.4: Data Quality Monitoring [13 pts]
```
En tant que [Data Engineer]
Je veux tableau de bord qualité données
Afin d'identifier data drift

Métrics:
- Quality score distribution
- Duplicate rate
- Null rate
- Anomaly rate

Critères d'acceptation:
- [ ] Data profiling (hourly)
- [ ] Anomaly detection (Isolation Forest)
- [ ] Data drift alerts (Kolmogorov-Smirnov test)
- [ ] Data quality score trend

Tasks:
- [ ] Implement data profiler
- [ ] Setup monitoring pipeline
- [ ] Create profiling dashboard
- [ ] Configure drift detection
```

---

### **EPIC 6: Monitoring & Observabilité**
*Bénéfice utilisateur: Dormir tranquille (système fonctionne sans te surveiller 24/7)*

#### US 6.1: Alertes sources cassées [5 pts]
```
👤 En tant que [SRE/Ops]
🎯 Je veux Slack/Email si une source panne (pas articles depuis 2h?)
💎 Afin de réagir AVANT que mes données soient polluées

Valeur utilisateur:
✅ Proactivity: "Reuters RSS down depuis 2h" → Je fixe maintenant
✅ Quiet: Pas alerte tous les jours (juste vrais problèmes)
✅ Visible: Vois statut chaque source en dashboard

Exemple concret:
[SLACK MESSAGE]
🚨 ALERT: Reuters RSS Feed
Status: DOWN (last success: 2 hours ago)
Error: Connection timeout
Action: Check feed URL / Contact Reuters
[Button: Acknowledge] [Button: Mute 1h]

Dashboard:
Source          Status  Last Check  Articles Today  
Reuters         ⛔ DOWN  2h ago      0 (expect 50)
Le Monde        ✅ OK   1min ago    48
France3         ✅ OK   3min ago    35

Critères de succès:
- Check each source every 5 min
- Alert si > 2 failures consécutifs
- Mute capability (snooze 1h si false alarm)
- Email + Slack
```

#### US 6.2: Dashboard "Is DATASENS working?" [8 pts]
```
👤 En tant que [Utilisateur/PDG]
🎯 Je veux page: "Is DATASENS healthy right now? YES or NO?"
💎 Afin de savoir si je peux faire confiance aux données

Valeur utilisateur:
✅ Trust: "Dashboard dit 🟢 = données fraîches"
✅ Speed: "Dashboard dit 🔴 = j'attends avant décision"
✅ Transparency: Vois breakdown (API ok? DB ok? Sentiment model ok?)

Exemple concret:
[STATUS PAGE]
🟢 DATASENS IS OPERATIONAL

Component Status:
✅ API (latency: 120ms, 100% availability)
✅ Data Ingestion (50 articles/min, no errors)
✅ Quality Pipeline (99.5% success rate)
✅ ML Models (Inference: 25ms/article)
✅ Dashboards (load time: 2.5sec)
✅ Database (CPU: 15%, RAM: 40%)

Last incident: 15 december, 2h downtime
Uptime (30 days): 99.7%

Critères de succès:
- Status page public (https://status.datasens.com)
- Update realtime
- Incident history + postmortems
- Email subscribe (notif changes)
```

#### US 6.3: SLA garanties (ou argent back) [8 pts]
```
👤 En tant que [Client payant]
🎯 Je veux SLA: "99.5% uptime ou remboursement"
💎 Afin de savoir que vous prenez le service au sérieux

Valeur utilisateur:
✅ Confidence: "Payer pour service fiable"
✅ Accountability: "Si down > 5h = remboursement"
✅ Transparent: "Je vois % uptime actualisé"

SLA Tiers:
FREE: Best effort (pas SLA)
PRO: 99% uptime ($99/mo)
ENTERPRISE: 99.9% uptime ($999/mo) + dedicated support

Critères de succès:
- Tracking uptime automated (Pingdom)
- Credit system (down 1% = 10% next bill)
- Published SLA page
- Incident notifications
```

#### US 6.4: Data Quality Dashboard (dérive détectée?) [13 pts]
```
👤 En tant que [Data steward]
🎯 Je veux graphique montrant "données se dégradent-elles?" (data drift)
💎 Afin de détecter quand qualité baisse (adapter pipeline)

Valeur utilisateur:
✅ Early warning: "Quality score moyen ↓ 15% vs semaine passée"
✅ Actionable: "Tableau breakdown = où le problème vient"
✅ Historical: "Voir trend (a dégradé progressivement? ou d'un coup?)"

Exemple concret:
[DATA QUALITY DASHBOARD]

Overall Quality Score: 72/100 ⚠️ (was 85 last week)

Breakdown:
- Duplication Rate: 8% 🔴 (was 2%) → Reuters RSS parsing broken?
- Null Rate: 3% 🟢 (was 3%)
- Average Sentiment Confidence: 87% 🟢 (was 87%)
- Articles/day: 2500 🟡 (was 3200) → Fewer sources?

Timeline (7-day history):
[CHART: Quality score trend]
Dec 9: 85 → Dec 10: 84 → ... → Dec 15: 72 📉

Action items:
- 🔴 HIGH: Check Reuters for parsing changes
- 🟡 MED: Investigate volume drop
- 🟢 LOW: Model performance stable

Critères de succès:
- Profiling runs hourly
- Anomaly detection (Isolation Forest)
- Drift detection (KS test)
- Actionable recommendations
```

**Epic 6 Bénéfice Global**: 🎯 **Proactive ops** (détecte problems avant users) = **Reliability trust**

**Epic 6 Total**: 34 pts | **Sprint Mapping**: Sprint 6-7

---

### **EPIC 7: Fine-tuning IA**
*Bénéfice utilisateur: Modèles sentiments optimisés pour France (pas US models)*

#### US 7.1: Annoter 5000 articles (pour entrainer) [13 pts]
```
👤 En tant que [ML Engineer]
🎯 Je veux 5000 articles annotés (sentiment + topics)
💎 Afin d'avoir données d'entrainement de qualité

Valeur utilisateur:
✅ Quality: Inter-annotator agreement > 85%
✅ Balanced: Pas juste articles positifs (50/30/20)
✅ Documented: Guidelines claires (pas confusion annotateurs)

Workflow concret:
[LABEL STUDIO INTERFACE]

Article: "Macron annonce hausse retraites à 65 ans..."

Questions:
1. Sentiment: [Positive] [Neutral] [Negative] ← J'click "Negative" (73% voters fâchés)
2. Topics: [Select multiple] Politique ☑️, Retraites ☑️, Social ☐
3. Confidence: [1-5 slider] ← 4 (je suis sûr)
4. Notes: [optional] "Sentiment is strong, multiple negatives words"

[Save] [Next Article]

Stats:
Annotated: 3,200/5000 (64%)
Agreement (annotator 1 vs 2): 87% ✅
Remaining: 1,800

Critères de succès:
- 5000 annotations complet
- Sentiment: 3-way balanced (±5%)
- Topics: multi-label, 0-5 topics/article
- Cohen's kappa > 0.80 inter-annotator
```

#### US 7.2: Modèles sentiments (FlauBERT fine-tuned) [13 pts]
```
👤 En tant que [Data scientist]
🎯 Je veux modèle français optimisé (85%+ accuracy)
💎 Afin que sentiment analysis soit fiable

Valeur utilisateur:
✅ Accuracy: 85%+ F1 score (validé sur test set français)
✅ Speed: < 50ms par article (real-time processing)
✅ Explainability: "Why did you say negative?" → show tokens

Résultats modèle:
```
FlauBERT Fine-tuned Sentiment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Accuracy: 86% (test set)
F1-weighted: 0.84
Precision: 0.85
Recall: 0.83

Breakdown:
Positive: Precision 0.82, Recall 0.80
Neutral: Precision 0.87, Recall 0.85  
Negative: Precision 0.85, Recall 0.84

Latency: 35ms/article (GPU)
Model size: 350 MB

Confusion matrix (test):
            Predicted
            Pos  Neu  Neg
Actual Pos  800   50   50
       Neu   60  850   90
       Neg   40   80  820
```

Critères de succès:
- F1-weighted >= 0.85
- < 50ms inference latency
- No data leakage (test set clean)
- Model card documented (intended use, limitations)
```

#### US 7.3: Topics classification (22 catégories) [13 pts]
```
👤 En tant que [Product manager]
🎯 Je veux articles catégorisés: Économie/Politique/Climat/etc.
💎 Afin de filtrer par topic (utilisateurs intéressés politique uniquement)

Valeur utilisateur:
✅ Granularity: 22 topics (pas trop, pas trop peu)
✅ Multi-label: Article peut être "Éco + Finance + Emploi"
✅ Confidence: "This is Économie 92% confident"

Topics (22):
1. Politique 2. Économie 3. Emploi 4. Climat 5. Santé
6. Éducation 7. Transport 8. Culture 9. Sport 10. Immigration
11. Europe 12. Technologie 13. Énergie 14. Agriculture 15. Justice
16. Défense 17. Logement 18. Tourisme 19. Environnement 20. Finance
21. Régional 22. Divers

Résultats:
```
Topics Classifier (Multi-label)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model: DISTILBERT fine-tuned
F1-weighted: 0.81
Average precision per topic: 0.79
Recall: 0.80

Top Topics (in corpus):
1. Politique (28% articles)
2. Économie (22%)
3. Emploi (15%)
4. Climat (12%)
...

Sample prediction:
Article: "Retraite: nouvelles mesures gouvernement..."
Topics:
- Politique: 0.95 ✅
- Emploi: 0.78 ✅
- Économie: 0.45 (filtered, < 0.5 threshold)
```

Critères de succès:
- F1-weighted >= 0.80
- Per-topic precision >= 0.75
- Macro-recall >= 0.78
- Multi-label support (1-5 topics/article)
```

#### US 7.4: Model versioning (MLflow) [8 pts]
```
👤 En tant que [ML ops]
🎯 Je veux versioner modèles (v1.0, v1.1, v2.0 + track metrics)
💎 Afin de rollback si nouveau modèle pire

Valeur utilisateur:
✅ Reproducibility: Reload v1.0 si v2.0 broken
✅ Comparison: "v1.0 F1=0.84, v2.0 F1=0.86 → use v2"
✅ Audit: "When did we deploy v2? Who approved?"

MLflow Registry:
```
Model: datasens-sentiment
━━━━━━━━━━━━━━━━━━━━━━━━

Version 1.0 (Production)
├─ F1: 0.84
├─ Precision: 0.83
├─ Trained: 2025-11-15
├─ Deployed: 2025-11-20
└─ Status: PROD

Version 2.0 (Staging)
├─ F1: 0.86 (↑ +2%)
├─ Precision: 0.85
├─ Trained: 2025-12-10
├─ Status: STAGED (waiting approval)
└─ QA: "Looks good, data drift detected in Negative class"

Rollback history:
- 2025-12-01: v1.1 → v1.0 (latency issue)
- 2025-11-15: v1.0 released
```

Critères de succès:
- Model registry: track all versions + metrics
- Promotion workflow: DEV → STAGING → PROD
- Rollback capability (1 click)
- Audit trail (who, when, why)
```

#### US 7.5: A/B testing (comparer modèles live) [8 pts]
```
👤 En tant que [Product manager]
🎯 Je veux A/B test: "Model v1 vs v2" sur 10% users
💎 Afin de savoir si v2 vraiment mieux (pas juste test metrics)

Valeur utilisateur:
✅ Confidence: Real user feedback, not just lab
✅ Safety: Gradual rollout (5% → 25% → 100%)
✅ Metrics: Track accuracy, latency, satisfaction

A/B Test Setup:
```
Test: "Sentiment Model v2 vs v1"
Duration: 14 days
Traffic split: 90% v1, 10% v2

Primary metrics:
- Accuracy (vs manual labels): v1=84%, v2=86%
- Latency: v1=35ms, v2=38ms
- User satisfaction (proxy: dashboard opens): v1=92%, v2=94%

Results:
✅ v2 more accurate (+2% F1)
⚠️ v2 slightly slower (+3ms) but acceptable
✅ Users prefer v2 (engagement +2.5%)

Decision: SHIP v2 to 100%

Rollout plan:
Day 1-3: 5% traffic
Day 4-7: 25% traffic
Day 8-14: 100% traffic (monitor SLOs)
```

Critères de succès:
- Feature flags (easy on/off)
- Gradual rollout (5% → 25% → 100%)
- Statistical significance (p < 0.05)
- Auto-rollback if errors > threshold
```

**Epic 7 Bénéfice Global**: 🎯 **Modèles fiables** (fine-tuned français, A/B tested) = **Trust in insights**

**Epic 7 Total**: 55 pts | **Sprint Mapping**: Sprint 7-9

---

### **EPIC 8: Gouvernance & Conformité RGPD**
*Bénéfice utilisateur: Donnée légale & certifiée (auditable par avocats)*

#### US 8.1: Anonymiser données personnelles [13 pts]
```
👤 En tant que [Data privacy officer]
🎯 Je veux noms de personnes anonymisés ("Jean Dupont" → "[PERSON_1]")
💎 Afin de respecter RGPD (droit à oubli) + éviter procès

Valeur utilisateur:
✅ Legal: "Impossible réidentifier personne"
✅ Audit: "Vois rapport anonymisation par date"
✅ Selective: "Je décide quoi anonymiser (noms? emails? adresses?)"

Anonymization rules:
```
Rule 1: Person names → [PERSON_N]
"Emmanuel Macron" → "[PERSON_1]"
"Jean Dupont" → "[PERSON_2]"

Rule 2: Emails → [EMAIL_HASH]
"jean@example.com" → "[EMAIL_8a92f3e]"

Rule 3: Phone numbers → [PHONE]
"06 12 34 56 78" → "[PHONE]"

Rule 4: Addresses → [ADDRESS_CITY]
"123 Rue de la Paix, Paris" → "[ADDRESS_Paris]"

Anonymization Report (Dec 15, 2025):
Articles processed: 2500
Persons anonymized: 1200
Emails anonymized: 150
Addresses anonymized: 30
K-anonymity score: 8 (good - k>=5 required)
```

Critères de succès:
- K-anonymity >= 5 (re-identification impossible)
- < 200ms per 1000 articles
- Audit log: what was anonymized
- Reversible (optional): maintain mapping for authorized users
```

#### US 8.2: Access control par rôle [8 pts]
```
👤 En tant que [Admin]
🎯 Je veux rôles: Admin (tout) / Analyst (lire + export) / Viewer (dashboard only)
💎 Afin de contrôler "qui voit quoi" (pas tout le monde voit clients data)

Valeur utilisateur:
✅ Security: "Stagiaire ne voit pas data confidentiels"
✅ Audit: "Log: qui a lu article X le 15/12 à 10h"
✅ Granular: "Data scientist voit exporté, ne voit pas API keys"

Roles:
```
ADMIN
├─ Lire tout
├─ Créer/modifier sources
├─ Modifier utilisateurs
├─ Voir audit logs
└─ Access credentials

ANALYST
├─ Lire articles
├─ Exporter datasets
├─ Créer dashboards persos
└─ Pas: modify sources, voir audit logs

VIEWER
├─ Lire dashboards publics
├─ Pas: Export, API access
└─ Pas: données sensibles

Row-level security:
- Client X: voit juste articles liés à Client X
- Team Finance: voit juste articles topic "Économie"
```

Critères de succès:
- JWT/OAuth2 authentication
- Role-based access control (RBAC)
- Row-level security (RLS)
- Audit: track qui a accédé quoi quand
```

#### US 8.3: Retention policies (droit à l'oubli) [5 pts]
```
👤 En tant que [Compliance officer]
🎯 Je veux politique: articles bruts 6 mois, données anonymes 2 ans
💎 Afin d'être RGPD conforme (droit à oubli articles people)

Valeur utilisateur:
✅ Legal: "Je prouve respect retention policies"
✅ Automated: "Pas besoin reminder, auto-deletion"
✅ Auditability: "Vois historique suppression"

Retention Policy:
```
Article Type              Retention    Action
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Raw articles             6 months     DELETE
Anonymized articles      2 years      DELETE
Sentiment labels         2 years      KEEP (aggregated)
User logs                1 year       DELETE
Backups                  90 days post deletion PURGE

Example:
Article published: Dec 15, 2024
Stored in raw: Dec 15, 2024 - June 15, 2025
June 15, 2025: Auto-delete (raw)
BUT kept anonymized until Dec 15, 2026
Dec 15, 2026: Auto-delete anonymized version too

Deletion Report (Dec 2025):
Articles deleted: 12,500
Data freed: 45 GB
Compliance: ✅ RGPD
```

Critères de succès:
- Auto-deletion scheduler
- Cascading deletes (referential integrity)
- Audit trail (what was deleted when)
- Restore capability (7 days post-delete from backup)
```

#### US 8.4: Compliance reports (pour les avocats) [8 pts]
```
👤 En tant que [Legal]
🎯 Je veux rapport: "Data inventory + Access logs + Incidents"
💎 Afin de prouver à régulateurs "on respecte les règles"

Valeur utilisateur:
✅ Audit-ready: "Télécharge PDF, envois à CNIL"
✅ Comprehensive: Inventory + logs + incidents
✅ Automatic: Monthly generation

Compliance Report Template:
```
DATASENS COMPLIANCE REPORT — December 2025

1. DATA INVENTORY
━━━━━━━━━━━━━━━━
Name: articles_raw
Data subject: News articles (no personal data after anonymization)
Retention: 6 months
Processors: DATASENS, AWS S3
Safeguards: Encryption at rest, TLS in transit, k-anonymity >= 5
Last audit: 2025-12-10

2. ACCESS LOGS
━━━━━━━━━━━━
Date              User          Action              Data
2025-12-15        john@co.com   Export 100 articles Articles raw (December)
2025-12-14        admin@...     Add user Jane       ...
...

3. INCIDENTS
━━━━━━━━━━
Dec 1: Database misconfiguration (1h, no data exposed)
Nov 15: API timeout (2h, no data exposure)

4. DPIA (Data Protection Impact Assessment)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Risk: Sentiment analysis could be discriminatory
Mitigation: Bias audits quarterly, fairness metrics tracked
Status: ✅ APPROVED by DPO

[Signature]: ________________  Date: 2025-12-15
```

Critères de succès:
- Monthly auto-generation
- Signature-ready PDF
- Customizable sections
- Archive (2 years retention)
- Multi-language (French, English)
```

**Epic 8 Bénéfice Global**: 🎯 **Légalement protégé** (RGPD compliant, auditable) = **No regulator fines**

**Epic 8 Total**: 34 pts | **Sprint Mapping**: Sprint 9-10

---

## 📊 Backlog Prioritisé

### Par Impact (High → Low)

| Rang | Epic | Story Points | Priority | Rationale |
|------|------|--------------|----------|-----------|
| 1 | EPIC 1: Collecte | 39 | 🔴 MUST | MVP: sans data, rien ne marche |
| 2 | EPIC 2: Qualité | 39 | 🔴 MUST | Sans qualité, IA inutile |
| 3 | EPIC 3: Sentiment | 39 | 🔴 MUST | Valeur core du produit |
| 4 | EPIC 4: Dashboards | 39 | 🟠 SHOULD | User-facing, adoption |
| 5 | EPIC 5: API | 39 | 🟠 SHOULD | Extensibility, 3rd-party |
| 6 | EPIC 7: Fine-tune IA | 55 | 🟡 COULD | Accuracy, Phase 06 |
| 7 | EPIC 6: Monitoring | 39 | 🟡 COULD | Production readiness |
| 8 | EPIC 8: Conformité | 34 | 🟡 COULD | Compliance, legal |

**Total Story Points**: 324 pts  
**Estimated Duration** (1 dev, 20 pts/sprint): **16 sprints = 4 mois**

---

## 🏃 Sprint Planning (16 sprints)

### Sprint 1 (Semaine 1-2): Data Foundations
**Pts**: 20 | **Goal**: Basic ingestion running

- [ ] US 1.1: RSS Feeds (5 pts)
- [ ] US 1.2: GDELT API (8 pts) 
- [ ] US 1.3: INSEE Data (5 pts)
- [ ] Setup: Git + CI/CD + Docker
- **Deliverable**: 150+ articles/jour ingérés ✅

### Sprint 2 (Semaine 3-4): Quality & Cleaning
**Pts**: 20 | **Goal**: Clean dataset pipeline

- [ ] US 2.1: Quality Score (5 pts)
- [ ] US 2.2: Deduplication (8 pts)
- [ ] US 2.3: Text Normalization (5 pts)
- [ ] Integrate with Sprint 1 data
- **Deliverable**: 80%+ clean articles ✅

### Sprint 3 (Semaine 5-6): Sentiment Analysis
**Pts**: 20 | **Goal**: Sentiment labels + confidence

- [ ] US 3.1: Sentiment (13 pts)
- [ ] Setup: FlauBERT + GPU
- [ ] Test: 85%+ accuracy
- [ ] Integration: PIPELINE
- **Deliverable**: Every article has sentiment label ✅

### Sprint 4 (Semaine 7-8): Dashboard MVP
**Pts**: 20 | **Goal**: First visualizations

- [ ] US 4.1: Executive Summary (8 pts)
- [ ] US 4.2: Sentiment Timeline (5 pts)
- [ ] US 4.3: Source Comparison (5 pts)
- [ ] Setup: Streamlit + Plotly
- **Deliverable**: 3 working dashboards ✅

### Sprint 5 (Semaine 9-10): Expanded Dashboards
**Pts**: 20 | **Goal**: Full visualization suite

- [ ] US 4.4: Geographic Heatmap (13 pts)
- [ ] US 4.5: Topic Trending (5 pts)
- [ ] Performance optimization
- [ ] Mobile responsiveness
- **Deliverable**: 5 dashboards, production-ready ✅

### Sprint 6 (Semaine 11-12): API Core
**Pts**: 20 | **Goal**: REST API + GraphQL basics

- [ ] US 5.1: REST Query API (8 pts)
- [ ] US 5.2: Export API (5 pts)
- [ ] Setup: FastAPI + OpenAPI docs
- [ ] Rate limiting + auth
- **Deliverable**: API endpoints tested + documented ✅

### Sprint 7 (Semaine 13-14): API Advanced
**Pts**: 20 | **Goal**: Webhooks + GraphQL

- [ ] US 5.3: Webhooks (8 pts)
- [ ] US 5.4: GraphQL (13 pts) **[DEFER IF TIME]**
- [ ] SDK: Python package (5 pts)
- **Deliverable**: API feature-complete ✅

### Sprint 8 (Semaine 15-16): Monitoring
**Pts**: 20 | **Goal**: Production observability

- [ ] US 6.1: Ingestion Health (5 pts)
- [ ] US 6.2: DB Monitoring (8 pts)
- [ ] US 6.3: API Metrics (5 pts)
- [ ] Setup: Prometheus + Grafana
- **Deliverable**: Full monitoring stack ✅

### Sprint 9 (Semaine 17-18): ML Training Prep
**Pts**: 20 | **Goal**: Annotated training data

- [ ] US 7.1: Data Annotation (13 pts)
- [ ] US 7.2: FlauBERT Fine-tune setup (5 pts) **[PARTIAL]**
- [ ] Setup: Label Studio + Prodigy
- [ ] Recruit annotators
- **Deliverable**: 5000+ annotated articles ✅

### Sprint 10 (Semaine 19-20): ML Training
**Pts**: 20 | **Goal**: Improved ML models

- [ ] US 7.2: FlauBERT Fine-tuning (13 pts)
- [ ] US 7.3: Topic Classification (13 pts) **[PARTIAL]**
- [ ] Evaluation: F1 >= 0.85
- **Deliverable**: Production models trained ✅

### Sprints 11-16: Compliance + Optimization
**Pts**: 54 | **Goal**: Production-ready system

- Compliance (EPIC 8): 34 pts
- Data Quality Monitoring (EPIC 6): 20 pts
- A/B Testing + MLOps (EPIC 7): 13 pts
- Performance tuning + documentation

---

## 🎯 Taiga Configuration

```
Projet: DATASENS
├─ 8 Epics
├─ 43 User Stories
├─ 324 story points
├─ 16 sprints (2 weeks each)
└─ 1 dev team

Kanban columns:
- Backlog
- Ready for Sprint
- In Progress
- Testing
- Done (Definition: Tested + Documented)

DoD (Definition of Done):
✅ Code reviewed + merged
✅ Unit tests >= 80% coverage
✅ Integration tests pass
✅ Documentation written
✅ Tested in staging env
✅ No SonarQube issues (A grade)
✅ Approved by PO
```

---

## 🎯 Miro Board Structure

```
Miro Board: DATASENS Roadmap

Sections (Left → Right):
1. VISION (Personas + Value Props)
2. 8 EPICS (Color-coded, sticky notes)
3. USER STORIES (Each epic's stories)
4. SPRINT PLANNING (Current + next sprint)
5. RISKS & DEPENDENCIES (Red flags)
6. PARKING LOT (Nice-to-have features)

Colors:
🔴 RED = Epic 1 (Collecte)
🟠 ORANGE = Epic 2 (Qualité)
🟡 YELLOW = Epic 3-4 (Intelligence + Dashboards)
🟢 GREEN = Epic 5-6 (API + Monitoring)
🔵 BLUE = Epic 7-8 (ML + Compliance)

Each story card:
- User persona
- Acceptance criteria
- Story points
- Epic link
- Dependencies
```

---

## 🎯 Trello Board Structure

```
Trello Board: DATASENS Sprint Board

Lists (Left → Right):
1. BACKLOG (All 43 stories, sorted by priority)
2. SPRINT [N] (Current sprint = 20 pts target)
3. IN PROGRESS (WIP limit = 3)
4. TESTING (QA checklist)
5. DONE (✅ Definition of Done met)

Card format:
Title: [EPIC] User Story Name
Description:
- User story text
- Acceptance criteria (checklist)
- Story points
- Assignee
- Due date

Labels:
- Epic1 (Red), Epic2 (Orange), ...
- Priority (High/Med/Low)
- Size (Small/Medium/Large)
- Status (Ready/WIP/Blocked)
```

---

## 📋 Key Metrics

### Velocity Tracking
```
Sprint | Points | Completed | Velocity | Trend
1      | 20     | 20        | 20       | ─
2      | 20     | 18        | 18       | ↓
3      | 20     | 20        | 20       | ↑
4      | 20     | 22        | 22       | ↑ (team ramping)
```

### Value Delivered (per sprint)
```
Sprint | MVP Feature | User Value | Business Impact
1      | Ingestion   | 10x articles/day | Data foundation
2      | Quality     | 80% clean | Reliable IA input
3      | Sentiment   | Actual labels | Core product
4      | Dashboard   | Visuals | Executive adoption
```

---

## 🚩 Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| RSS feeds go down | Ingestion breaks | Medium | Fallback mocks + retry logic |
| GDELT API limits | Data loss | Low | Cache + offline mode |
| Annotation quality low | ML models poor | Medium | Training annotators + QC |
| Scaling to 100k articles | DB slow | Low | Indexing + Spark Phase 2 |
| NLP model accuracy low | User distrust | Medium | Fine-tuning + A/B testing |
| RGPD compliance | Legal risk | Low | Privacy by design (Epic 8) |

---

## 🎓 Learning Curve

**Week 1-2**: Setup + RSS integration (Easy ✅)  
**Week 3-4**: Quality pipeline (Medium ⚠️)  
**Week 5-6**: NLP/FlauBERT (Hard 🔴 - learning curve)  
**Week 7-8**: Dashboards (Medium ⚠️)  
**Week 9-12**: API + Backend (Medium ⚠️)  
**Week 13-16**: ML ops + Compliance (Hard 🔴)  

**Recommendations**:
- Use free resources: HuggingFace, FastAPI docs, PyTorch tutorials
- Join communities: r/MachineLearning, HF forums, FastAPI discord
- Pair with experienced ML engineer (2-3 sprints) if budget allows

---

## 📌 Next Actions

1. **This Week**:
   - [ ] Create Taiga project (import this roadmap)
   - [ ] Setup Miro board (paste structure above)
   - [ ] Create Trello board (Sprint 1)
   - [ ] Define team roles (PO, Dev, QA)

2. **Next Sprint (Sprint 1)**:
   - [ ] Start US 1.1: RSS Feeds
   - [ ] Daily standup (15 min)
   - [ ] Sprint review Friday
   - [ ] Sprint retro (lessons learned)

3. **Forever**:
   - [ ] Keep roadmap in sync with reality
   - [ ] Track velocity
   - [ ] Adjust sprint scope based on learnings
   - [ ] Celebrate wins 🎉

---

**Created**: 16 décembre 2025  
**Version**: 1.0  
**Last Updated**: Aujourd'hui  

Prêt pour 16 sprints? 🚀
++