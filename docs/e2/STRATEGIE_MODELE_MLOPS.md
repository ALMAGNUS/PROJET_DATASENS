# Stratégie modèle — Objectifs, apprentissage, MLOps et contrôle

**Projet** : DataSens — Modèle de sentiment  
**Date** : 2026-03

---

## Glossaire : backbone (et termes proches)

Le **backbone** (modèle de base) est le modèle pré-entraîné sur lequel on effectue le fine-tuning. C'est l'architecture + les poids initiaux qu'on adapte à nos données. Dans ce projet : `sentiment_fr`, `camembert`, `bert_multilingual`, `flaubert` sont des backbones.

**À ne pas confondre avec :**

| Terme | Signification |
|-------|---------------|
| **Barebone** | Système minimal (ex. PC barebone = boîtier + carte mère sans CPU/RAM) — terme informatique général |
| **Blackbone** | Pas un terme standard en ML |

---

## 1. Objectifs du modèle

### 1.1 Objectifs métier

| Objectif | Métrique prioritaire | Seuil cible |
|----------|---------------------|-------------|
| Qualité globale | F1 macro | ≥ 0,55 (seuil minimal) |
| Robustesse par classe | F1 par classe (neg, neu, pos) | Aucune classe à F1 < 0,20 |
| Classe minoritaire | F1 positif | ≥ 0,40 (priorité) |
| Réactivité | Latence moyenne | < 250 ms (CPU) |
| Confiance | Confiance moyenne | Pas de baisse > 0,05 vs baseline |

### 1.2 Objectifs techniques

- **Reproductibilité** : même seed, même config → mêmes résultats
- **Traçabilité** : version du modèle, hyperparamètres, dataset dans `trainer_state.json`
- **Fallback** : si modèle fine-tuné indisponible → `sentiment_fr` (backbone)

---

## 2. Stratégie d'apprentissage

### 2.1 Éviter le sur-apprentissage (overfitting)

| Signal d'overfitting | Action préventive |
|-----------------------|-------------------|
| `eval_loss` remonte alors que `train_loss` baisse | Réduire epochs (2–3), augmenter `weight_decay` |
| F1 validation << F1 train | Early stopping, régularisation L2 |
| Modèle "par cœur" les exemples | Plus de données, augmentation, dropout |
| F1 pos = 0 en test malgré bon eval | Vérifier distribution test ≠ train, class weights |

**Mécanismes déjà en place :**

- `load_best_model_at_end=True` : on garde le checkpoint avec le **meilleur eval_f1_macro**, pas le dernier
- `metric_for_best_model="f1_macro"` : évite de sur-optimiser l'accuracy au détriment des classes minoritaires
- `weight_decay=0.01` : régularisation L2
- `warmup_ratio=0.1` : montée progressive du LR pour éviter les spikes

### 2.2 Stratégie des poids (class weights)

| Situation | Action |
|-----------|--------|
| Déséquilibre classes (ex. pos = 13 %) | `class_weight='balanced'` (déjà activé) |
| Classe encore ignorée après balanced | Augmenter manuellement le poids de la classe minoritaire |
| Sur-pondération excessive | Réduire le poids, vérifier qualité des labels |

**Formule balanced** : `weight_i = n_samples / (n_classes * n_samples_i)`

### 2.3 Nombre d'epochs et early stopping

- **Recommandation** : 3 epochs pour un run complet
- **Mode quick** : 1 epoch (validation pipeline, pas production)
- **Si overfitting** : passer à 2 epochs, ou augmenter `weight_decay` à 0.02
- **Early stopping** : implicite via `load_best_model_at_end` (on ne garde pas le dernier epoch si eval dégrade)

### 2.4 Learning rate et warmup

- **LR** : 2e-5 (défaut), 3e-5 si loss stagne
- **Warmup** : 10 % des steps (évite divergence au démarrage)
- **Trop élevé** : loss instable, NaN → réduire à 1e-5

---

## 3. Stratégie de test et validation

### 3.1 Split des données

