"""
Crée le compte de service `drift-refresh@datasens.local` (rôle reader)
======================================================================
Compte utilisé par `scripts/refresh_drift_metrics.py` pour rafraîchir les
gauges Prometheus de drift via l'API E2.

À lancer une seule fois après le clone du projet, ou si le compte a été
supprimé.

Usage :
  python scripts/setup_drift_refresh_account.py
  python scripts/setup_drift_refresh_account.py --password <mdp>     # non-interactif
  python scripts/setup_drift_refresh_account.py --regenerate         # régénère un mdp aléatoire

Ce que ça fait :
  1. crée (ou met à jour) le compte `drift-refresh@datasens.local` rôle `reader`
  2. écrit DRIFT_REFRESH_EMAIL et DRIFT_REFRESH_PASSWORD dans `.env`
     (n'écrase pas si la valeur existe déjà, sauf --regenerate)
  3. affiche le mot de passe une seule fois (à conserver)

Voir RUNBOOK.md § 11.4 pour la documentation complète.
"""

from __future__ import annotations

import argparse
import secrets
import sqlite3
import string
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_data_dir, get_settings
from src.e2.auth.security import get_security_service

DRIFT_EMAIL = "drift-refresh@datasens.local"
DRIFT_USERNAME = "drift_refresh"
DRIFT_ROLE = "reader"
ENV_PATH = PROJECT_ROOT / ".env"


def _generate_password(length: int = 24) -> str:
    """Mot de passe aléatoire URL-safe (pas d'espaces, pas de quotes)."""
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _resolve_db_path() -> str:
    settings = get_settings()
    db_path = settings.db_path
    if not db_path.startswith("/") and not db_path.startswith("C:"):
        db_path = str(get_data_dir().parent / db_path)
    return db_path


def upsert_account(password: str) -> None:
    security = get_security_service()
    db_path = _resolve_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profils'")
        if not cursor.fetchone():
            print(
                "ERREUR: Table profils absente. Lancer d'abord `python scripts/init_profils_table.py`."
            )
            sys.exit(1)

        password_hash = security.hash_password(password)
        cursor.execute("SELECT profil_id FROM profils WHERE email = ?", (DRIFT_EMAIL,))
        if cursor.fetchone():
            cursor.execute(
                """
                UPDATE profils
                SET password_hash = ?, role = ?, active = 1, firstname = ?, lastname = ?, username = ?
                WHERE email = ?
                """,
                (password_hash, DRIFT_ROLE, "Drift", "Refresh", DRIFT_USERNAME, DRIFT_EMAIL),
            )
            print(f"OK: compte de service {DRIFT_EMAIL} mis à jour (role: {DRIFT_ROLE}).")
        else:
            cursor.execute(
                """
                INSERT INTO profils (email, password_hash, firstname, lastname, role, active, username)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (DRIFT_EMAIL, password_hash, "Drift", "Refresh", DRIFT_ROLE, DRIFT_USERNAME),
            )
            print(f"OK: compte de service {DRIFT_EMAIL} créé (role: {DRIFT_ROLE}).")
        conn.commit()
    finally:
        conn.close()


def write_env(password: str, *, regenerate: bool) -> None:
    """Ajoute ou met à jour DRIFT_REFRESH_* dans .env."""
    if not ENV_PATH.exists():
        print(f"ATTENTION: {ENV_PATH} absent. Crée-le depuis .env.example puis relance.")
        print("\nValeurs à ajouter manuellement :")
        print(f"  DRIFT_REFRESH_EMAIL={DRIFT_EMAIL}")
        print(f"  DRIFT_REFRESH_PASSWORD={password}")
        return

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    found_email = False
    found_password = False
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("DRIFT_REFRESH_EMAIL="):
            found_email = True
            new_lines.append(f"DRIFT_REFRESH_EMAIL={DRIFT_EMAIL}")
        elif stripped.startswith("DRIFT_REFRESH_PASSWORD="):
            found_password = True
            if regenerate or stripped.endswith("="):
                new_lines.append(f"DRIFT_REFRESH_PASSWORD={password}")
            else:
                new_lines.append(line)  # on garde la valeur existante
        else:
            new_lines.append(line)

    appended: list[str] = []
    if not found_email:
        appended.append(f"DRIFT_REFRESH_EMAIL={DRIFT_EMAIL}")
    if not found_password:
        appended.append(f"DRIFT_REFRESH_PASSWORD={password}")
    if appended:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append("# Drift refresh (compte de service - cf. RUNBOOK § 11.4)")
        new_lines.extend(appended)

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    if regenerate or appended:
        print("OK: .env mis à jour avec DRIFT_REFRESH_EMAIL et DRIFT_REFRESH_PASSWORD.")
    else:
        print("INFO: .env déjà configuré (utiliser --regenerate pour forcer la rotation).")


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure le compte de service drift-refresh.")
    parser.add_argument("--password", default=None, help="Mot de passe explicite (sinon généré)")
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Force la génération d'un nouveau mot de passe (rotation)",
    )
    args = parser.parse_args()

    password = args.password or _generate_password()

    upsert_account(password)
    write_env(password, regenerate=args.regenerate)

    print()
    print("=" * 60)
    print("Compte de service drift-refresh configuré.")
    print("=" * 60)
    print(f"  Email    : {DRIFT_EMAIL}")
    print(f"  Rôle     : {DRIFT_ROLE}")
    if args.regenerate or args.password:
        print(f"  Mot de passe (à garder confidentiel) : {password}")
    else:
        print("  Mot de passe : (déjà dans .env, ou nouveau si .env n'existait pas)")
    print()
    print("Test rapide :")
    print("  python scripts/refresh_drift_metrics.py")
    print()
    print("Voir RUNBOOK.md § 11.4 pour la procédure complète.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
