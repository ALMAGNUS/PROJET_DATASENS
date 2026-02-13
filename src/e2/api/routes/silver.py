"""
SILVER Routes - Lecture seule (isolation E1)
============================================
- GET : actifs (reader, writer, deleter, admin)
- POST/PUT/DELETE : exposés pour cohérence API → retournent 501 par conception.
  E2 ne modifie jamais les données E1. Voir docs/README_E2_API.md.
"""


from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.e2.api.dependencies import (
    require_deleter,
    require_reader,
    require_writer,
)
from src.e2.api.schemas.article import (
    ArticleCreate,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
)
from src.e2.api.schemas.user import UserInDB
from src.e2.api.services.data_service import get_data_service

router = APIRouter(prefix="/silver", tags=["SILVER Zone"])


@router.get("/articles", response_model=ArticleListResponse)
async def list_silver_articles(
    date: str | None = Query(None, description="Date au format YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(50, ge=1, le=100, description="Taille de page"),
    current_user: UserInDB = Depends(require_reader),
):
    """
    Liste les articles SILVER (lecture)

    Permissions: reader, writer, deleter, admin

    Args:
        date: Date au format YYYY-MM-DD (optionnel)
        page: Numéro de page (défaut: 1)
        page_size: Taille de page (défaut: 50, max: 100)
        current_user: Utilisateur authentifié (dépendance)

    Returns:
        ArticleListResponse avec articles paginés
    """
    data_service = get_data_service()
    offset = (page - 1) * page_size

    articles, total = data_service.get_silver_articles_paginated(
        date=date, limit=page_size, offset=offset
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ArticleListResponse(
        items=articles, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_silver_article(article_id: int, current_user: UserInDB = Depends(require_reader)):
    """
    Récupère un article SILVER par ID (lecture)

    Permissions: reader, writer, deleter, admin

    Args:
        article_id: ID de l'article
        current_user: Utilisateur authentifié (dépendance)

    Returns:
        ArticleResponse

    Raises:
        HTTPException 404: Si article non trouvé
    """
    data_service = get_data_service()
    articles = data_service.get_silver_articles(limit=1000, offset=0)  # TODO: Optimiser

    for article in articles:
        if article.raw_data_id == article_id:
            return article

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Article {article_id} not found in SILVER zone",
    )


@router.post(
    "/articles",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        501: {
            "description": "Par conception (isolation E1) : E2 ne modifie jamais les données. Réponse attendue.",
        }
    },
)
async def create_silver_article(
    article: ArticleCreate, current_user: UserInDB = Depends(require_writer)
):
    """
    Crée un article dans la zone SILVER.

    **Retourne toujours 501** — par conception (isolation E1). E2 = reader uniquement.
    Endpoint exposé pour cohérence API. Voir docs/README_E2_API.md.
    """
    # TODO: Implémenter création article SILVER
    # Pour l'instant, on respecte l'isolation E1 (pas d'écriture)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Article creation in SILVER zone not yet implemented (E1 isolation)",
    )


@router.put(
    "/articles/{article_id}",
    response_model=ArticleResponse,
    responses={
        501: {
            "description": "Par conception (isolation E1) : E2 ne modifie jamais les données. Réponse attendue.",
        }
    },
)
async def update_silver_article(
    article_id: int, article: ArticleUpdate, current_user: UserInDB = Depends(require_writer)
):
    """
    Met à jour un article dans la zone SILVER.

    **Retourne toujours 501** — par conception (isolation E1). Voir docs/README_E2_API.md.
    """
    # TODO: Implémenter mise à jour article SILVER
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Article update in SILVER zone not yet implemented (E1 isolation)",
    )


@router.delete(
    "/articles/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        501: {
            "description": "Par conception (isolation E1) : E2 ne modifie jamais les données. Réponse attendue.",
        }
    },
)
async def delete_silver_article(article_id: int, current_user: UserInDB = Depends(require_deleter)):
    """
    Supprime un article de la zone SILVER.

    **Retourne toujours 501** — par conception (isolation E1). Voir docs/README_E2_API.md.
    """
    # TODO: Implémenter suppression article SILVER
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Article deletion in SILVER zone not yet implemented (E1 isolation)",
    )
