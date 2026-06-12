"""
Change le mot de passe d'un utilisateur du cockpit (table PROFILS).
====================================================================
Usage:
  python scripts/change_password.py                       # mode interactif (email + mdp masques)
  python scripts/change_password.py user@example.com      # mdp tape masque
  python scripts/change_password.py --list                # liste les comptes existants

Ne change que le password_hash (bcrypt). Ne touche pas au role, prenom, etc.
Pour creer un compte ou modifier le role, utiliser scripts/create_user.py.
"""

from __future__ import annotations

import argparse
import getpass
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import get_data_dir, get_settings
from src.e2.auth.security import get_security_service


def _resolve_db_path() -> str:
    settings = get_settings()
    db_path = settings.db_path
    if not db_path.startswith("/") and not db_path.startswith("C:"):
        db_path = str(get_data_dir().parent / db_path)
    return db_path


def _list_users(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute("SELECT email, role, active, last_login FROM profils ORDER BY email")
        rows = cur.fetchall()
        if not rows:
            print("Aucun utilisateur dans la table profils.")
            return 0
        print(f"{len(rows)} utilisateur(s) :")
        print(f"{'EMAIL':40s} {'ROLE':10s} {'ACTIF':6s} LAST_LOGIN")
        for r in rows:
            print(
                f"{r['email']:40s} {r['role'] or '?':10s} "
                f"{'oui' if r['active'] else 'non':6s} {r['last_login'] or '-'}"
            )
        return 0
    finally:
        conn.close()


def _confirm_password() -> str:
    pwd = getpass.getpass("Nouveau mot de passe : ")
    if not pwd:
        print("ERREUR : mot de passe vide refuse.")
        sys.exit(1)
    pwd2 = getpass.getpass("Confirmer le mot de passe : ")
    if pwd != pwd2:
        print("ERREUR : les deux saisies different.")
        sys.exit(1)
    if len(pwd) < 8:
        print("ATTENTION : moins de 8 caracteres, c'est faible.")
    return pwd


def _update_password(db_path: str, email: str, new_password: str) -> int:
    security = get_security_service()
    new_hash = security.hash_password(new_password)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT profil_id FROM profils WHERE email = ?",
            (email,),
        )
        row = cur.fetchone()
        if not row:
            print(f"ERREUR : email '{email}' inconnu. Lancez --list pour voir les comptes.")
            return 1
        conn.execute(
            "UPDATE profils SET password_hash = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE email = ?",
            (new_hash, email),
        )
        conn.commit()
        print(f"OK : mot de passe mis a jour pour {email}.")
        return 0
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Change le mot de passe d'un utilisateur du cockpit (table PROFILS).",
    )
    parser.add_argument("email", nargs="?", help="Email du compte a modifier.")
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liste les comptes existants et sort.",
    )
    args = parser.parse_args()

    db_path = _resolve_db_path()
    if not Path(db_path).exists():
        print(f"ERREUR : base SQLite introuvable ({db_path}).")
        print("Lancez d'abord le pipeline E1 (main.py) pour initialiser la base.")
        return 1

    if args.list:
        return _list_users(db_path)

    email = args.email
    if not email:
        email = input("Email du compte : ").strip()
    if not email:
        print("ERREUR : email requis.")
        return 1

    new_password = _confirm_password()
    return _update_password(db_path, email, new_password)


if __name__ == "__main__":
    sys.exit(main())
