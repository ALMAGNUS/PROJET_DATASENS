"""
Schemas IA - Inference locale.
"""

from pydantic import BaseModel


class AIPredictRequest(BaseModel):
    text: str
    model: str
    task: str


class AIPredictResponse(BaseModel):
    model: str
    task: str
    result: list[dict]


class InsightRequest(BaseModel):
    """Requete pour le chat insights (utilisateurs, financier, politique)."""
    theme: str  # "utilisateurs" | "financier" | "politique"
    message: str


class InsightResponse(BaseModel):
    """Reponse texte du assistant insights."""
    reply: str
    theme: str
