"""
SILVER Routes - Read/Write Endpoints
=====================================
Endpoints pour zone SILVER (lecture + écriture)
Permissions:
- GET: reader, writer, deleter, admin
- POST/PUT: writer, admin
- DELETE: deleter, admin
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from src.e2.api.schemas.article import ArticleResponse, ArticleListResponse, ArticleCreate, ArticleUpdate
from src.e2.api.schemas.user import UserInDB
from src.e2.api.dependencies import (
    get_current_active_user,
    require_reader,
    require_writer,
    require_deleter
)
from src.e2.api.services.data_service import get_data_service

router = APIRouter(prefix="/silver", tags=["SILVER Zone"])


@router.get("/articles", response_model=ArticleListResponse)
async def list_silver_articles(
    date: Optional[str] = Query(None, description="Date au format YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(50, ge=1, le=100, description="Taille de page"),
    current_user: UserInDB = Depends(require_reader)
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
    
    articles = data_service.get_silver_articles(date=date, limit=page_size, offset=offset)
    
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
async def get_silver_article(
    article_id: int,
    current_user: UserInDB = Depends(require_reader)
):
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
        detail=f"Article {article_id} not found in SILVER zone"
    )


@router.post("/articles", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_silver_article(
    article: ArticleCreate,
    current_user: UserInDB = Depends(require_writer)
):
    """
    Crée un article dans la zone SILVER (écriture)
    
    Permissions: writer, admin
    
    Args:
        article: Données de l'article à créer
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        ArticleResponse
    
    Note:
        Pour l'instant, cette fonction retourne une erreur car l'écriture
        dans SILVER nécessite une modification de E1 (non autorisée).
        Cette fonction sera implémentée dans une phase ultérieure si nécessaire.
    """
    # TODO: Implémenter création article SILVER
    # Pour l'instant, on respecte l'isolation E1 (pas d'écriture)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Article creation in SILVER zone not yet implemented (E1 isolation)"
    )


@router.put("/articles/{article_id}", response_model=ArticleResponse)
async def update_silver_article(
    article_id: int,
    article: ArticleUpdate,
    current_user: UserInDB = Depends(require_writer)
):
    """
    Met à jour un article dans la zone SILVER (écriture)
    
    Permissions: writer, admin
    
    Args:
        article_id: ID de l'article
        article: Données à mettre à jour
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        ArticleResponse
    
    Note:
        Pour l'instant, cette fonction retourne une erreur car la modification
        dans SILVER nécessite une modification de E1 (non autorisée).
    """
    # TODO: Implémenter mise à jour article SILVER
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Article update in SILVER zone not yet implemented (E1 isolation)"
    )


@router.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_silver_article(
    article_id: int,
    current_user: UserInDB = Depends(require_deleter)
):
    """
    Supprime un article de la zone SILVER (suppression)
    
    Permissions: deleter, admin
    
    Args:
        article_id: ID de l'article
        current_user: Utilisateur authentifié (dépendance)
    
    Returns:
        204 No Content
    
    Note:
        Pour l'instant, cette fonction retourne une erreur car la suppression
        dans SILVER nécessite une modification de E1 (non autorisée).
    """
    # TODO: Implémenter suppression article SILVER
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Article deletion in SILVER zone not yet implemented (E1 isolation)"
    )
