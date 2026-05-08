#!/usr/bin/env python3
"""
Installe un modèle fine-tuné sur Colab dans le pipeline local en une commande.

Usage:
    python scripts/install_colab_model.py path\\to\\sentiment_fr_finetuned_colab.zip

Le script:
    1. dézippe l'archive dans models/<nom>/
    2. vérifie la présence des fichiers HuggingFace requis
    3. teste un chargement rapide (tokenizer + modèle)
    4. met à jour SENTIMENT_FINETUNED_MODEL_PATH dans .env
    5. affiche les étapes restantes (redémarrage API, vérif cockpit)
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_FILES = ["config.json", "tokenizer_config.json"]
WEIGHT_FILES = ["model.safetensors", "pytorch_model.bin"]


def _print_step(idx: int, total: int, title: str) -> None:
    print(f"\n[{idx}/{total}] {title}")


def _extract_zip(zip_path: Path, target_dir: Path) -> Path:
    if not zip_path.exists():
        raise FileNotFoundError(f"Archive introuvable: {zip_path}")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(target_dir)
    nested = [p for p in target_dir.iterdir() if p.is_dir()]
    if len(nested) == 1 and not (target_dir / "config.json").exists():
        for entry in nested[0].iterdir():
            shutil.move(str(entry), str(target_dir / entry.name))
        nested[0].rmdir()
    return target_dir


def _validate_layout(model_dir: Path) -> list[str]:
    missing: list[str] = []
    for fname in REQUIRED_FILES:
        if not (model_dir / fname).exists():
            missing.append(fname)
    if not any((model_dir / w).exists() for w in WEIGHT_FILES):
        missing.append("model.safetensors|pytorch_model.bin")
    return missing


def _smoke_load(model_dir: Path) -> tuple[bool, str]:
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        return False, f"transformers indisponible: {exc}"
    try:
        AutoTokenizer.from_pretrained(str(model_dir))
        AutoModelForSequenceClassification.from_pretrained(str(model_dir))
    except Exception as exc:
        return False, f"chargement échoué: {exc}"
    return True, "tokenizer + modèle chargés sans erreur"


def _update_env(env_path: Path, relative_model_path: str) -> str:
    key = "SENTIMENT_FINETUNED_MODEL_PATH"
    new_line = f"{key}={relative_model_path}\n"
    if not env_path.exists():
        env_path.write_text(new_line, encoding="utf-8")
        return "créé"
    lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)
    replaced = False
    for i, line in enumerate(lines):
        stripped = line.lstrip("# ").strip()
        if stripped.startswith(f"{key}="):
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] = lines[-1] + "\n"
        lines.append(new_line)
    env_path.write_text("".join(lines), encoding="utf-8")
    return "mis à jour" if replaced else "ajouté"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Installe un modèle fine-tuné Colab dans le pipeline local"
    )
    parser.add_argument(
        "zip_path",
        type=str,
        help="Chemin vers l'archive téléchargée depuis Colab (.zip)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="sentiment_fr-finetuned-colab",
        help="Nom du dossier cible sous models/ (défaut: sentiment_fr-finetuned-colab)",
    )
    parser.add_argument(
        "--no-env",
        action="store_true",
        help="Ne pas modifier .env (utile pour test).",
    )
    args = parser.parse_args()

    zip_path = Path(args.zip_path).resolve()
    target_dir = (PROJECT_ROOT / "models" / args.name).resolve()
    rel_path = target_dir.relative_to(PROJECT_ROOT).as_posix()

    total = 4
    _print_step(1, total, f"Extraction de {zip_path.name}")
    _extract_zip(zip_path, target_dir)
    print(f"  -> {target_dir}")

    _print_step(2, total, "Validation de la structure du modèle")
    missing = _validate_layout(target_dir)
    if missing:
        print(f"  ECHEC: fichiers manquants: {', '.join(missing)}")
        print("  Vérifiez le contenu du zip Colab (cellule de sauvegarde).")
        return 1
    print("  OK: config.json + tokenizer + poids présents")

    _print_step(3, total, "Test de chargement (smoke test)")
    ok, msg = _smoke_load(target_dir)
    if not ok:
        print(f"  ECHEC: {msg}")
        return 2
    print(f"  OK: {msg}")

    if args.no_env:
        _print_step(4, total, "Mise à jour .env (sautée par --no-env)")
    else:
        _print_step(4, total, "Mise à jour .env")
        env_path = PROJECT_ROOT / ".env"
        action = _update_env(env_path, rel_path)
        print(f"  SENTIMENT_FINETUNED_MODEL_PATH={rel_path}  ({action})")

    print("\n[OK] Modèle Colab installé.")
    print("Etapes restantes:")
    print("  1. Redémarrer l'API: start_full.bat (ou python run_e2_api.py)")
    print("  2. Ouvrir le cockpit Streamlit, onglet IA")
    print(f"     -> 'Modèle utilisé' doit afficher: {rel_path}")
    print("  3. Tester une prédiction sur une phrase de démo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
