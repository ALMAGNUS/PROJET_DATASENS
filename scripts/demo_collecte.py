#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Démo collecte - Avant/Après"""
import subprocess
import sys
import time
import re

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("\n" + "="*80)
print("  DÉMO COLLECTE - DataSens E1")
print("="*80)

# 1. Avant
print("\n[1/3] Nombre d'articles AVANT collecte...")
result = subprocess.run(
    ['python', 'scripts/query_sqlite.py', 'SELECT COUNT(*) as total FROM raw_data'],
    capture_output=True,
    text=True
)
print(result.stdout)
# Extraire le nombre depuis la sortie (chercher le nombre sur sa propre ligne, pas dans "ligne(s)")
try:
    match = re.search(r'^\s*(\d+)\s*$', result.stdout, re.MULTILINE)
    if not match:
        # Fallback: chercher le premier grand nombre (pas "1 ligne(s)")
        matches = re.findall(r'\b(\d+)\b', result.stdout)
        avant = int(max(matches, key=len)) if matches else 0
    else:
        avant = int(match.group(1))
except (ValueError, AttributeError):
    avant = 0

# 2. Collecte
print("\n[2/3] Lancement de la collecte (pipeline complet)...")
print("="*80)
subprocess.run(['python', 'main.py'])

# 3. Après
print("\n[3/3] Nombre d'articles APRÈS collecte...")
time.sleep(2)
result = subprocess.run(
    ['python', 'scripts/query_sqlite.py', 'SELECT COUNT(*) as total FROM raw_data'],
    capture_output=True,
    text=True
)
print(result.stdout)
# Extraire le nombre depuis la sortie (chercher le nombre sur sa propre ligne, pas dans "ligne(s)")
try:
    match = re.search(r'^\s*(\d+)\s*$', result.stdout, re.MULTILINE)
    if not match:
        # Fallback: chercher le premier grand nombre (pas "1 ligne(s)")
        matches = re.findall(r'\b(\d+)\b', result.stdout)
        apres = int(max(matches, key=len)) if matches else 0
    else:
        apres = int(match.group(1))
except (ValueError, AttributeError):
    apres = 0

# Résumé
print("\n" + "="*80)
print("  RÉSUMÉ")
print("="*80)
print(f"  Avant:  {avant:,} articles")
print(f"  Après:  {apres:,} articles")
print(f"  Ajout:  {apres - avant:,} nouveaux articles")
if apres > avant:
    print(f"  ✅ Collecte réussie !")
else:
    print(f"  ⚠️  Aucun nouvel article collecté")
print("="*80 + "\n")
