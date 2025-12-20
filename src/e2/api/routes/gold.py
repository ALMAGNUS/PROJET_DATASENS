"""
GOLD Routes - Read-Only Endpoints
===================================
Endpoints pour zone GOLD (lecture seule, données enrichies)
Permissions: reader, writer, deleter, admin
"""


from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.e2.api.dependencies import require_reader
from src.e2.api.schemas.article import ArticleListResponse, ArticleResponse
from src.e2.api.schemas.user import UserInDB
from src.e2.api.services.data_service import get_data_service

router = APIRouter(prefix="/gold", tags=["GOLD Zone"])


@router.get("/articles", response_model=ArticleListResponse)
async def list_gold_articles(
    date: str | None = Query(None, description="Date au format YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(50, ge=1, le=100, description="Taille de page"),
    current_user: UserInDB = Depends(require_reader)
):
    """
    Liste les articles GOLD (lecture seule, données enrichies)

    Permissions: reader, writer, deleter, admin

    Args:
        date: Date au format YYYY-MM-DD (optionnel)
        page: Numéro de page (défaut: 1)
        page_size: Taille de page (défaut: 50, max: 100)
        current_user: Utilisateur authentifié (dépendance)

    Returns:
        ArticleListResponse avec articles paginés (sentiment + topics inclus)
    """
    data_service = get_data_service()
    offset = (page - 1) * page_size

    articles = data_service.get_gold_articles(date=date, limit=page_size, offset=offset)

    # TODO: Calculer total depuis DB
    total = len(articles)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ArticleListResponse(
        items=articles,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_gold_article(
    article_id: int,
    current_user: UserInDB = Depends(require_reader)
):
    """
    Récupère un article GOLD par ID (lecture seule, données enrichies)

    Permissions: reader, writer, deleter, admin

    Args:
        article_id: ID de l'article
        current_user: Utilisateur authentifié (dépendance)

    Returns:
        ArticleResponse avec sentiment et topics

    Raises:
        HTTPException 404: Si article non trouvé
    """
    data_service = get_data_service()
    articles = data_service.get_gold_articles(limit=1000, offset=0)  # TODO: Optimiser

    for article in articles:
        if article.raw_data_id == article_id:
            return article

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Article {article_id} not found in GOLD zone"
    )


@router.get("/stats")
async def get_gold_stats(
    current_user: UserInDB = Depends(require_reader)
):
    """
    Récupère les statistiques de la base de données

    Permissions: reader, writer, deleter, admin

    Args:
        current_user: Utilisateur authentifié (dépendance)

    Returns:
        Dict avec statistiques (total_articles, total_sources, etc.)
    """
    data_service = get_data_service()
    stats = data_service.get_database_stats()
    return stats
