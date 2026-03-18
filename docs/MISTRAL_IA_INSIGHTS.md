# 🤖 IA Générative Mistral - Insights Climat Social & Financier

## 🎯 Objectif

Utiliser l'API Mistral pour générer automatiquement :
1. **Résumé du dataset** complet
2. **Insights climat social** français
3. **Insights climat financier** français

---

## 🔧 Configuration

### **1. Clé API Mistral**

```bash
# .env
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-large  # ou mistral-7b-instruct
```

### **2. Installation**

```bash
pip install mistralai
```

Ajouter à `requirements.txt` :
```
mistralai==0.1.0
```

---

## 📋 Structure Proposée

```
src/
  ai/
    mistral/
      __init__.py
      client.py              # Client API Mistral
      prompts.py             # Templates prompts
      insights/
        __init__.py
        summary.py           # Résumé dataset
        social_climate.py    # Insights climat social
        financial_climate.py # Insights climat financier
      cache.py               # Cache réponses
```

---

## 🔧 Implémentation

### **1. Client API Mistral**

```python
# src/ai/mistral/client.py
import os
from mistralai import Mistral
from typing import Optional, Dict, List
import json
from datetime import datetime

class MistralClient:
    def __init__(self):
        api_key = os.getenv('MISTRAL_API_KEY')
        if not api_key:
            raise ValueError("MISTRAL_API_KEY not set")
        
        self.client = Mistral(api_key=api_key)
        self.model = os.getenv('MISTRAL_MODEL', 'mistral-large')
        self.cache = {}  # Cache simple (à améliorer avec Redis)
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        cache_key: Optional[str] = None
    ) -> str:
        """Génère texte avec Mistral (avec cache)"""
        # Vérifier cache
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un expert en analyse de données et économie française."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            result = response.choices[0].message.content
            
            # Mettre en cache
            if cache_key:
                self.cache[cache_key] = result
            
            return result
        except Exception as e:
            print(f"Erreur API Mistral: {e}")
            return f"Erreur lors de la génération: {str(e)}"
```

---

### **2. Templates Prompts**

