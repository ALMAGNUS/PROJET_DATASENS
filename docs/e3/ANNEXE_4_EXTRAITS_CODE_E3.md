# Annexe 4 — Extraits de code E3 (illustration jury)

Cette annexe regroupe **trois extraits de code** représentatifs du bloc E3. Ils illustrent respectivement l'exposition API (C9), la résilience du monitorage (C11) et la vérification automatisée (C12). Chaque extrait est accompagné du chemin du fichier source pour consultation complète.

---

## Extrait 1 — Exposition du modèle IA via API REST (C9)

**Fichier** : `src/e2/api/routes/ai.py` (lignes 393-421)

**Compétence** : C9 — Exposer un modèle IA via API REST

**Contexte** : L'endpoint `POST /api/v1/ai/predict` expose l'inférence locale (Hugging Face) avec un contrat structuré. Le schéma `AIPredictResponse` garantit une réponse typée (`model`, `task`, `result`). La résolution du modèle priorise le fine-tuné (`SENTIMENT_FINETUNED_MODEL_PATH`), puis les backbones configurés.

```python
@router.post("/predict", response_model=AIPredictResponse)
def predict(payload: AIPredictRequest, _user=Depends(require_reader)):
    """
    Inférence locale HF (CamemBERT/sentiment_fr).
    Sentiment: label 3 classes (POSITIVE/NEUTRAL/NEGATIVE) + confidence + sentiment_score ∈ [-1,+1].
    """
    from src.ml.inference.local_hf_service import (
        LocalHFService,
        compute_sentiment_output,
    )
    from loguru import logger

    try:
        model_path = _resolve_sentiment_model(payload.model)
        task = "text-classification" if payload.task == "sentiment-analysis" else payload.task
        service = LocalHFService(model_name=model_path, task=task)
        raw = service.predict(payload.text, return_all_scores=True)
        scores = raw[0] if raw and isinstance(raw[0], list) else raw
        if not scores:
            return AIPredictResponse(model=payload.model, task=payload.task, result=[])
        if payload.task == "sentiment-analysis":
            out = compute_sentiment_output(scores)
            return AIPredictResponse(model=payload.model, task=payload.task, result=[out])
        return AIPredictResponse(model=payload.model, task=payload.task, result=[scores[0]])
    except Exception as e:
        logger.exception("Predict error: %s", e)
        raise HTTPException(status_code=500, detail=str(e)[:200])
```

**Lien** : [src/e2/api/routes/ai.py](../../src/e2/api/routes/ai.py)

---

## Extrait 2 — Résilience du monitorage drift (C11)

**Fichier** : `src/e2/api/routes/analytics.py` (lignes 262-345)

**Compétence** : C11 — Monitorer un modèle IA

**Contexte** : L'endpoint `GET /api/v1/analytics/drift-metrics` calcule les indicateurs de drift (entropy, dominance, score composite). En cas d'échec Spark/Java (ex. `JAVA_GATEWAY_EXITED`), un **fallback pandas** lit les partitions Parquet et recalcule les mêmes métriques. Les gauges Prometheus sont alimentées dans les deux cas, garantissant l'observabilité même en environnement démo sans stack Big Data.

```python
    except Exception as spark_error:
        # Fallback robuste pour environnements démo/école sans Java Spark
        try:
            fallback = _compute_drift_with_pandas(target_date=target_date)
            drift_sentiment_entropy.set(fallback.sentiment_entropy)
            drift_topic_dominance.set(fallback.topic_dominance)
            drift_score.set(fallback.drift_score)
            drift_articles_total.set(fallback.articles_total)
            return fallback
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=f"Parquet GOLD not found: {e!s}") from e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error computing drift (Spark: {spark_error!s}; fallback: {e!s})",
            ) from e
```

**Lien** : [src/e2/api/routes/analytics.py](../../src/e2/api/routes/analytics.py)

---

## Extrait 3 — Vérification automatisée du fallback (C12)

**Fichier** : `tests/test_e3_quality_gate.py` (lignes 63-97)

**Compétence** : C12 — Tester automatiquement données / entraînement / évaluation

**Contexte** : Ce test simule une panne Spark (`JAVA_GATEWAY_EXITED`) et vérifie que l'endpoint `drift-metrics` utilise le fallback pandas. Les données sont préparées dans une partition Parquet temporaire. Le test prouve que le service reste opérationnel en environnement contraint (école, démo, CI sans Java).

```python
def test_drift_metrics_endpoint_uses_pandas_fallback_when_spark_fails(tmp_path, monkeypatch):
    """
    Simule une panne Spark/Java et vérifie le fallback pandas.
    """
    data_dir = tmp_path / "data"
    gold_partition = data_dir / "gold" / "date=2026-03-11"
    gold_partition.mkdir(parents=True)

    pd.DataFrame(
        {
            "raw_data_id": [1, 2, 3, 4],
            "sentiment": ["positif", "positif", "neutre", "négatif"],
            "topic_1": ["finance", "finance", "politique", "finance"],
        }
    ).to_parquet(gold_partition / "articles.parquet", index=False)

    class BrokenReader:
        def read_gold(self, date=None):
            raise RuntimeError("JAVA_GATEWAY_EXITED")

    monkeypatch.setattr(analytics_routes, "GoldParquetReader", BrokenReader)
    monkeypatch.setattr("src.config.get_data_dir", lambda: Path(data_dir))

    client = _build_test_client()
    response = client.get(
        "/api/v1/analytics/drift-metrics?target_date=2026-03-11",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["articles_total"] == 4
    assert "drift_score" in body
    assert 0 <= body["drift_score"] <= 1
```

**Lien** : [tests/test_e3_quality_gate.py](../../tests/test_e3_quality_gate.py)

---

## Synthèse pour le jury

| Extrait | Compétence | Message clé |
|---------|------------|-------------|
| 1 | C9 | Exposition API structurée, contrat Pydantic, intégration modèle local |
| 2 | C11 | Résilience : Spark → fallback pandas, gauges Prometheus toujours alimentées |
| 3 | C12 | Test automatisé : panne simulée, vérification du fallback, reproductible en CI |

Ces extraits sont exécutables et vérifiables dans le dépôt. Le workflow `.github/workflows/e3-quality-gate.yml` exécute l'extrait 3 (et les autres tests E3) sur chaque push.
