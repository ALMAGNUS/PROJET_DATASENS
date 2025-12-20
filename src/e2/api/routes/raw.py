"""
RAW Routes - Read-Only Endpoints
==================================
Endpoints pour zone RAW (lecture seule)
Permissions: reader, writer, deleter, admin
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from src.e2.api.schemas.article import ArticleResponse, ArticleListResponse
from src.e2.api.schemas.user import UserInDB
from src.e2.api.dependencies import get_current_active_user, require_reader
from src.e2.api.services.data_service import get_data_service

router = APIRouter(prefix="/raw", tags=["RAW Zone"])


@router.get("/articles", response_model=ArticleListResponse)
async def list_raw_articles(
    date: Optional[str] = Query(None, description="Date au format YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(50, ge=1, le=100, description="Taille de page"),
    current_user: UserInDB = Depends(require_reader)
):
    """
    Liste les articles RAW (lecture seule)
    
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
    
    articles = data_service.get_raw_articles(date=date, limit=page_size, offset=offset)
    
    # TODO: Calculer total depuis DB (pour l'instant on retourne juste la page)
    total = len(articles)  # Approximation
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return ArticleListResponse(
        items=articles,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_raw_article(
    article_id: int,
    current_user: UserInDB = Depends(require_reader)
):
    """
    Récupère un article RAW par ID (lecture seule)
    
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
    articles = data_service.get_raw_articles(limit=1, offset=0)
    
    # Chercher l'article par ID
    for article in articles:
        if article.raw_data_id == article_id:
            return article
    
    from fastapi import HTTPException, status
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Article {article_id} not found in RAW zone"
    )
