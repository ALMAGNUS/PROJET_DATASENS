#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Affiche le répertoire home et le chemin de la base de données"""
from pathlib import Path
import os
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("\n" + "="*80)
print("RÉPERTOIRE HOME")
print("="*80)

# Répertoire home
home = Path.home()
print(f"\n📁 Votre répertoire home:")
print(f"   {home}")
print(f"   Chemin complet: {home.absolute()}")

# Variable d'environnement Windows
userprofile = os.getenv('USERPROFILE')
print(f"\n🔧 Variable USERPROFILE (Windows):")
print(f"   {userprofile}")

# Base de données
db_path = home / 'datasens_project' / 'datasens.db'
print(f"\n💾 Base de données DataSens:")
print(f"   {db_path}")
print(f"   Existe: {db_path.exists()}")
if db_path.exists():
    size_mb = db_path.stat().st_size / 1024 / 1024
    print(f"   Taille: {size_mb:.2f} MB")

print("\n" + "="*80)
print("EXPLICATION")
print("="*80)
print("""
Le répertoire HOME est votre dossier personnel sur votre ordinateur.

Sur Windows:
  • C'est généralement: C:\\Users\\VotreNom
  • Dans votre cas: C:\\Users\\Utilisateur
  • C'est là que Windows stocke vos documents, téléchargements, etc.

Pourquoi la base de données est là?
  • C'est un endroit standard et accessible
  • Sépare les données du code du projet
  • Facilite les sauvegardes (tout est au même endroit)

Pour ouvrir votre base de données:
  1. Ouvrez l'Explorateur de fichiers Windows
  2. Allez dans: C:\\Users\\Utilisateur\\datasens_project\\
  3. Double-cliquez sur: datasens.db
     (si vous avez DB Browser for SQLite installé)
""")
