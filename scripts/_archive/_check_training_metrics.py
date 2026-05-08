"""Vérifie la cohérence entre toutes les sources de métriques d'entraînement."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]

print("Référence taxonomie clés JSON ↔ vrais modèles : docs/e2/MODELE_TAXONOMIE.md\n")

# 1. Benchmark JSON
bench_path = root / "docs" / "e2" / "AI_BENCHMARK_RESULTS.json"
if bench_path.exists():
    bench = json.loads(bench_path.read_text(encoding="utf-8"))
    print("=== AI_BENCHMARK_RESULTS.json ===")
    print("  (clé interne → model_name = ce qui est réellement chargé)\n")
    for model, m in bench.items():
        if isinstance(m, dict) and "error" not in m:
            acc = m.get("accuracy", 0)
            f1 = m.get("f1_macro", 0)
            mn = m.get("model_name", "?")
            print(f"  [{model}]")
            print(f"      model_name: {mn}")
            print(f"      accuracy={acc:.3f}  f1_macro={f1:.3f}")
else:
    print("AI_BENCHMARK_RESULTS.json ABSENT")

# 2. Training results JSONs
for name in ["TRAINING_RESULTS.json", "TRAINING_RESULTS_QUICK.json"]:
    p = root / "docs" / "e2" / name
    if p.exists():
        tr = json.loads(p.read_text(encoding="utf-8"))
        print(f"\n=== {name} ===")
        print(f"  eval_accuracy    = {tr.get('eval_accuracy', '?')}")
        print(f"  eval_f1_weighted = {tr.get('eval_f1_weighted', '?')}")
        if "eval_f1_macro" in tr:
            print(f"  eval_f1_macro    = {tr.get('eval_f1_macro')}")
        print(f"  model (base HF)   = {tr.get('model', '?')}  ← backbone, pas le nom publié ALMAGNUS")
        print(f"  epochs           = {tr.get('epochs', '?')}")
        print(f"  train_samples    = {tr.get('train_samples', '?')}")
    else:
        print(f"\n{name} ABSENT")

# 3. trainer_state.json des modèles locaux
models_dir = root / "models"
if models_dir.exists():
    for model_dir in sorted(models_dir.iterdir()):
        state = model_dir / "trainer_state.json"
        if not state.exists():
            # cherche dans checkpoints
            candidates = sorted(model_dir.glob("checkpoint-*/trainer_state.json"), reverse=True)
            if candidates:
                state = candidates[0]
        if state.exists():
            s = json.loads(state.read_text(encoding="utf-8"))
            log = s.get("log_history", [])
            evals = [e for e in log if "eval_accuracy" in e]
            print(f"\n=== trainer_state: {model_dir.name} ===")
            print(f"  best_metric = {s.get('best_metric')}")
            print(f"  epoch final = {s.get('epoch')}")
            for e in evals:
                print(f"  eval @ epoch {e.get('epoch',0):.1f}: "
                      f"acc={e.get('eval_accuracy',0):.4f}  "
                      f"f1_macro={e.get('eval_f1_macro', e.get('eval_f1',0)):.4f}")
else:
    print("\nDossier models/ ABSENT")
