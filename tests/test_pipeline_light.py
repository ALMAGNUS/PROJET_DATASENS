#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test pipeline léger : seulement extraction Kaggle"""
import sys
import io
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from src.core import create_extractor, Source

def test_kaggle_extraction():
    """Test seulement l'extraction Kaggle"""
    print("="*70)
    print("TEST LEGER : Extraction Kaggle uniquement")
    print("="*70)
    
    # Charger config
    config_path = Path(__file__).parent.parent / 'sources_config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Trouver source Kaggle active
    kaggle_source = None
    for s in config['sources']:
        if 'kaggle' in s.get('source_name', '').lower() and s.get('active', False):
            kaggle_source = Source(**s)
            break
    
    if not kaggle_source:
        print("\n[ERREUR] Aucune source Kaggle active trouvee")
        return
    
    print(f"\nSource trouvee: {kaggle_source.source_name}")
    print(f"Type: {kaggle_source.acquisition_type}")
    print(f"URL: {kaggle_source.url}")
    
    # Extraire
    print("\nExtraction en cours...")
    try:
        extractor = create_extractor(kaggle_source)
        articles = extractor.extract()
        print(f"\n✅ {len(articles)} articles extraits")
        
        if len(articles) > 0:
            print(f"\nExemple premier article:")
            a = articles[0]
            print(f"   Titre: {a.title[:80]}...")
            print(f"   Contenu: {a.content[:80]}...")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)

if __name__ == "__main__":
    test_kaggle_extraction()
