"""
Rafraîchit les gauges Prometheus de drift en appelant l'API E2.
======================================================================

À appeler après chaque run pipeline (intégré dans `main.py`) ou manuellement
depuis le cockpit. Best-effort : si l'API est down, on log et on sort en 0
(ne fait jamais échouer le pipeline parent).

Usage :
  python scripts/refresh_drift_metrics.py
  python scripts/refresh_drift_metrics.py --target-date 2026-05-08
  python scripts/refresh_drift_metrics.py --quiet

Configuration (`.env`) :
  DRIFT_REFRESH_EMAIL=drift-refresh@datasens.local
  DRIFT_REFRESH_PASSWORD=<mot_de_passe_compte_de_service>
  API_BASE=http://localhost:8001  (défaut)

Création du compte de service (une fois) :
  python scripts/setup_drift_refresh_account.py

Voir RUNBOOK.md § 11.4 pour la procédure complète.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date as _date
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_API_BASE = os.getenv("API_BASE", "http://localhost:8001")
DEFAULT_EMAIL = os.getenv("DRIFT_REFRESH_EMAIL", "drift-refresh@datasens.local")
DEFAULT_PASSWORD = os.getenv("DRIFT_REFRESH_PASSWORD", "")
TIMEOUT = float(os.getenv("DRIFT_REFRESH_TIMEOUT", "10"))


def _log(msg: str, *, quiet: bool = False) -> None:
    if not quiet:
        print(f"[drift-refresh] {msg}", flush=True)


def login(api_base: str, email: str, password: str, *, quiet: bool = False) -> str | None:
    """Récupère un token JWT. Retourne None en cas d'échec."""
    url = f"{api_base}/auth/login"
    try:
        r = requests.post(
            url,
            data={"username": email, "password": password},
            timeout=TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        _log(f"API E2 injoignable ({api_base}) — gauges drift non rafraîchies (best-effort)", quiet=quiet)
        return None
    except requests.exceptions.Timeout:
        _log(f"API E2 timeout après {TIMEOUT}s — abandon", quiet=quiet)
        return None
    except Exception as e:
        _log(f"Erreur login : {type(e).__name__}: {e}", quiet=quiet)
        return None

    if r.status_code != 200:
        _log(f"Login refusé ({r.status_code}). Vérifier DRIFT_REFRESH_EMAIL/DRIFT_REFRESH_PASSWORD dans .env.", quiet=quiet)
        return None

    token = r.json().get("access_token")
    if not token:
        _log("Login OK mais pas de access_token dans la réponse — abandon", quiet=quiet)
        return None
    return token


def refresh_drift(api_base: str, token: str, target_date: str | None, *, quiet: bool = False) -> int:
    """Appelle /drift-metrics. Retourne 0 si succès, 1 sinon."""
    url = f"{api_base}/api/v1/analytics/drift-metrics"
    params = {"target_date": target_date} if target_date else {}
    try:
        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=TIMEOUT,
        )
    except requests.exceptions.Timeout:
        _log(f"Drift compute timeout après {TIMEOUT}s — abandon", quiet=quiet)
        return 1
    except Exception as e:
        _log(f"Erreur drift-metrics : {type(e).__name__}: {e}", quiet=quiet)
        return 1

    if r.status_code != 200:
        _log(f"Drift refresh KO ({r.status_code}) : {r.text[:200]}", quiet=quiet)
        return 1

    body = r.json()
    _log(
        "OK — drift_score={score:.4f} entropy={entropy:.4f} dominance={dominance:.4f} articles={total}".format(
            score=body.get("drift_score", 0.0),
            entropy=body.get("sentiment_entropy", 0.0),
            dominance=body.get("topic_dominance", 0.0),
            total=body.get("articles_total", 0),
        ),
        quiet=quiet,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Rafraîchit les gauges Prometheus de drift.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help=f"URL API E2 (défaut: {DEFAULT_API_BASE})")
    parser.add_argument("--email", default=DEFAULT_EMAIL, help="Compte de service")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Mot de passe (préférer .env)")
    parser.add_argument(
        "--target-date",
        default=_date.today().isoformat(),
        help="Date cible YYYY-MM-DD (défaut: aujourd'hui)",
    )
    parser.add_argument("--quiet", action="store_true", help="Pas d'output sur stdout")
    args = parser.parse_args()

    if not args.password:
        _log(
            "DRIFT_REFRESH_PASSWORD non défini dans .env — abandon (rester silencieux côté pipeline E1)",
            quiet=args.quiet,
        )
        return 0  # best-effort : on ne casse pas le pipeline parent

    token = login(args.api_base, args.email, args.password, quiet=args.quiet)
    if not token:
        return 0  # best-effort

    return refresh_drift(args.api_base, token, args.target_date, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