```python
# src/ai/mistral/prompts.py
from typing import Dict

def get_summary_prompt(stats: Dict) -> str:
    """Prompt pour résumé dataset"""
    return f"""
Tu es un expert en analyse de données. Analyse et résume le dataset DataSens E1.

**Statistiques du dataset :**
- Total articles : {stats.get('total_articles', 0):,}
- Période : {stats.get('date_range', 'N/A')}
- Sources : {stats.get('nb_sources', 0)}

**Distribution sentiment :**
- Positif : {stats.get('sentiment_positif', 0):,} ({stats.get('sentiment_positif_pct', 0):.1f}%)
- Neutre : {stats.get('sentiment_neutre', 0):,} ({stats.get('sentiment_neutre_pct', 0):.1f}%)
- Négatif : {stats.get('sentiment_negatif', 0):,} ({stats.get('sentiment_negatif_pct', 0):.1f}%)

**Topics principaux :**
{stats.get('top_topics', 'N/A')}

**Instructions :**
Génère un résumé structuré et professionnel du dataset (max 500 mots) incluant :
1. Vue d'ensemble du volume et de la diversité des données
2. Tendances sentimentales principales
3. Sujets les plus discutés
4. Qualité et représentativité du dataset

Format : Texte structuré avec paragraphes clairs.
"""

def get_social_climate_prompt(stats: Dict, articles_sample: List[Dict]) -> str:
    """Prompt pour insights climat social"""
    return f"""
Tu es un expert en sociologie et analyse du climat social français.

**Contexte :**
Analyse le climat social français basé sur {stats.get('total_articles', 0):,} articles collectés.

**Distribution sentiment :**
- Positif : {stats.get('sentiment_positif_pct', 0):.1f}%
- Neutre : {stats.get('sentiment_neutre_pct', 0):.1f}%
- Négatif : {stats.get('sentiment_negatif_pct', 0):.1f}%

**Topics sociaux identifiés :**
{stats.get('social_topics', 'N/A')}

**Échantillon d'articles récents :**
{format_articles_sample(articles_sample[:5])}

**Instructions :**
Génère 5 insights clés sur le climat social français (max 300 mots chacun) :
1. Sentiment général de la population
2. Préoccupations sociales principales
3. Évolution des tendances
4. Facteurs influençant le climat social
5. Recommandations pour améliorer la compréhension

Format : Liste numérotée avec insights détaillés et structurés.
"""

def get_financial_climate_prompt(stats: Dict, articles_sample: List[Dict]) -> str:
    """Prompt pour insights climat financier"""
    return f"""
Tu es un expert en économie et analyse du climat financier français.

**Contexte :**
Analyse le climat financier français basé sur {stats.get('total_articles', 0):,} articles collectés.

**Distribution sentiment économique :**
- Positif : {stats.get('sentiment_positif_pct', 0):.1f}%
- Neutre : {stats.get('sentiment_neutre_pct', 0):.1f}%
- Négatif : {stats.get('sentiment_negatif_pct', 0):.1f}%

**Topics financiers identifiés :**
{stats.get('finance_topics', 'N/A')}

**Échantillon d'articles récents :**
{format_articles_sample(articles_sample[:5])}

**Instructions :**
Génère 5 insights clés sur le climat financier français (max 300 mots chacun) :
1. Sentiment économique général
2. Secteurs financiers les plus discutés
3. Indicateurs économiques clés
4. Risques et opportunités identifiés
5. Perspectives à court et moyen terme

Format : Liste numérotée avec insights détaillés et structurés.
"""

def format_articles_sample(articles: List[Dict]) -> str:
    """Formate échantillon d'articles pour prompt"""
    formatted = []
    for i, article in enumerate(articles, 1):
        formatted.append(f"""
Article {i}:
- Titre: {article.get('title', 'N/A')}
- Sentiment: {article.get('sentiment', 'N/A')}
- Topic: {article.get('topic_1', 'N/A')}
- Source: {article.get('source', 'N/A')}
""")
    return "\n".join(formatted)
```

---

### **3. Génération Insights**

```python
# src/ai/mistral/insights/summary.py
from src.ai.mistral.client import MistralClient
from src.ai.mistral.prompts import get_summary_prompt
from src.repository import Repository
from datetime import datetime

def generate_dataset_summary(db: Repository) -> Dict:
    """Génère résumé du dataset avec Mistral"""
    client = MistralClient()
    
    # Récupérer statistiques
    stats = get_dataset_stats(db)
    
    # Générer prompt
    prompt = get_summary_prompt(stats)
    
    # Générer résumé
    cache_key = f"summary_{datetime.now().strftime('%Y-%m-%d')}"
    summary = client.generate(prompt, max_tokens=1000, cache_key=cache_key)
    
    return {
        'summary': summary,
        'generated_at': datetime.now().isoformat(),
        'stats': stats
    }

def get_dataset_stats(db: Repository) -> Dict:
    """Récupère statistiques du dataset"""
    cursor = db.conn.cursor()
    
    # Total articles
    cursor.execute("SELECT COUNT(*) FROM raw_data")
    total = cursor.fetchone()[0]
    
    # Distribution sentiment
    cursor.execute("""
        SELECT label, COUNT(*) as count
        FROM model_output
        WHERE model_name = 'sentiment_keyword'
        GROUP BY label
    """)
    sentiments = {row[0]: row[1] for row in cursor.fetchall()}
    total_sent = sum(sentiments.values())
    
    # Top topics
    cursor.execute("""
        SELECT t.name, COUNT(*) as count
        FROM document_topic dt
        JOIN topic t ON dt.topic_id = t.topic_id
        GROUP BY t.name
        ORDER BY count DESC
        LIMIT 10
    """)
    top_topics = [f"{row[0]}: {row[1]}" for row in cursor.fetchall()]
    
    return {
        'total_articles': total,
        'sentiment_positif': sentiments.get('positif', 0),
        'sentiment_neutre': sentiments.get('neutre', 0),
        'sentiment_negatif': sentiments.get('négatif', 0),
        'sentiment_positif_pct': (sentiments.get('positif', 0) / total_sent * 100) if total_sent > 0 else 0,
        'sentiment_neutre_pct': (sentiments.get('neutre', 0) / total_sent * 100) if total_sent > 0 else 0,
        'sentiment_negatif_pct': (sentiments.get('négatif', 0) / total_sent * 100) if total_sent > 0 else 0,
        'top_topics': ', '.join(top_topics),
        'nb_sources': 21  # À récupérer dynamiquement
    }
```

