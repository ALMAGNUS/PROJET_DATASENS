"""
E3 Quality Gate Tests (C9-C13 support)
======================================
Tests ciblés pour sécuriser l'exposition API IA et la résilience MLOps.
"""

from pathlib import Path
import re
import sys
import types

import pandas as pd
from fastapi.testclient import TestClient

from src.e2.api.dependencies import require_reader as require_reader_dependency
from src.e2.api.dependencies.permissions import require_reader as require_reader_permissions
from src.e2.api.main import create_app
from src.e2.api.routes import analytics as analytics_routes
from src.shared.interfaces import E1DataReaderImpl


def _fake_reader_user():
    class FakeUser:
        role = "reader"

    return FakeUser()


def _build_test_client():
    app = create_app()
    app.dependency_overrides[require_reader_permissions] = _fake_reader_user
    app.dependency_overrides[require_reader_dependency] = _fake_reader_user
    return TestClient(app)


def test_read_raw_data_empty_csv_returns_empty_dataframe(tmp_path):
    """
    Garantit que l'accès RAW ne plante pas si le CSV du jour est vide.
    """
    base_path = tmp_path / "data"
    raw_dir = base_path / "raw" / "sources_2026-03-11"
    raw_dir.mkdir(parents=True)
    (raw_dir / "raw_articles.csv").write_text("", encoding="utf-8")

    reader = E1DataReaderImpl(base_path=base_path, db_path=tmp_path / "datasens.db")
    df = reader.read_raw_data("2026-03-11")

    assert df.empty
    expected_columns = {
        "raw_data_id",
        "source_id",
        "source_name",
        "title",
        "content",
        "url",
        "published_at",
        "collected_at",
        "quality_score",
    }
    assert expected_columns.issubset(set(df.columns))


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


def test_ai_predict_endpoint_contract_with_stubbed_local_model(monkeypatch):
    """
    Vérifie le contrat REST C9/C10 de /ai/predict sans téléchargement de modèle.
    """

    class DummyLocalHFService:
        def __init__(self, model_name, task):
            self.model_name = model_name
            self.task = task

        def predict(self, text, return_all_scores=True):
            assert text
            assert return_all_scores is True
            return [[{"label": "POSITIVE", "score": 0.91}]]

    def dummy_compute_sentiment_output(scores):
        assert scores[0]["label"] == "POSITIVE"
        return {
            "label": "POSITIVE",
            "confidence": 0.91,
            "sentiment_score": 0.82,
            "p_pos": 0.91,
            "p_neu": 0.05,
            "p_neg": 0.04,
        }

    fake_module = types.ModuleType("src.ml.inference.local_hf_service")
    fake_module.LocalHFService = DummyLocalHFService
    fake_module.compute_sentiment_output = dummy_compute_sentiment_output
    monkeypatch.setitem(sys.modules, "src.ml.inference.local_hf_service", fake_module)

    client = _build_test_client()
    response = client.post(
        "/api/v1/ai/predict",
        json={"text": "Le marché progresse fortement", "model": "sentiment_fr", "task": "sentiment-analysis"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "sentiment_fr"
    assert payload["task"] == "sentiment-analysis"
    assert isinstance(payload["result"], list)
    assert payload["result"][0]["label"] == "POSITIVE"
    assert "sentiment_score" in payload["result"][0]


def test_metrics_expose_drift_gauge_after_drift_call(tmp_path, monkeypatch):
    """
    Vérifie C11: les gauges drift sont visibles dans /metrics après calcul.
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
    drift_response = client.get(
        "/api/v1/analytics/drift-metrics?target_date=2026-03-11",
        headers={"Authorization": "Bearer test-token"},
    )
    assert drift_response.status_code == 200

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    metrics_text = metrics_response.text
    assert "datasens_drift_score" in metrics_text
    assert re.search(r"^datasens_drift_articles_total\s+4(\.0+)?$", metrics_text, re.MULTILINE)

