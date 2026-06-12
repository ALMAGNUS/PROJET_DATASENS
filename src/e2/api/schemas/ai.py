"""
Schemas IA - Inference locale.
"""

from pydantic import BaseModel, Field


class AIPredictRequest(BaseModel):
    text: str
    model: str
    task: str


class AIPredictResponse(BaseModel):
    model: str
    task: str
    result: list[dict]
    resolved_model: str | None = None


class InsightRequest(BaseModel):
    """Requete pour le chat insights (utilisateurs, financier, politique)."""

    theme: str  # "utilisateurs" | "financier" | "politique"
    message: str


class InsightCard(BaseModel):
    """Carte insight métier (croisement GoldAI)."""

    id: str
    type: str
    title: str
    summary: str
    facts: dict = Field(default_factory=dict)


class InsightResponse(BaseModel):
    """Réponse insights : synthèse + cartes multiples."""

    reply: str
    theme: str
    insights: list[InsightCard] = Field(default_factory=list)
    engine: str = "goldai_mistral_v3"
