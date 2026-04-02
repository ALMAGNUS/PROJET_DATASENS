import pandas as pd

from src.ml.inference.goldai_loader import get_goldai_texts


def test_get_goldai_texts_accepts_string_ids_without_crash() -> None:
    df = pd.DataFrame(
        {
            "id": ["https://example.com/article/123"],
            "title": ["Titre test"],
            "content": ["Contenu test"],
        }
    )
    rows = get_goldai_texts(df)
    assert len(rows) == 1
    aid, title, text = rows[0]
    assert aid == "https://example.com/article/123"
    assert title == "Titre test"
    assert "Contenu test" in text


def test_get_goldai_texts_prefers_raw_data_id_when_present() -> None:
    df = pd.DataFrame(
        {
            "raw_data_id": [42],
            "id": ["https://example.com/article/123"],
            "title": ["Titre"],
            "content": ["Contenu"],
        }
    )
    rows = get_goldai_texts(df)
    assert len(rows) == 1
    assert rows[0][0] == "42"


def test_get_goldai_texts_fallbacks_to_id_when_raw_data_id_missing() -> None:
    df = pd.DataFrame(
        {
            "raw_data_id": [None],
            "id": ["stable-abc"],
            "title": ["Titre"],
            "content": ["Contenu"],
        }
    )
    rows = get_goldai_texts(df)
    assert len(rows) == 1
    assert rows[0][0] == "stable-abc"

