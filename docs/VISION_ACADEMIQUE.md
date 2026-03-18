# 🎓 Vision Académique & Recherche - DataSens E1

## 📊 Vision du Projet

**Finalité** : Analyser l'état des sentiments des français en se basant sur diverses sources, afin d'alimenter :
- **Acteurs politiques** : Faire ressortir les préoccupations des français
- **Acteurs financiers** : Guider les décisions d'investissements

## 🔬 Démarche Académique & Recherche

### Sources de Données

Le projet DataSens E1 collecte et analyse des données provenant de **sources multiples** :

#### Sources Réelles
- **RSS** : France24, Google News, Yahoo Finance
- **API** : Reddit, OpenWeather, INSEE
- **Scraping** : Trustpilot, IFOP
- **Datasets** : Kaggle (actualités financières, avis, tweets)
- **Big Data** : GDELT (événements globaux)

#### Source Académique/Recherche : **ZZDB (LAB IA)**

**zzdb_synthetic** est une source de **données synthétiques** générées dans le cadre de la recherche académique.

**Objectif** :
- Enrichir l'analyse des sentiments français
- Compléter les données réelles pour une vision plus complète
- Valider les modèles d'analyse sur des données contrôlées
- Spécialisation en climat social, politique, économique et financier français

**Caractéristiques** :
- Données synthétiques générées avec Faker
- Spécialisées en contexte français
- Thèmes : Sentiment, Social, Politique, Économique, Finance
- Garde-fous implémentés (limite, validation, qualité réduite)

**Utilisation** :
- Apparaît dans tous les rapports avec marqueur `[LAB IA]`
- Qualité réduite (`quality_score = 0.3`) pour identification
- Limite de collecte : 50 articles max par exécution
- Déduplication automatique

## 📈 Intégration dans les Rapports

### Collection Report
- ZZDB apparaît dans la liste des sources avec marqueur `[LAB IA]`
- Note académique expliquant la démarche de recherche

### Dashboard
- ZZDB inclus dans les statistiques par source
- Identification claire comme source académique/recherche
- Note explicative sur l'utilisation dans le cadre de la recherche

### Exports (RAW/SILVER/GOLD)
- ZZDB intégré dans tous les exports
- Identifiable via `source = 'zzdb_synthetic'`
- Qualité réduite pour filtrage si nécessaire

## 🎯 Objectifs de Recherche

1. **Analyse des Sentiments** : Comprendre l'état d'esprit des français
2. **Climat Social** : Identifier les préoccupations et mouvements sociaux
3. **Climat Politique** : Analyser les débats et réformes
4. **Climat Économique** : Suivre les indicateurs et tendances
5. **Climat Financier** : Guider les décisions d'investissement

## 📊 Utilisation pour les Acteurs

### Acteurs Politiques
- **Préoccupations des français** : Identifier les sujets qui préoccupent
- **Sentiment général** : Comprendre l'état d'esprit de la population
- **Tendances sociales** : Anticiper les mouvements sociaux

### Acteurs Financiers
- **Sentiment économique** : Analyser la confiance des acteurs
- **Tendances de marché** : Identifier les opportunités d'investissement
- **Risques** : Évaluer les risques liés au climat social/politique

## 🔬 Méthodologie

1. **Collecte** : Sources réelles + données synthétiques (ZZDB)
2. **Nettoyage** : Normalisation et validation
3. **Enrichissement** : Topics + Sentiment (positif/négatif/neutre)
4. **Agrégation** : RAW → SILVER → GOLD
5. **Analyse** : Rapports et visualisations

## 📝 Notes Importantes

- **ZZDB est une source académique** : Utilisée pour enrichir et valider les analyses
- **Transparence** : Tous les rapports identifient clairement ZZDB comme source synthétique
- **Garde-fous** : Limites et validations pour éviter la pollution des données réelles
- **Qualité** : Score réduit pour permettre le filtrage si nécessaire

## 🎓 Contribution à la Recherche

Le projet DataSens E1 contribue à la recherche en :
- Développant des méthodes d'analyse de sentiment pour le contexte français
- Créant des datasets enrichis pour l'analyse politique et financière
- Fournissant des outils pour l'aide à la décision publique et privée
