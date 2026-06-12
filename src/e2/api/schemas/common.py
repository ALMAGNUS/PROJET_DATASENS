"""Validateurs partagés schémas API E2."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BeforeValidator

# EmailStr rejette .local / .test (RFC special-use) — comptes démo locaux.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    normalized = str(value).strip().lower()
    if not _EMAIL_RE.match(normalized):
        raise ValueError("invalid email format")
    return normalized


DemoSafeEmail = Annotated[str, BeforeValidator(normalize_email)]
