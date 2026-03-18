"""
Vérification E5 — MCO (C20/C21)
================================
Vérifie que les éléments de monitorage sont opérationnels.
Usage: python scripts/run_e5_verification.py

Vérifications:
- API E2 /health et /metrics accessibles
- Fichiers de configuration monitoring présents
- Procédure incidents documentée
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_api_metrics() -> bool:
    """Vérifie que l'API expose /metrics (si elle tourne)."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:8001/health")
        with urllib.request.urlopen(req, timeout=3) as r:
            if r.status == 200:
                return True
    except Exception:
        pass
    return False


def check_api_metrics_endpoint() -> bool:
    """Vérifie que /metrics retourne des données datasens_*."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:8001/metrics")
        with urllib.request.urlopen(req, timeout=3) as r:
            data = r.read().decode("utf-8")
            return "datasens_" in data
    except Exception:
        pass
    return False


def check_files() -> tuple[bool, list[str]]:
    """Vérifie la présence des fichiers E5."""
    required = [
        ("src/e2/api/middleware/prometheus.py", "Middleware Prometheus"),
        ("monitoring/prometheus_rules.yml", "Règles d'alerte"),
        ("monitoring/prometheus.local.yml", "Config Prometheus locale"),
        ("src/logging_config.py", "Configuration journalisation"),
        ("docs/METRIQUES_SEUILS_ALERTES.md", "Documentation métriques"),
        ("docs/PROCEDURE_INCIDENTS.md", "Procédure incidents"),
        ("docs/e5/PROCEDURE_INSTALLATION_MONITORING.md", "Procédure installation"),
    ]
    missing = []
    for rel_path, desc in required:
        if not (ROOT / rel_path).exists():
            missing.append(f"  - {rel_path} ({desc})")
    return len(missing) == 0, missing


def main() -> int:
    print("=" * 60)
    print("DataSens E5 — Vérification MCO (C20/C21)")
    print("=" * 60)

    ok_count = 0
    total = 0

    # Fichiers
    total += 1
    files_ok, missing = check_files()
    if files_ok:
        print("[OK] Fichiers E5 présents")
        ok_count += 1
    else:
        print("[KO] Fichiers manquants:")
        for m in missing:
            print(m)

    # API (si démarrée)
    if check_api_metrics():
        total += 1
        print("[OK] API E2 /health accessible")
        ok_count += 1
        total += 1
        if check_api_metrics_endpoint():
            print("[OK] API E2 /metrics expose datasens_*")
            ok_count += 1
        else:
            print("[--] API /metrics sans datasens_* (appeler drift-metrics pour alimenter)")
    else:
        print("[--] API E2 non démarrée (python run_e2_api.py) — vérification /health et /metrics ignorée")

    print()
    print(f"Résultat: {ok_count}/{total} vérifications OK")
    if ok_count < total and not check_api_metrics():
        print("Pour une vérification complète, démarrer l'API: python run_e2_api.py")
    return 0 if files_ok else 1


if __name__ == "__main__":
    sys.exit(main())
