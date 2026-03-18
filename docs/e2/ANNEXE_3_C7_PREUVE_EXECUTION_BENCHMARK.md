# Annexe 3 (C7) - Preuve d'exécution du benchmark

Le benchmark des modèles de sentiment a été exécuté via la commande `scripts/run_benchmark_e2.bat`, qui appelle `scripts/ai_benchmark.py` dans un environnement Python isolé.

Le dataset utilisé pour l'évaluation est `data/goldai/ia/test.parquet`, avec un échantillonnage équilibré de 80 exemples par classe (`neg`, `neu`, `pos`) en mode quick, soit 240 échantillons.

Dans la boucle complète `scripts/run_training_loop_e2.bat` (mode quick), la phase d'entraînement a été exécutée avant benchmark avec les paramètres CPU contraints suivants : 3 000 exemples train, 800 exemples validation, 1 epoch. Les métriques obtenues en fin d'epoch sont :
- `eval_accuracy = 0.68625` (68.62 %)
- `eval_f1 = 0.6362`
- `train_runtime = 1478.6 s` (24 min 38 s)

Le modèle entraîné est sauvegardé dans `models/camembert-sentiment-finetuned`.

Le benchmark final a ensuite été exécuté sur 4 modèles (`camembert_distil`, `flaubert_multilingual`, `sentiment_fr`, `finetuned_local`) et a généré les rapports finaux.

Les fichiers générés automatiquement après exécution sont :

- `docs/e2/AI_BENCHMARK.md`
- `docs/e2/AI_BENCHMARK_RESULTS.json`
- `docs/e2/AI_REQUIREMENTS.md`

L'horodatage de la dernière exécution est visible dans `docs/e2/AI_BENCHMARK.md` (`Date: 2026-03-11 00:14`).

Preuve d'exécution datée (validation) : l'exécution complète du benchmark C7 est confirmée par le journal terminal du `11/03/2026` montrant l'enchaînement des 4 modèles, puis les messages `OK Benchmark`, `OK Exigences`, `OK Résultats bruts` et `Benchmark finished`, ce qui atteste une génération effective, datée et reproductible des livrables C7.
