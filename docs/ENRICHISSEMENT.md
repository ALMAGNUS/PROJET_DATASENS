# 🔧 Guide d'Enrichissement des Articles

## ⚠️ Pourquoi seulement 4.3% des articles sont enrichis ?

### Explication

Le pipeline enrichit **automatiquement** uniquement les **nouveaux articles** collectés lors de chaque exécution de `python main.py`.

Les **anciens articles** (collectés avant) ne sont **pas enrichis automatiquement** pour éviter de surcharger le pipeline à chaque run.

### Solution : Enrichir rétroactivement

Pour enrichir **tous les articles existants** (topics + sentiment), utilisez le script d'enrichissement :

```bash
python scripts/enrich_all_articles.py
```

## 📊 Ce que fait le script

1. **Identifie** tous les articles non enrichis :
   - Articles sans topics
   - Articles sans sentiment
   - Articles avec topics mais sans sentiment
   - Articles avec sentiment mais sans topics

2. **Enrichit** chaque article :
   - **Topics** : Classification automatique (max 2 topics par article)
   - **Sentiment** : Analyse automatique (positif/neutre/négatif)

3. **Affiche** les statistiques :
   - Nombre d'articles taggés
   - Nombre d'articles analysés
   - Total traité

## ⏱️ Temps d'exécution

- **~1000 articles** : 1-2 minutes
- **~2000 articles** : 2-4 minutes
- **~5000 articles** : 5-10 minutes

Le script affiche la progression tous les 50 articles.

## ✅ Après l'enrichissement

Une fois le script terminé, relancez le dashboard :

```bash
python scripts/show_dashboard.py
```

Vous devriez voir :
- **Taux d'enrichissement** : 90-100% (au lieu de 4.3%)
- **Articles taggés** : Presque tous les articles
- **Articles analysés** : Presque tous les articles

## 🔄 Quand enrichir ?

### Enrichissement automatique (nouveaux articles)
- ✅ Se fait automatiquement à chaque `python main.py`
- ✅ Pas d'action requise

### Enrichissement rétroactif (anciens articles)
- ⚠️ À faire **une fois** après avoir collecté beaucoup d'articles
- ⚠️ À refaire si vous avez ajouté de nouveaux articles manuellement
- ⚠️ À refaire si vous avez modifié les règles de tagging/sentiment

## 📝 Exemple de sortie

```
[ENRICHISSEMENT] 1580 articles à enrichir
   Cela peut prendre quelques minutes...

   Progression: 50/1580...
   Progression: 100/1580...
   ...
   Progression: 1550/1580...

[OK] Enrichissement terminé:
   Articles taggés: 1420
   Articles analysés: 1580
   Total traités: 1580
```

## 💡 Astuce

Pour enrichir automatiquement tous les nouveaux articles à chaque collecte, le pipeline le fait déjà ! Le script `enrich_all_articles.py` est uniquement pour les **anciens articles** qui n'ont pas été enrichis lors de leur collecte initiale.