| Split | Rôle | Taille typique |
|-------|------|----------------|
| **Train** | Apprentissage | ~80 % (ex. 36 170) |
| **Val** | Sélection du meilleur checkpoint, early stopping | ~10 % (ex. 4 521) |
| **Test** | Évaluation finale, benchmark (jamais vu pendant l'entraînement) | ~10 % (ex. 4 522) |

**Règle** : le test set ne doit **jamais** servir à ajuster les hyperparamètres. Uniquement pour le benchmark final.

### 3.2 Stratégie de validation

1. **Pendant l'entraînement** : `eval_strategy="epoch"` → évaluation à chaque epoch sur le val set
2. **Sélection** : checkpoint avec le meilleur `eval_f1_macro`
3. **Post-training** : benchmark sur le test set (`scripts/ai_benchmark.py`)

### 3.3 Métriques de validation prioritaires

| Ordre | Métrique | Pourquoi |
|-------|----------|----------|
| 1 | `eval_f1_macro` | Équilibre entre classes, pas de classe ignorée |
| 2 | `eval_f1_pos` | Classe minoritaire, souvent la plus difficile |
| 3 | `eval_loss` | Détecte overfitting si remonte |
| 4 | `eval_accuracy` | Complément, mais peut masquer une classe |

---

## 4. Surcouche : matrice de seuils et de décision

### 4.1 Idée

Une **matrice de seuils** (ou couche de décision) permet d'ajuster la prédiction **après** l'inférence, sans réentraîner :

- **Seuils de confiance** : si `confidence < 0.5` → retourner "neutre" ou "indéterminé"
- **Matrice de coût** : pénaliser différemment les erreurs (ex. faux positif politique > faux négatif)
- **Mapping probabilités** : ajuster les seuils de décision par classe

### 4.2 Implémentation possible

```python
# Exemple : seuil de confiance minimal
def apply_confidence_threshold(score: dict, threshold: float = 0.5) -> str:
    if score["confidence"] < threshold:
        return "neutre"  # ou "indéterminé"
    return score["label"]

# Exemple : matrice de coût (simplifiée)
# Coût[prédit=pos, réel=neg] = 2  → on évite de prédire positif à tort
```

### 4.3 Quand l'utiliser

- **Production** : ajuster les seuils de confiance selon le feedback métier
- **Réduction du bruit** : seuil plus strict pour les cas ambigus
- **Sans réentraînement** : changement rapide, sans re-run du fine-tuning

---

## 5. Contexte enrichi

### 5.1 Ajouter du contexte au modèle

| Méthode | Où | Comment |
|---------|-----|---------|
| **Topics** | `create_ia_copy.py`, `finetune_sentiment.py` | `--topics finance,politique` filtre le dataset |
| **Longueur** | `--max-length` | 256 tokens par défaut, augmenter si besoin de contexte long |
| **Prompt Mistral** | `ai.py` | Contexte GoldAI + synthèse politique/financière dans le prompt |
| **Features externes** | Dataset | Colonnes `topic_1`, `topic_2` déjà présentes |

### 5.2 Enrichissement du dataset

- **Avant split** : s'assurer que les topics sont bien répartis dans train/val/test
- **Augmentation** : synonymes, paraphrases (à implémenter si besoin)
- **Rééquilibrage** : oversampling de la classe positive (ou `class_weight`)

---

## 6. Cycle de vie du modèle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Développement │──▶│  Validation  │──▶│  Déploiement │──▶│  Production  │
│  (train/val)   │   │  (benchmark) │   │  (SENTIMENT_  │   │  (monitoring)│
│                 │   │  (test set)  │   │   FINETUNED)  │   │              │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬───────┘
                                                                   │
                                                                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Réentraînement │◀──│  Décision │◀──│  Détection  │◀──│  Drift /     │
│  (si seuil      │   │  (seuil    │   │  (métriques │   │  Dégradation │
│   franchi)      │   │   franchi) │   │   Prometheus)│   │              │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 6.1 Étapes

1. **Développement** : `finetune_sentiment.py` sur train/val
2. **Validation** : benchmark sur test set, comparaison avec baseline
3. **Déploiement** : mise à jour `SENTIMENT_FINETUNED_MODEL_PATH` dans `.env`
4. **Production** : inférence, monitoring (Prometheus, drift-metrics)
5. **Détection** : seuils de drift franchis (voir section 7)
6. **Décision** : réentraînement ou ajustement de seuils
7. **Réentraînement** : nouveau cycle avec données récentes ou corrigées

---

## 7. Drift et stratégie de contrôle

### 7.1 Types de drift

| Type | Définition | Mesure |
|------|-------------|--------|
| **Data drift** | Distribution des entrées change (langue, longueur, thèmes) | Ratio EN/FR, longueur texte, topics dominants |
| **Concept drift** | Le sens des classes évolue (ex. ironie financière) | Baisse F1/accuracy sans changement visible des entrées |
| **Performance drift** | Qualité du modèle baisse | F1 macro, F1 par classe, accuracy |
| **Prediction drift** | Distribution des sorties change (ex. trop de neutre) | % neg/neu/pos en prod vs baseline |
| **Confidence drift** | Le modèle est moins sûr | Confiance moyenne en baisse |

### 7.2 Seuils d'alerte (exemple)

| Indicateur | Seuil | Action |
|------------|-------|--------|
| F1 macro | Baisse > 0,03 vs baseline | Alerte, préparer réentraînement |
| F1 pos | < 0,20 | Réentraînement prioritaire (class weights) |
| Distribution sorties | Écart > 10 pts sur une classe vs baseline | Audit textes, vérifier labels |
| Confiance moyenne | Baisse > 0,05 sur 7 jours | Revue cas ambigus, ajuster seuils |
| Latence | Hausse > 25 % | Ajuster batch/threads |
| Data drift | Variation > 20 % (ratio EN/FR, topics) | Rebalancer dataset, réentraînement |

### 7.3 Stratégie de contrôle

1. **Benchmark régulier** : ex. hebdomadaire sur un échantillon de contrôle annoté
2. **Drift-metrics** : endpoint `/api/v1/analytics/drift-metrics` alimente les gauges Prometheus (entropy, dominance)
3. **Réentraînement** : déclenché uniquement si seuil franchi (pas systématique)
4. **Validation post-training** : benchmark obligatoire avant changement de modèle en production
5. **A/B testing** : optionnel, comparer ancien vs nouveau modèle sur un échantillon avant bascule complète

---

## 8. MLOps — Automatisation et traçabilité

### 8.1 Ce qui est en place

- **Scripts** : `run_training_loop_e2.bat`, `create_ia_copy.py`, `finetune_sentiment.py`, `ai_benchmark.py`, `plot_e2_results.py`
- **Métriques** : `trainer_state.json`, `AI_BENCHMARK_RESULTS.json`, `TRAINING_RESULTS.json` (quick ou full)
- **Monitoring** : Prometheus (drift gauges), endpoint drift-metrics
- **CI** : quality gate E3 (tests API, predict, drift)

### 8.2 Évolutions possibles

| Évolution | Bénéfice |
|-----------|----------|
| **MLflow** | Versioning des modèles, comparaison des runs |
| **Pipeline de réentraînement** | Déclenchement automatique si drift détecté |
| **Shadow mode** | Nouveau modèle en parallèle sans impact prod |
| **Feedback loop** | Collecte des corrections utilisateurs pour réentraînement |

---

## 9. Checklist synthétique

- [ ] **Objectifs** : F1 macro ≥ 0,55, F1 pos ≥ 0,40, aucun F1 < 0,20
- [ ] **Overfitting** : `load_best_model_at_end=True`, `metric_for_best_model="f1_macro"`, 2–4 epochs max
- [ ] **Poids** : `class_weight='balanced'` sur données déséquilibrées
- [ ] **Test** : split train/val/test strict, benchmark sur test uniquement en post-training
- [ ] **Drift** : seuils définis, surveillance via drift-metrics, réentraînement si franchi
- [ ] **Surcouche** : seuils de confiance ou matrice de coût si besoin d'ajustement sans réentraînement
- [ ] **Contexte** : `--topics` pour cibler, colonnes topic_1/topic_2 dans le dataset
- [ ] **Cycle de vie** : dev → validation → déploiement → monitoring → décision (réentraînement ou seuils)