---

### **4. Intégration FastAPI**

```python
# src/api/routes/insights.py
from fastapi import APIRouter, Depends
from src.api.dependencies import get_current_user, get_db
from src.api.permissions import require_reader
from src.ai.mistral.insights.summary import generate_dataset_summary
from src.ai.mistral.insights.social_climate import generate_social_insights
from src.ai.mistral.insights.financial_climate import generate_financial_insights

router = APIRouter(prefix="/api/v1/insights", tags=["Insights"])

@router.get("/summary")
@require_reader
async def get_summary(
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db)
):
    """Résumé dataset généré par Mistral"""
    return generate_dataset_summary(db)

@router.get("/social-climate")
@require_reader
async def get_social_insights(
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db)
):
    """Insights climat social générés par Mistral"""
    return generate_social_insights(db)

@router.get("/financial-climate")
@require_reader
async def get_financial_insights(
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db)
):
    """Insights climat financier générés par Mistral"""
    return generate_financial_insights(db)
```

---

### **5. Intégration Streamlit**

```python
# streamlit_app/pages/insights.py
import streamlit as st
from src.ai.mistral.insights.summary import generate_dataset_summary
from src.ai.mistral.insights.social_climate import generate_social_insights
from src.ai.mistral.insights.financial_climate import generate_financial_insights
from src.repository import Repository

st.title("🤖 Insights IA - Mistral")

db = Repository()

tab1, tab2, tab3 = st.tabs(["Résumé Dataset", "Climat Social", "Climat Financier"])

with tab1:
    st.header("Résumé du Dataset")
    if st.button("Générer Résumé"):
        with st.spinner("Génération en cours..."):
            result = generate_dataset_summary(db)
            st.markdown(result['summary'])
            st.caption(f"Généré le {result['generated_at']}")

with tab2:
    st.header("Insights Climat Social")
    if st.button("Générer Insights Social"):
        with st.spinner("Génération en cours..."):
            result = generate_social_insights(db)
            st.markdown(result['insights'])
            st.caption(f"Généré le {result['generated_at']}")

with tab3:
    st.header("Insights Climat Financier")
    if st.button("Générer Insights Financier"):
        with st.spinner("Génération en cours..."):
            result = generate_financial_insights(db)
            st.markdown(result['insights'])
            st.caption(f"Généré le {result['generated_at']}")
```

---

## 📊 Workflow Complet

```
1. Pipeline E1 → Génère GOLD (42,466 articles)
2. Modèles IA (FlauBERT/CamemBERT) → Enrichissent données
3. Mistral → Analyse GOLD et génère :
   - Résumé dataset
   - 5 insights climat social
   - 5 insights climat financier
4. Cache → Stocke réponses (évite coûts API)
5. Streamlit → Affiche insights
6. FastAPI → Expose insights via API
7. Schedule → Génération automatique quotidienne
```

---

## 💰 Gestion Coûts API Mistral

- ✅ **Cache** : Évite appels API répétés
- ✅ **Schedule** : Génération quotidienne (pas en temps réel)
- ✅ **Limite tokens** : `max_tokens=1000` par prompt
- ✅ **Monitoring** : Tracker nombre d'appels API

---

**Status** : 📋 **GUIDE COMPLET - PRÊT POUR IMPLÉMENTATION**
