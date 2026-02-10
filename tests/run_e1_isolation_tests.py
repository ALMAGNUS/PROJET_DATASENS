#!/usr/bin/env python3
"""
Script pour lancer les tests de non-régression E1
====================================================

Usage:
    python tests/run_e1_isolation_tests.py
    python tests/run_e1_isolation_tests.py --slow  # Inclut les tests lents
    python tests/run_e1_isolation_tests.py --fast  # Exclut les tests lents
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Lance les tests E1 isolation"""
    project_root = Path(__file__).parent.parent

    # Arguments par défaut
    args = [sys.executable, "-m", "pytest", "tests/test_e1_isolation.py", "-v", "--tb=short"]

    # Gérer les arguments
    if "--slow" in sys.argv:
        # Inclut les tests lents
        args.append("-m")
        args.append("slow or not slow")  # Tous les tests
    elif "--fast" in sys.argv or "--quick" in sys.argv:
        # Exclut les tests lents
        args.append("-m")
        args.append("not slow")

    if "--coverage" in sys.argv:
        args.extend(["--cov=src/e1", "--cov=src/shared", "--cov-report=html"])

    print("=" * 70)
    print("TESTS DE NON-RÉGRESSION E1 - ISOLATION")
    print("=" * 70)
    print(f"Lancement: {' '.join(args)}")
    print("=" * 70)
    print()

    # Lancer les tests
    result = subprocess.run(args, cwd=project_root)

    if result.returncode == 0:
        print()
        print("=" * 70)
        print("✅ TOUS LES TESTS E1 PASSENT - ISOLATION VALIDÉE")
        print("=" * 70)
    else:
        print()
        print("=" * 70)
        print("❌ CERTAINS TESTS E1 ONT ÉCHOUÉ - VÉRIFIER L'ISOLATION")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
