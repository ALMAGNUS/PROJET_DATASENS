"""
Cree ou met a jour un utilisateur dans PROFILS (email + mot de passe).
======================================================================
Usage:
  python scripts/create_user.py <email> <mot_de_passe> [--role admin|reader|writer|deleter]
  python scripts/create_user.py   # demande email et mot de passe (masque)

Exemple:
  python scripts/create_user.py jaffre.alan.pro@gmail.com "Plama2020@"
"""

import argparse
import getpass
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import get_data_dir, get_settings
from src.e2.auth.security import get_security_service

settings = get_settings()
security = get_security_service()

db_path = settings.db_path
if not db_path.startswith("/") and not db_path.startswith("C:"):
    db_path = str(get_data_dir().parent / db_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cree ou met a jour un utilisateur PROFILS")
    parser.add_argument("email", nargs="?", help="Email de l'utilisateur")
    parser.add_argument("password", nargs="?", help="Mot de passe (eviter de le mettre en clair en prod)")
    parser.add_argument("--role", default="admin", choices=["reader", "writer", "deleter", "admin"])
    parser.add_argument("--firstname", default="", help="Prenom")
    parser.add_argument("--lastname", default="", help="Nom")
    args = parser.parse_args()

    email = args.email
    password = args.password
    if not email:
        email = input("Email: ").strip()
    if not password:
        password = getpass.getpass("Mot de passe: ")

    if not email or not password:
        print("ERREUR: email et mot de passe requis.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profils'")
        if not cursor.fetchone():
            print("ERREUR: Table profils absente. Lancez d'abord le pipeline E1 ou init_profils_table.py")
            sys.exit(1)

        password_hash = security.hash_password(password)
        username = email.split("@")[0] if email else "user"
        firstname = args.firstname or "User"
        lastname = args.lastname or "DataSens"

        cursor.execute("SELECT profil_id FROM profils WHERE email = ?", (email,))
        if cursor.fetchone():
            cursor.execute(
                """
                UPDATE profils
                SET password_hash = ?, role = ?, active = 1, firstname = ?, lastname = ?, username = ?
                WHERE email = ?
                """,
                (password_hash, args.role, firstname, lastname, username, email),
            )
            print(f"OK: Utilisateur {email} mis a jour (role: {args.role}).")
        else:
            cursor.execute(
                """
                INSERT INTO profils (email, password_hash, firstname, lastname, role, active, username)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (email, password_hash, firstname, lastname, args.role, username),
            )
            print(f"OK: Utilisateur {email} cree (role: {args.role}).")
        conn.commit()
        print("Vous pouvez vous connecter au cockpit avec cet email et ce mot de passe.")
    except Exception as e:
        conn.rollback()
        print(f"ERREUR: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
