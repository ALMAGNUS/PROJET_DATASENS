"""
Script pour lancer les tests E2 API
====================================
Évite les problèmes d'encodage dans PowerShell
"""
import subprocess
import sys


def main():
    """Lance les tests E2 API"""
    print("=" * 70)
    print("DataSens E2 API - Tests")
    print("=" * 70)
    print()

    try:
        # Lancer pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_e2_api.py", "-v", "--tb=short"],
            capture_output=False,
            text=True
        )

        # Retourner le code de sortie
        sys.exit(result.returncode)

    except Exception as e:
        print(f"ERREUR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
