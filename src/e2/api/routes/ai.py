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
    current_user=Depends(require_reader)
):
    """
    Inférence sentiment ML sur GoldAI (FlauBERT/CamemBERT).

    Charge merged_all_dates.parquet depuis data/goldai/.
    Nécessite: python scripts/merge_parquet_goldai.py
    """
    try:
        from src.ml.inference.sentiment import run_sentiment_inference
        results = run_sentiment_inference(limit=limit, use_merged=True)
        return {"count": len(results), "results": results}
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
def _insight_reply(theme: str, message: str) -> str:
    """
    Genere une reponse pour le chat insights.
    Peut etre etendue avec Mistral/LLM (config.mistral_api_key).
    """
    theme_labels = {
        "utilisateurs": "insights utilisateurs (comportement, satisfaction, personas)",
        "financier": "insights financiers (marche, tendances, indicateurs)",
        "politique": "insights politiques (veille, tendances, analyse)",
    }
    label = theme_labels.get(theme.lower(), theme)
    settings = get_settings()
    if settings.mistral_api_key:
        # Placeholder: integration Mistral a implementer
        return (
            f"[Theme: {label}]\n\n"
            f"Votre question : « {message[:500]} »\n\n"
            "Reponse synthetique (integration Mistral a brancher ici)."
        )
    return (
        f"[Theme: {label}]\n\n"
        f"Vous avez demande : « {message[:500]} »\n\n"
        "Reponse synthetique basee sur les donnees DataSens. "
        "Pour des reponses generees par IA, configurez MISTRAL_API_KEY et branchez le service Mistral."
    )


@router.post("/predict", response_model=AIPredictResponse)
def predict(payload: AIPredictRequest, _user=Depends(require_reader)):
    """Inference locale HF (CamemBERT/FlauBERT)."""
    from src.ml.inference.local_hf_service import LocalHFService

    settings = get_settings()
    if payload.model == "camembert":
        model_path = settings.camembert_model_path
    else:
        model_path = settings.flaubert_model_path

    service = LocalHFService(model_name=model_path, task=payload.task)
    result = service.predict(payload.text)
    return AIPredictResponse(model=payload.model, task=payload.task, result=result)


@router.post("/insight", response_model=InsightResponse)
def insight(payload: InsightRequest, _user=Depends(require_reader)):
    """
    Chat insights par theme : utilisateurs, financier, politique.
    Utilise par le panel Assistant IA du cockpit Streamlit.
    """
    reply = _insight_reply(payload.theme, payload.message)
    return InsightResponse(reply=reply, theme=payload.theme)
