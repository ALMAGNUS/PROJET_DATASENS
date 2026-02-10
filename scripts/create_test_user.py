"""
Script pour créer un utilisateur de test dans PROFILS
=====================================================
Usage: python scripts/create_test_user.py
"""

import sqlite3
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_data_dir, get_settings
from src.e2.auth.security import get_security_service

settings = get_settings()
security_service = get_security_service()

# Chemin vers la DB
db_path = settings.db_path
if not db_path.startswith("/") and not db_path.startswith("C:"):
    db_path = str(get_data_dir().parent / db_path)

print(f"Creation utilisateur de test dans: {db_path}")

# Connexion DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Vérifier si la table PROFILS existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profils'")
    if not cursor.fetchone():
        print(
            "ERREUR: Table PROFILS n'existe pas. Executez d'abord le pipeline E1 pour creer la table."
        )
        sys.exit(1)

    # Créer utilisateur admin de test
    email = "admin@datasens.test"
    password = "admin123"  # Mot de passe simple pour test
    password_hash = security_service.hash_password(password)

    # Vérifier si l'utilisateur existe déjà
    cursor.execute("SELECT profil_id FROM profils WHERE email = ?", (email,))
    if cursor.fetchone():
        print(f"ATTENTION: Utilisateur {email} existe deja. Mise a jour du mot de passe...")
        cursor.execute(
            """
            UPDATE profils
            SET password_hash = ?, role = 'admin', active = 1
            WHERE email = ?
        """,
            (password_hash, email),
        )
    else:
        print(f"OK: Creation utilisateur {email}...")
        cursor.execute(
            """
            INSERT INTO profils (email, password_hash, firstname, lastname, role, active, username)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (email, password_hash, "Admin", "Test", "admin", 1, "admin"),
        )

    conn.commit()

    # Créer aussi un utilisateur reader
    email_reader = "reader@datasens.test"
    password_reader = "reader123"
    password_hash_reader = security_service.hash_password(password_reader)

    cursor.execute("SELECT profil_id FROM profils WHERE email = ?", (email_reader,))
    if cursor.fetchone():
        print(f"ATTENTION: Utilisateur {email_reader} existe deja. Mise a jour...")
        cursor.execute(
            """
            UPDATE profils
            SET password_hash = ?, role = 'reader', active = 1
            WHERE email = ?
        """,
            (password_hash_reader, email_reader),
        )
    else:
        print(f"OK: Creation utilisateur {email_reader}...")
        cursor.execute(
            """
            INSERT INTO profils (email, password_hash, firstname, lastname, role, active, username)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (email_reader, password_hash_reader, "Reader", "Test", "reader", 1, "reader"),
        )

    conn.commit()

    print("\nOK: Utilisateurs de test crees:")
    print(f"   Admin: {email} / {password} (role: admin)")
    print(f"   Reader: {email_reader} / {password_reader} (role: reader)")
    print("\nVous pouvez maintenant tester l'API avec ces credentials")

except Exception as e:
    print(f"ERREUR: {e}")
    conn.rollback()
    sys.exit(1)
finally:
    conn.close()
