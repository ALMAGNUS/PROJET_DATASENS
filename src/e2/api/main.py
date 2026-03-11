"""
E2 API Main - FastAPI Application
===================================
Application FastAPI principale avec tous les routers
"""

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from src.config import get_settings
from src.e2.api.middleware.audit import AuditMiddleware
from src.e2.api.middleware.prometheus import PrometheusMiddleware, get_metrics
from src.e2.api.routes import (
    ai_router,
    auth_router,
    gold_router,
    raw_router,
    silver_router,
    sources_router,
)
from src.e2.api.routes.analytics import router as analytics_router

settings = get_settings()


def create_app() -> FastAPI:
    """
    Factory pour créer l'application FastAPI

    Returns:
        FastAPI app configurée
    """
    app = FastAPI(
        title="DataSens E2 API",
        description="API REST avec authentification et contrôle d'accès par zone (RAW/SILVER/GOLD)",
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    # Prometheus metrics middleware (première position pour capturer toutes les requêtes)
    app.add_middleware(PrometheusMiddleware)

    # Audit trail middleware (avant CORS pour capturer toutes les requêtes)
    app.add_middleware(AuditMiddleware)

    # CORS middleware (CORS_ORIGINS: '*' en dev, liste d'origines en prod)
    origins_str = settings.cors_origins.strip()
    cors_origins_list = [o.strip() for o in origins_str.split(",") if o.strip()] if origins_str != "*" else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inclure les routers
    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(raw_router, prefix=settings.api_v1_prefix)
    app.include_router(silver_router, prefix=settings.api_v1_prefix)
    app.include_router(gold_router, prefix=settings.api_v1_prefix)
    app.include_router(sources_router, prefix=settings.api_v1_prefix)
    app.include_router(analytics_router, prefix=settings.api_v1_prefix)
    app.include_router(ai_router, prefix=settings.api_v1_prefix)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "ok", "service": "DataSens E2 API"}

    # Prometheus metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(content=get_metrics(), media_type="text/plain")

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        """ReDoc UI with stable JS bundle URL."""
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_js_url="https://unpkg.com/redoc@2.1.3/bundles/redoc.standalone.js",
        )

    return app


# Créer l'instance de l'app
app = create_app()
