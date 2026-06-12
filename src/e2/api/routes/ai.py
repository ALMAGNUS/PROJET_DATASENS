"""
AI Routes - Mistral + ML Inference + Local HF + Chat Insights
=============================================================
Endpoints pour chat Mistral, résumé, analyse sentiment,
inférence ML sur GoldAI, predict LocalHF, et insights assistant.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field

from src.config import get_settings
from src.e2.api.dependencies.permissions import require_reader
from src.e2.api.schemas.ai import (
    AIPredictRequest,
    AIPredictResponse,
    InsightRequest,
    InsightResponse,
)
from src.e3.mistral import get_mistral_service
from src.insights.builder import build_insight_pack

router = APIRouter(prefix="/ai", tags=["AI - Mistral & ML"])


# --- Schemas Mistral (chat, summarize, sentiment) ---
class ChatRequest(BaseModel):
    """Requête chat"""

    message: str = Field(..., min_length=1, max_length=5000, description="Message utilisateur")


class ChatResponse(BaseModel):
    """Réponse chat"""

    response: str


class SummarizeRequest(BaseModel):
    """Requête résumé"""

    text: str = Field(..., min_length=1, max_length=10000)
    max_length: int = Field(default=200, ge=50, le=500, description="Longueur max cible")


class SummarizeResponse(BaseModel):
    """Réponse résumé"""

    summary: str


class SentimentRequest(BaseModel):
    """Requête analyse sentiment"""

    text: str = Field(..., min_length=1, max_length=5000)


class SentimentResponse(BaseModel):
    """Réponse sentiment"""

    sentiment: str
    label: str = Field(description="positif, négatif ou neutre")


# --- Mistral endpoints ---
@router.get("/status")
async def ai_status(current_user=Depends(require_reader)):
    """
    Vérifie si l'API Mistral est configurée et disponible.

    Returns:
        status: ok ou unavailable
        configured: bool
    """
    service = get_mistral_service()
    if service.is_available():
        return {"status": "ok", "configured": True}
    return {"status": "unavailable", "configured": False}


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, current_user=Depends(require_reader)):
    """
    Chat avec Mistral AI.

    Envoie un message et reçoit une réponse du modèle.
    """
    service = get_mistral_service()
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mistral API not configured. Set MISTRAL_API_KEY in .env.",
        )
    try:
        response = service.chat(body.message)
        return ChatResponse(response=response)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Mistral API error: {e!s}"
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(body: SummarizeRequest, current_user=Depends(require_reader)):
    """
    Résume un texte avec Mistral AI.
    """
    service = get_mistral_service()
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mistral API not configured. Set MISTRAL_API_KEY in .env.",
        )
    try:
        summary = service.summarize(body.text, max_length=body.max_length)
        return SummarizeResponse(summary=summary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Mistral API error: {e!s}"
        )


@router.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(body: SentimentRequest, current_user=Depends(require_reader)):
    """
    Analyse le sentiment d'un texte (positif/négatif/neutre).
    """
    service = get_mistral_service()
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mistral API not configured. Set MISTRAL_API_KEY in .env.",
        )
    try:
        sentiment = service.analyze_sentiment(body.text)
        return SentimentResponse(sentiment=sentiment, label=sentiment)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Mistral API error: {e!s}"
        )


@router.get("/ml/sentiment-goldai")
async def ml_sentiment_goldai(
    limit: int = Query(50, ge=1, le=500, description="Nombre d'articles GoldAI"),
    persist: bool = Query(False, description="Écrire dans MODEL_OUTPUT (label, score)"),
    current_user=Depends(require_reader),
):
    """
    Inférence sentiment ML sur GoldAI. Optimisé CPU (batch=8, max_length=256).
    Si persist=true: écrit dans model_output (model_name=sentiment_ml_distilcamembert).
    """
    try:
        from src.ml.inference.sentiment import (
            run_sentiment_inference,
            write_inference_to_model_output,
            write_predictions_parquet,
        )

        results = run_sentiment_inference(limit=limit, use_merged=True)
        persisted = 0
        predictions_path = None
        if persist and results:
            persisted = write_inference_to_model_output(results)
            predictions_path = str(write_predictions_parquet(results))
        return {
            "count": len(results),
            "persisted": persisted,
            "predictions_parquet": predictions_path,
            "results": results,
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GoldAI not found. Run: python scripts/merge_parquet_goldai.py - {e!s}",
        )
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML dependencies required: {e!s}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"ML inference error: {e!s}"
        )


# --- Local HF + Insights (Cockpit Streamlit) ---

_THEME_KEYWORDS = {
    "politique": [
        "politiqu",
        "gouvern",
        "election",
        "president",
        "parti",
        "senat",
        "assemblee",
        "ministre",
    ],
    "financier": [
        "financ",
        "economie",
        "econom",
        "bourse",
        "marche",
        "inflation",
        "bce",
        "fed",
        "taux",
        "banque",
    ],
    "utilisateurs": [],
}


def _load_goldai_theme_df(theme: str):
    """
    Charge GoldAI et filtre par thème.
    Retourne (df_theme, data_label) ou lève FileNotFoundError / ValueError.
    """
    from pathlib import Path

    import pandas as pd

    project_root = Path(__file__).resolve().parents[4]
    goldai_root = project_root / "data" / "goldai"
    app_input_path = goldai_root / "app" / "gold_app_input.parquet"
    pred_candidates = (
        sorted(
            (goldai_root / "predictions").glob("date=*/run=*/predictions.parquet"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if (goldai_root / "predictions").exists()
        else []
    )
    latest_pred_path = pred_candidates[0] if pred_candidates else None
    data_label = "GoldAI merged (legacy sentiment)"

    if app_input_path.exists() and latest_pred_path is not None:
        app_df = pd.read_parquet(app_input_path)
        pred_df = pd.read_parquet(latest_pred_path)
        if "id" in app_df.columns and "id" in pred_df.columns:
            app_df = app_df.copy()
            pred_df = pred_df.copy()
            app_df["id"] = (
                app_df["id"]
                .astype("string")
                .str.strip()
                .fillna("")
                .replace({"<NA>": "", "nan": "", "None": ""})
            )
            pred_df["id"] = (
                pred_df["id"]
                .astype("string")
                .str.strip()
                .fillna("")
                .replace({"<NA>": "", "nan": "", "None": ""})
            )
            pred_cols = [
                c
                for c in ["id", "predicted_sentiment", "predicted_sentiment_score"]
                if c in pred_df.columns
            ]
            pred_df = pred_df[pred_cols].drop_duplicates(subset=["id"], keep="last")
            df = app_df.merge(pred_df, on="id", how="left")
            pred_coverage = (
                float(df["predicted_sentiment"].notna().mean())
                if "predicted_sentiment" in df.columns and len(df) > 0
                else 0.0
            )
            if pred_coverage < 0.3:
                legacy_path = goldai_root / "merged_all_dates.parquet"
                if legacy_path.exists():
                    legacy_df = pd.read_parquet(
                        legacy_path, columns=["id", "sentiment", "sentiment_score"]
                    )
                    if "id" in legacy_df.columns:
                        legacy_df = legacy_df.copy()
                        legacy_df["id"] = (
                            legacy_df["id"]
                            .astype("string")
                            .str.strip()
                            .fillna("")
                            .replace({"<NA>": "", "nan": "", "None": ""})
                        )
                        legacy_df = legacy_df.drop_duplicates(subset=["id"], keep="last")
                        df = df.merge(
                            legacy_df.rename(
                                columns={
                                    "sentiment": "sentiment_legacy",
                                    "sentiment_score": "sentiment_score_legacy",
                                }
                            ),
                            on="id",
                            how="left",
                        )
                if "predicted_sentiment" in df.columns:
                    df["sentiment"] = df["predicted_sentiment"].fillna(df.get("sentiment_legacy"))
                if "predicted_sentiment_score" in df.columns:
                    df["sentiment_score"] = df["predicted_sentiment_score"].fillna(
                        df.get("sentiment_score_legacy")
                    )
                data_label = (
                    f"Gold app input + predictions (coverage={pred_coverage:.1%}) + legacy fallback"
                )
            else:
                if "predicted_sentiment" in df.columns:
                    df["sentiment"] = df["predicted_sentiment"]
                if "predicted_sentiment_score" in df.columns:
                    df["sentiment_score"] = df["predicted_sentiment_score"]
                data_label = f"Gold app input + predictions (coverage={pred_coverage:.1%})"
        else:
            df = app_df
            data_label = "Gold app input (without joined predictions)"
    else:
        goldai_path = goldai_root / "merged_all_dates.parquet"
        if not goldai_path.exists():
            gold_dir = project_root / "data" / "gold"
            if gold_dir.exists():
                for d in sorted(gold_dir.iterdir(), reverse=True):
                    if d.is_dir() and d.name.startswith("date="):
                        p = d / "articles.parquet"
                        if p.exists():
                            goldai_path = p
                            break
        if not goldai_path.exists():
            raise FileNotFoundError("Aucune donnée GoldAI disponible.")
        df = pd.read_parquet(goldai_path)

    kws = _THEME_KEYWORDS.get(theme.lower(), [])
    df_theme = df
    if kws and "topic_1" in df.columns:
        mask = df["topic_1"].astype(str).str.lower().str.contains("|".join(kws), na=False)
        if "title" in df.columns:
            mask |= df["title"].astype(str).str.lower().str.contains("|".join(kws), na=False)
        if mask.sum() > 10:
            df_theme = df[mask]

    if len(df_theme) == 0:
        raise ValueError(f"Aucun article pour le thème {theme}.")
    return df_theme, data_label


def _build_insight_facts(df_theme, theme: str, data_label: str) -> dict:
    total = len(df_theme)
    facts: dict = {"total": total, "theme": theme, "data_label": data_label}
    if "sentiment" in df_theme.columns and total > 0:
        sv = df_theme["sentiment"].value_counts()
        facts["sentiment_counts"] = {
            str(k): {"count": int(v), "pct": float(v) / total} for k, v in sv.items()
        }
        facts["dominant_sentiment"] = str(sv.index[0])
        facts["dominant_pct"] = float(sv.iloc[0]) / total
    if "sentiment_score" in df_theme.columns:
        facts["mean_score"] = float(df_theme["sentiment_score"].mean())
    if "topic_1" in df_theme.columns:
        tv = df_theme["topic_1"].dropna().value_counts()
        if len(tv):
            facts["top_topic"] = (str(tv.index[0]), int(tv.iloc[0]))
    if "source" in df_theme.columns:
        sv = df_theme["source"].dropna().value_counts()
        if len(sv):
            facts["top_sources"] = [(str(k), int(v)) for k, v in sv.head(3).items()]
    return facts


def _format_insight_reply(facts: dict, theme_label: str, message: str) -> str:
    """Synthèse courte ancrée sur GoldAI — format fixe pour la démo."""
    total = int(facts.get("total") or 0)
    if total <= 0:
        return "Aucune donnée GoldAI disponible pour ce thème."

    q = message.lower()
    dom = facts.get("dominant_sentiment", "—")
    dom_pct = float(facts.get("dominant_pct") or 0)

    if any(w in q for w in ("source", "contenu", "génère", "genere", "utilisateur")):
        sources = facts.get("top_sources") or []
        if sources:
            src, n = sources[0]
            lead = f"Sur {total:,} articles ({theme_label}), la source principale est {src} ({n:,} articles)."
        else:
            lead = f"Sur {total:,} articles ({theme_label}), données GoldAI disponibles."
    else:
        lead = f"Sur {total:,} articles ({theme_label}), le sentiment dominant est {dom} ({dom_pct:.0%})."

    bullets: list[str] = []
    counts = facts.get("sentiment_counts") or {}
    if counts and not any(w in q for w in ("source", "contenu", "génère", "genere")):
        order = sorted(counts.items(), key=lambda x: -x[1]["count"])
        dist = " · ".join(f"{lbl} {info['pct']:.0%}" for lbl, info in order[:3])
        bullets.append(f"- Répartition : {dist}")
    if facts.get("mean_score") is not None and not any(w in q for w in ("source", "contenu")):
        bullets.append(
            f"- Score moyen : {facts['mean_score']:+.2f} (indicateur continu, distinct du dominant)"
        )
    if any(w in q for w in ("source", "contenu", "génère", "genere", "utilisateur")):
        for src, n in (facts.get("top_sources") or [])[:3]:
            bullets.append(f"- {src} : {n:,} articles ({n/total:.0%})")
    else:
        top = facts.get("top_topic")
        if top:
            bullets.append(f"- Topic principal : {top[0]} ({top[1]:,} articles)")

    return lead + "\n" + "\n".join(bullets[:2])


def _sanitize_insight_reply(text: str) -> str:
    import re

    out = (text or "").strip()
    for pat in (
        r"\n\s*\*?\*?Recommandation",
        r"\n\s*\*?\*?Limite",
        r"\n\s*\*?\*?Points clés",
        r"\n\s*---",
    ):
        m = re.search(pat, out, flags=re.IGNORECASE)
        if m:
            out = out[: m.start()].strip()
    out = re.sub(r"\*\*([^*]+)\*\*", r"\1", out)
    out = re.sub(r"\*([^*]+)\*", r"\1", out)
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    if len(lines) > 4:
        out = "\n".join(lines[:4])
    words = out.split()
    if len(words) > 90:
        out = " ".join(words[:90]).rstrip(".,;") + "…"
    return out


def _build_data_context(theme: str) -> str:
    """
    Construit un contexte de données réel depuis GoldAI pour alimenter le prompt Mistral.
    Retourne un bloc texte résumant les données récentes selon le thème demandé.
    """
    context_lines: list[str] = []
    try:
        df_theme, data_label = _load_goldai_theme_df(theme)
        facts = _build_insight_facts(df_theme, theme, data_label)
        total = facts["total"]
        context_lines.append(f"Dataset analysé : {total:,} articles (thème : {theme})")
        context_lines.append(f"Source contexte : {data_label}")

        if facts.get("sentiment_counts"):
            sv_parts = [
                f"{k}: {v['count']} ({v['pct']:.0%})" for k, v in facts["sentiment_counts"].items()
            ]
            context_lines.append(f"Répartition sentiment : {' | '.join(sv_parts)}")
            context_lines.append(
                f"Sentiment dominant : {facts['dominant_sentiment']} ({facts['dominant_pct']:.0%})"
            )
        if facts.get("mean_score") is not None:
            context_lines.append(
                f"Score moyen continu : {facts['mean_score']:+.3f} "
                f"(indicateur distinct du sentiment dominant)"
            )
        if facts.get("top_topic"):
            t, n = facts["top_topic"]
            context_lines.append(f"Topic principal : {t}: {n}")
        if facts.get("top_sources"):
            srcs_str = " | ".join(f"{s}: {n}" for s, n in facts["top_sources"])
            context_lines.append(f"Sources principales : {srcs_str}")

        import pandas as pd

        if "published_at" in df_theme.columns and "sentiment_score" in df_theme.columns:
            try:
                dt = df_theme.copy()
                dt["_d"] = pd.to_datetime(dt["published_at"], errors="coerce")
                dt = dt.dropna(subset=["_d"])
                if len(dt) > 0:
                    median_date = dt["_d"].median()
                    score_recent = dt[dt["_d"] >= median_date]["sentiment_score"].mean()
                    score_old = dt[dt["_d"] < median_date]["sentiment_score"].mean()
                    trend = (
                        "en hausse"
                        if score_recent > score_old + 0.05
                        else ("en baisse" if score_recent < score_old - 0.05 else "stable")
                    )
                    context_lines.append(
                        f"Tendance sentiment : {trend} (récent={score_recent:+.3f} vs ancien={score_old:+.3f})"
                    )
            except Exception:
                pass

    except Exception as exc:
        context_lines.append(f"(Contexte données partiellement disponible : {exc!s})")

    return (
        "\n".join(context_lines) if context_lines else "Aucune donnée disponible dans le dataset."
    )


def _insight_reply(theme: str, message: str) -> str:
    """
    Synthèse insight : chiffres GoldAI (fiables) + reformulation légère Mistral (optionnelle).
    """
    theme_labels = {
        "utilisateurs": "utilisateurs",
        "financier": "financier",
        "politique": "politique",
    }
    label = theme_labels.get(theme.lower(), theme)
    settings = get_settings()

    try:
        df_theme, data_label = _load_goldai_theme_df(theme)
        facts = _build_insight_facts(df_theme, theme, data_label)
        reply = _format_insight_reply(facts, label, message)
    except Exception as exc:
        if not settings.mistral_api_key:
            return f"Aucune donnée GoldAI : {exc!s}"
        reply = _build_data_context(theme)
        reply = f"Données partielles.\n{reply[:400]}"

    if not settings.mistral_api_key:
        return reply

    try:
        service = get_mistral_service()
        if not service.is_available():
            return reply
        lead, _, bullets = reply.partition("\n")
        polished = service.chat(
            message=(
                f"Reformule cette phrase en français, max 22 mots, sans markdown, "
                f"conserve les chiffres : {lead}"
            ),
            system_prompt="Une seule phrase. Pas de **. Pas de Recommandation. Pas d'introduction.",
            temperature=0.1,
            max_tokens=80,
        )
        lead_clean = _sanitize_insight_reply(polished).split("\n")[0].strip()
        if lead_clean and len(lead_clean.split()) <= 28:
            return lead_clean + ("\n" + bullets if bullets.strip() else "")
        return reply
    except Exception:
        return reply


def _resolve_sentiment_model(choice: str) -> str:
    """
    Résout le modèle pour prédiction sentiment selon le choix explicite du client.

    - sentiment_fr / camembert / flaubert : backbone demandé
    - finetuned_local : checkpoint local benchmark prioritaire, sinon .env (Hub)
    """
    from pathlib import Path

    settings = get_settings()
    finetuned = getattr(settings, "sentiment_finetuned_model_path", None)
    choice_norm = (choice or "sentiment_fr").strip().lower()
    root = Path.cwd()

    def _local_finetuned_candidates() -> list[Path]:
        names = (
            "models/sentiment_fr-sentiment-finetuned",
            "models/camembert-sentiment-finetuned",
            "models/sentiment_fr-finetuned-colab",
        )
        out: list[Path] = []
        for name in names:
            p = Path(name)
            if not p.is_absolute():
                p = root / p
            if (p / "config.json").exists():
                out.append(p)
        return out

    def _finetuned_path() -> str | None:
        local = _local_finetuned_candidates()
        if local:
            return str(local[0].resolve())
        if not finetuned or not finetuned.strip():
            return None
        p = Path(finetuned.strip())
        if not p.is_absolute():
            p = root / p
        if (p / "config.json").exists():
            return str(p.resolve())
        if not p.exists() and "/" in finetuned.strip():
            return None
        return finetuned.strip()

    if choice_norm in ("finetuned_local", "finetuned", "local"):
        ft = _finetuned_path()
        if ft:
            return ft
        return getattr(settings, "sentiment_fr_model_path", "ac0hik/Sentiment_Analysis_French")

    if choice_norm == "sentiment_fr":
        base = getattr(settings, "sentiment_fr_model_path", "ac0hik/Sentiment_Analysis_French")
        if "datasens-sentiment-fr" in base.lower():
            return "ac0hik/Sentiment_Analysis_French"
        return base
    if choice_norm == "camembert":
        return settings.camembert_model_path
    return settings.xlm_roberta_model_path


@router.post("/predict", response_model=AIPredictResponse)
def predict(payload: AIPredictRequest, _user=Depends(require_reader)):
    """
    Inférence locale HF (CamemBERT/sentiment_fr).
    Sentiment: label 3 classes (POSITIVE/NEUTRAL/NEGATIVE) + confidence + sentiment_score ∈ [-1,+1].
    """
    from src.ml.inference.local_hf_service import LocalHFService
    from src.ml.inference.sentiment_postprocess import finalize_sentiment

    try:
        model_path = _resolve_sentiment_model(payload.model)
        task = "text-classification" if payload.task == "sentiment-analysis" else payload.task
        service = LocalHFService(model_name=model_path, task=task)
        raw = service.predict(payload.text, return_all_scores=True)
        # raw = [[{label, score}, ...]] pour 1 texte
        scores = raw[0] if raw and isinstance(raw[0], list) else raw
        if not scores:
            return AIPredictResponse(
                model=payload.model,
                task=payload.task,
                result=[],
                resolved_model=model_path,
            )
        if payload.task == "sentiment-analysis":
            out = finalize_sentiment(payload.text, scores)
            return AIPredictResponse(
                model=payload.model,
                task=payload.task,
                result=[out],
                resolved_model=model_path,
            )
        # Autre tâche: format brut
        return AIPredictResponse(
            model=payload.model,
            task=payload.task,
            result=[scores[0]],
            resolved_model=model_path,
        )
    except Exception as e:
        logger.exception("Predict error: %s", e)
        raise HTTPException(status_code=500, detail=str(e)[:200])


@router.post("/insight", response_model=InsightResponse)
def insight(payload: InsightRequest, _user=Depends(require_reader)):
    """
    Insights multi-cartes par thème : sentiment, sources, météo, économie, risque.
    Croisements calculés sur GoldAI (deterministic) + synthèse Mistral optionnelle.
    """
    try:
        pack = build_insight_pack(payload.theme, payload.message)
    except Exception as e:
        logger.exception("Insight pack error: %s", e)
        raise HTTPException(status_code=500, detail=str(e)[:200]) from e
    return InsightResponse(
        reply=pack.reply,
        theme=payload.theme,
        insights=pack.insights,
        engine="goldai_mistral_v3",
    )
