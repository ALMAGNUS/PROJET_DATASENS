"""
Benchmark IA (C7) - génération d'un comparatif et recommandation.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs" / "e2"
    docs_dir.mkdir(parents=True, exist_ok=True)

    bench_path = docs_dir / "AI_BENCHMARK.md"
    reqs_path = docs_dir / "AI_REQUIREMENTS.md"

    bench = []
    bench.append("# Benchmark IA - DataSens E2")
    bench.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    bench.append("")
    bench.append("| Solution | Coût | Latence | Confidentialité | Dépendances | Conformité |")
    bench.append("|---|---|---|---|---|---|")
    bench.append(
        "| Local HF (CamemBERT/FlauBERT) | Faible | Moyenne | Élevée | Modèles locaux | Haute |"
    )
    bench.append(
        "| API Cloud (OpenAI/Mistral) | Variable | Faible | Moyenne | Internet + API | Moyenne |"
    )
    bench.append("")
    bench.append("Conclusion: recommandation Local HF pour maîtrise des données et conformité.")

    reqs = []
    reqs.append("# Exigences IA - DataSens E2")
    reqs.append("")
    reqs.append("## Problématique")
    reqs.append("Classer et enrichir les textes (sentiment/topics) en local.")
    reqs.append("")
    reqs.append("## Contraintes")
    reqs.append("- Données sensibles: éviter l'exposition externe")
    reqs.append("- Coût maîtrisé")
    reqs.append("- Compatibilité CPU")
    reqs.append("")
    reqs.append("## Recommandation")
    reqs.append("Utiliser CamemBERT/FlauBERT en local via transformers.")

    bench_path.write_text("\n".join(bench), encoding="utf-8")
    reqs_path.write_text("\n".join(reqs), encoding="utf-8")
    print(f"OK Benchmark: {bench_path}")
    print(f"OK Exigences: {reqs_path}")


if __name__ == "__main__":
    main()
