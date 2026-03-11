"""
Run E3 quality gate tests.
==========================
Exécute un sous-ensemble de tests rapides alignés C9-C13.
"""

import subprocess
import sys


def main() -> None:
    print("=" * 72)
    print("DataSens E3 - Quality Gate (C9-C13)")
    print("=" * 72)
    print("Running targeted tests for API exposure, robustness and MLOps checks...")
    print()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_e3_quality_gate.py",
        "-v",
        "--tb=short",
    ]
    result = subprocess.run(cmd, check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

