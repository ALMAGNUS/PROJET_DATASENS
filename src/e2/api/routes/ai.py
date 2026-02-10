"""
AI Routes - local HF inference + chat insights (utilisateurs, financier, politique).
"""

from fastapi import APIRouter, Depends

from src.config import get_settings
from src.e2.api.dependencies import require_reader
from src.e2.api.schemas.ai import (
    AIPredictRequest,
    AIPredictResponse,
    InsightRequest,
    InsightResponse,
)
from src.ml.inference.local_hf_service import LocalHFService

router = APIRouter(prefix="/ai", tags=["AI"])


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
    # TODO: appeler Mistral/LLM si config.mistral_api_key
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
