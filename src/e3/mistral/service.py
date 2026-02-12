"""
Mistral AI Service - E3
========================
Service pour appeler l'API Mistral (chat, résumé, enrichissement)
"""

from mistralai import Mistral

from src.config import get_settings

_settings = get_settings()
_client: Mistral | None = None


class MistralService:
    """Service Mistral AI - encapsulation des appels API"""

    def __init__(self) -> None:
        self.api_key = _settings.mistral_api_key
        self.model = _settings.mistral_model
        self.temperature = _settings.mistral_temperature
        self.max_tokens = _settings.mistral_max_tokens

    def is_available(self) -> bool:
        """Vérifie si l'API Mistral est configurée"""
        return bool(self.api_key and self.api_key.strip())

    def _get_client(self) -> Mistral:
        """Retourne le client Mistral (singleton)"""
        global _client
        if _client is None:
            if not self.is_available():
                raise ValueError("MISTRAL_API_KEY not configured. Set it in .env or environment.")
            _client = Mistral(api_key=self.api_key)
        return _client

    def chat(self, message: str, system_prompt: str | None = None) -> str:
        """
        Envoie un message au chat Mistral et retourne la réponse.

        Args:
            message: Message utilisateur
            system_prompt: Prompt système optionnel (contexte/rôle)

        Returns:
            Réponse texte du modèle

        Raises:
            ValueError: Si API key non configurée
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        client = self._get_client()
        response = client.chat.complete(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""

    def summarize(self, text: str, max_length: int = 200) -> str:
        """
        Résume un texte court.

        Args:
            text: Texte à résumer
            max_length: Longueur max cible (approximative)

        Returns:
            Résumé
        """
        system = (
            "Tu es un assistant de résumé. Réponds uniquement en français. "
            f"Fais un résumé concis en environ {max_length} caractères."
        )
        return self.chat(
            message=f"Résume ce texte:\n\n{text[:4000]}",
            system_prompt=system,
        )

    def analyze_sentiment(self, text: str) -> str:
        """
        Analyse le sentiment d'un texte (positif/négatif/neutre).

        Args:
            text: Texte à analyser

        Returns:
            Un des: "positif", "négatif", "neutre"
        """
        system = (
            "Tu es un analyseur de sentiment. Réponds UNIQUEMENT par un seul mot: "
            '"positif", "négatif" ou "neutre". Aucune autre explication.'
        )
        response = self.chat(
            message=f"Analyse le sentiment:\n\n{text[:2000]}",
            system_prompt=system,
        )
        out = response.strip().lower()
        if "positif" in out:
            return "positif"
        if "négatif" in out or "negatif" in out:
            return "négatif"
        return "neutre"


_service: MistralService | None = None


def get_mistral_service() -> MistralService:
    """Retourne le singleton MistralService"""
    global _service
    if _service is None:
        _service = MistralService()
    return _service
