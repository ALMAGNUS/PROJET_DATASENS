"""
AI Routes - Mistral + ML Inference + Local HF + Chat Insights
=============================================================
Endpoints pour chat Mistral, résumé, analyse sentiment,
inférence ML sur GoldAI, predict LocalHF, et insights assistant.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
async def chat(
    body: ChatRequest,
    current_user=Depends(require_reader)
):
    """
    Chat avec Mistral AI.

    Envoie un message et reçoit une réponse du modèle.
    """
    service = get_mistral_service()
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mistral API not configured. Set MISTRAL_API_KEY in .env."
        )
    try:
        response = service.chat(body.message)
        return ChatResponse(response=response)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mistral API error: {e!s}"
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    body: SummarizeRequest,
    current_user=Depends(require_reader)
):
    """
    Résume un texte avec Mistral AI.
    """
    service = get_mistral_service()
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mistral API not configured. Set MISTRAL_API_KEY in .env."
        )
    try:
        summary = service.summarize(body.text, max_length=body.max_length)
        return SummarizeResponse(summary=summary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mistral API error: {e!s}"
        )


@router.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(
    body: SentimentRequest,
    current_user=Depends(require_reader)
):
    """
    Analyse le sentiment d'un texte (positif/négatif/neutre).
    """
    service = get_mistral_service()
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mistral API not configured. Set MISTRAL_API_KEY in .env."
        )
    try:
        sentiment = service.analyze_sentiment(body.text)
        return SentimentResponse(sentiment=sentiment, label=sentiment)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mistral API error: {e!s}"
        )


@router.get("/ml/sentiment-goldai")
async def ml_sentiment_goldai(
    limit: int = Query(50, ge=1, le=500, description="Nombre d'articles GoldAI"),
    persist: bool = Query(False, description="Écrire dans MODEL_OUTPUT (label, score)"),
    current_user=Depends(require_reader)
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
            detail=f"GoldAI not found. Run: python scripts/merge_parquet_goldai.py - {e!s}"
        )
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML dependencies required: {e!s}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML inference error: {e!s}"
        )


# --- Local HF + Insights (Cockpit Streamlit) ---
def _build_data_context(theme: str) -> str:
    """
    Construit un contexte de données réel depuis GoldAI pour alimenter le prompt Mistral.
    Retourne un bloc texte résumant les données récentes selon le thème demandé.
    """
    import json
    from pathlib import Path
    import pandas as pd

    context_lines: list[str] = []
    try:
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
                    app_df["id"].astype("string").str.strip().fillna("").replace({"<NA>": "", "nan": "", "None": ""})
                )
                pred_df["id"] = (
                    pred_df["id"].astype("string").str.strip().fillna("").replace({"<NA>": "", "nan": "", "None": ""})
                )
                pred_cols = [c for c in ["id", "predicted_sentiment", "predicted_sentiment_score"] if c in pred_df.columns]
                pred_df = pred_df[pred_cols].drop_duplicates(subset=["id"], keep="last")
                df = app_df.merge(pred_df, on="id", how="left")
                pred_coverage = (
                    float(df["predicted_sentiment"].notna().mean())
                    if "predicted_sentiment" in df.columns and len(df) > 0
                    else 0.0
                )
                if pred_coverage < 0.3:
                    # Fallback hybride: compléter avec le sentiment legacy GoldAI quand la couverture prédiction est faible.
                    legacy_path = goldai_root / "merged_all_dates.parquet"
                    if legacy_path.exists():
                        legacy_df = pd.read_parquet(legacy_path, columns=["id", "sentiment", "sentiment_score"])
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
                        df["sentiment_score"] = df["predicted_sentiment_score"].fillna(df.get("sentiment_score_legacy"))
                    data_label = (
                        f"Gold app input + latest predictions (coverage={pred_coverage:.1%}) "
                        "avec fallback legacy sentiment"
                    )
                else:
                    if "predicted_sentiment" in df.columns:
                        df["sentiment"] = df["predicted_sentiment"]
                    if "predicted_sentiment_score" in df.columns:
                        df["sentiment_score"] = df["predicted_sentiment_score"]
                    data_label = f"Gold app input + latest model predictions (coverage={pred_coverage:.1%})"
            else:
                df = app_df
                data_label = "Gold app input (without joined predictions)"
        else:
            goldai_path = goldai_root / "merged_all_dates.parquet"
            if not goldai_path.exists():
                # Fallback: dernier GOLD disponible
                gold_dir = project_root / "data" / "gold"
                if gold_dir.exists():
                    for d in sorted(gold_dir.iterdir(), reverse=True):
                        if d.is_dir() and d.name.startswith("date="):
                            p = d / "articles.parquet"
                            if p.exists():
                                goldai_path = p
                                break

            if not goldai_path.exists():
                return "Aucune donnée disponible dans le dataset."

            df = pd.read_parquet(goldai_path)

        # Filtrer par thème si possible
        THEME_KEYWORDS = {
            "politique": ["politiqu", "gouvern", "election", "president", "parti", "senat", "assemblee", "ministre"],
            "financier": ["financ", "economie", "econom", "bourse", "marche", "inflation", "bce", "fed", "taux", "banque"],
            "utilisateurs": [],
        }
        kws = THEME_KEYWORDS.get(theme.lower(), [])
        df_theme = df
        if kws and "topic_1" in df.columns:
            mask = df["topic_1"].astype(str).str.lower().str.contains("|".join(kws), na=False)
            if "title" in df.columns:
                mask |= df["title"].astype(str).str.lower().str.contains("|".join(kws), na=False)
            if mask.sum() > 10:
                df_theme = df[mask]

        total = len(df_theme)
        context_lines.append(f"Dataset analysé : {total:,} articles (thème : {theme})")
        context_lines.append(f"Source contexte : {data_label}")

        # Sentiment distribution
        if "sentiment" in df_theme.columns:
            sv = df_theme["sentiment"].value_counts()
            sent_str = " | ".join(f"{k}: {v} ({v/total:.0%})" for k, v in sv.items())
            context_lines.append(f"Répartition sentiment : {sent_str}")
            if "sentiment_score" in df_theme.columns:
                mean_score = df_theme["sentiment_score"].mean()
                context_lines.append(f"Score sentiment moyen : {mean_score:+.3f} ({'positif' if mean_score > 0.05 else 'négatif' if mean_score < -0.05 else 'neutre'})")

        # Top topics
        if "topic_1" in df_theme.columns:
            top_topics = df_theme["topic_1"].dropna().value_counts().head(8)
            topics_str = " | ".join(f"{t}: {n}" for t, n in top_topics.items())
            context_lines.append(f"Topics principaux : {topics_str}")

        # Top sources
        if "source" in df_theme.columns:
            top_srcs = df_theme["source"].dropna().value_counts().head(5)
            srcs_str = " | ".join(f"{s}: {n}" for s, n in top_srcs.items())
            context_lines.append(f"Sources principales : {srcs_str}")

        # Articles récents (titres)
        recent_cols = [c for c in ["title", "published_at"] if c in df_theme.columns]
        if recent_cols and "published_at" in df_theme.columns:
            recent = df_theme.sort_values("published_at", ascending=False).head(5)
            titles = [str(r.get("title", ""))[:120] for _, r in recent.iterrows() if str(r.get("title", "")).strip()]
            if titles:
                context_lines.append("Articles récents :")
                for t in titles:
                    context_lines.append(f"  - {t}")

        # Tendance récente vs ancienne (si dates disponibles)
        if "published_at" in df_theme.columns and "sentiment_score" in df_theme.columns:
            try:
                df_theme = df_theme.copy()
                df_theme["_d"] = pd.to_datetime(df_theme["published_at"], errors="coerce")
                df_theme = df_theme.dropna(subset=["_d"])
                median_date = df_theme["_d"].median()
                score_recent = df_theme[df_theme["_d"] >= median_date]["sentiment_score"].mean()
                score_old = df_theme[df_theme["_d"] < median_date]["sentiment_score"].mean()
                trend = "en hausse" if score_recent > score_old + 0.05 else ("en baisse" if score_recent < score_old - 0.05 else "stable")
                context_lines.append(f"Tendance sentiment : {trend} (récent={score_recent:+.3f} vs ancien={score_old:+.3f})")
            except Exception:
                pass

    except Exception as exc:
        context_lines.append(f"(Contexte données partiellement disponible : {exc!s})")

    return "\n".join(context_lines)


def _get_mistral_analysis_paragraphs(data_context: str, theme: str) -> str:
    """
    Demande à Mistral de produire un paragraphe d'analyse politique et un paragraphe
    d'analyse financière du dataset. Enrichit le contexte pour des réponses plus pertinentes.
    """
    service = get_mistral_service()
    if not service.is_available():
        return ""

    prompt_analysis = (
        "À partir des données dataset ci-dessous, rédige deux courts paragraphes distincts :\n"
        "1. **Analyse politique** : tendances, sujets dominants, sentiment sur le gouvernement/partis (max 80 mots)\n"
        "2. **Analyse financière** : tendances économiques, marchés, indicateurs clés (max 80 mots)\n\n"
        "Données :\n" + data_context[:4000]
    )
    try:
        analysis = service.chat(
            message=prompt_analysis,
            system_prompt=(
                "Tu es un analyste expert. Réponds uniquement en français. "
                "Sois factuel, cite les chiffres du dataset. Pas d'introduction ni de conclusion."
            ),
        )
        return f"\n\n--- Synthèse Mistral (analyse politique + financière) ---\n{analysis.strip()}\n"
    except Exception:
        return ""


def _insight_reply(theme: str, message: str) -> str:
    """
    Génère une réponse d'analyse client via Mistral, enrichie du contexte GoldAI.
    """
    theme_labels = {
        "utilisateurs": "analyse des comportements et satisfaction utilisateurs",
        "financier": "analyse financière et économique (marchés, indicateurs, tendances)",
        "politique": "veille politique et analyse des tendances politiques françaises",
    }
    label = theme_labels.get(theme.lower(), theme)
    settings = get_settings()

    if not settings.mistral_api_key:
        return (
            f"**Assistant DataSens — {label}**\n\n"
            f"Question : {message[:500]}\n\n"
            "Configurez `MISTRAL_API_KEY` dans `.env` pour activer les réponses IA."
        )

    try:
        data_context = _build_data_context(theme)

        # Enrichissement : paragraphe d'analyse politique et financière par Mistral
        mistral_analysis = _get_mistral_analysis_paragraphs(data_context, theme)
        full_context = data_context + (mistral_analysis if mistral_analysis else "")

        system_prompt = (
            f"Tu es un assistant expert en analyse de données pour DataSens, "
            f"une plateforme d'analyse de sentiment et de veille pour des clients professionnels "
            f"(journalistes, analystes politiques, équipes financières).\n\n"
            f"Tu as accès aux données suivantes extraites du dataset GoldAI (articles enrichis) "
            f"et à une synthèse d'analyse politique et financière :\n\n"
            f"{full_context}\n\n"
            f"Ton rôle : répondre à la question du client en t'appuyant sur ces données réelles "
            f"et sur l'analyse politique/financière fournie. Sois précis, professionnel et actionnable. "
            f"Réponds en français. Si les données ne permettent pas de répondre précisément, indique-le clairement. "
            f"Cite les chiffres clés du dataset quand c'est pertinent. "
            f"Limite ta réponse à 300 mots maximum."
        )

        service = get_mistral_service()
        return service.chat(message=message, system_prompt=system_prompt)

    except Exception as exc:
        return (
            f"**Erreur Mistral** : {exc!s}\n\n"
            "Vérifiez que l'API Mistral est accessible et que la clé est valide."
        )


def _resolve_sentiment_model(choice: str) -> str:
    """
    Résout le modèle pour prédiction sentiment.
    Priorité: SENTIMENT_FINETUNED > sentiment_fr (76%) > camembert > flaubert.
    """
    from pathlib import Path

    settings = get_settings()
    finetuned = getattr(settings, "sentiment_finetuned_model_path", None)
    if finetuned and finetuned.strip():
        p = Path(finetuned.strip())
        if not p.is_absolute():
            p = Path.cwd() / p
        if (p / "config.json").exists():
            return str(p.resolve())
        return finetuned.strip()

    if choice == "sentiment_fr":
        return getattr(settings, "sentiment_fr_model_path", "ac0hik/Sentiment_Analysis_French")
    if choice == "camembert":
        return settings.camembert_model_path
    # flaubert = XLM-RoBERTa multilingue (robuste)
    return settings.xlm_roberta_model_path


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
        # raw = [[{label, score}, ...]] pour 1 texte
        scores = raw[0] if raw and isinstance(raw[0], list) else raw
        if not scores:
            return AIPredictResponse(model=payload.model, task=payload.task, result=[])
        if payload.task == "sentiment-analysis":
            out = compute_sentiment_output(scores)
            return AIPredictResponse(model=payload.model, task=payload.task, result=[out])
        # Autre tâche: format brut
        return AIPredictResponse(model=payload.model, task=payload.task, result=[scores[0]])
    except Exception as e:
        logger.exception("Predict error: %s", e)
        raise HTTPException(status_code=500, detail=str(e)[:200])


@router.post("/insight", response_model=InsightResponse)
def insight(payload: InsightRequest, _user=Depends(require_reader)):
    """
    Chat insights par theme : utilisateurs, financier, politique.
    Utilise par le panel Assistant IA du cockpit Streamlit.
    """
    reply = _insight_reply(payload.theme, payload.message)
    return InsightResponse(reply=reply, theme=payload.theme)
