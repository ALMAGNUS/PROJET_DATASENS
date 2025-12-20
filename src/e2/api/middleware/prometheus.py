"""
Prometheus Middleware for FastAPI E2 API
=========================================
Middleware pour exposer des métriques Prometheus
"""
from time import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry, REGISTRY

# Registry pour E2 API
e2_registry = CollectorRegistry()

# Counters - Total events
api_requests_total = Counter(
    'datasens_e2_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code'],
    registry=e2_registry
)

api_authentications_total = Counter(
    'datasens_e2_api_authentications_total',
    'Total number of authentication attempts',
    ['status'],  # success, failed
    registry=e2_registry
)

api_zone_access_total = Counter(
    'datasens_e2_api_zone_access_total',
    'Total number of zone accesses',
    ['zone', 'method'],  # raw, silver, gold
    registry=e2_registry
)

api_errors_total = Counter(
    'datasens_e2_api_errors_total',
    'Total number of API errors',
    ['status_code', 'endpoint'],
    registry=e2_registry
)

# Histograms - Duration metrics
api_request_duration_seconds = Histogram(
    'datasens_e2_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    registry=e2_registry,
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

# Gauges - Current state
api_active_connections = Gauge(
    'datasens_e2_api_active_connections',
    'Current number of active API connections',
    registry=e2_registry
)

api_active_users = Gauge(
    'datasens_e2_api_active_users',
    'Current number of active authenticated users',
    registry=e2_registry
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware Prometheus pour FastAPI E2
    Enregistre les métriques de requêtes HTTP
    """
    
    def __init__(self, app, registry=None):
        super().__init__(app)
        self.registry = registry or e2_registry
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Dispatch request et enregistre les métriques
        """
        # Ignorer les endpoints de métriques et health check
        if request.url.path in ['/metrics', '/health', '/docs', '/redoc', '/openapi.json']:
            return await call_next(request)
        
        # Début du timing
        start_time = time()
        
        # Incrémenter connexions actives
        api_active_connections.inc()
        
        try:
            # Exécuter la requête
            response = await call_next(request)
            
            # Calculer la durée
            duration = time() - start_time
            
            # Extraire endpoint (simplifié)
            endpoint = self._get_endpoint(request.url.path)
            
            # Enregistrer les métriques
            api_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code
            ).inc()
            
            api_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            # Enregistrer les erreurs
            if response.status_code >= 400:
                api_errors_total.labels(
                    status_code=response.status_code,
                    endpoint=endpoint
                ).inc()
            
            # Métriques par zone
            if '/raw/' in request.url.path:
                api_zone_access_total.labels(zone='raw', method=request.method).inc()
            elif '/silver/' in request.url.path:
                api_zone_access_total.labels(zone='silver', method=request.method).inc()
            elif '/gold/' in request.url.path:
                api_zone_access_total.labels(zone='gold', method=request.method).inc()
            
            return response
            
        except Exception as e:
            # Erreur non gérée
            duration = time() - start_time
            endpoint = self._get_endpoint(request.url.path)
            
            api_errors_total.labels(
                status_code=500,
                endpoint=endpoint
            ).inc()
            
            api_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            raise
        
        finally:
            # Décrémenter connexions actives
            api_active_connections.dec()
    
    def _get_endpoint(self, path: str) -> str:
        """
        Normalise le path pour les métriques
        Ex: /api/v1/raw/articles/123 -> /api/v1/raw/articles/{id}
        """
        # Remplacer les IDs par {id}
        parts = path.split('/')
        normalized = []
        for part in parts:
            if part.isdigit() or (part.startswith('{') and part.endswith('}')):
                normalized.append('{id}')
            else:
                normalized.append(part)
        return '/'.join(normalized) or '/'


def record_auth_success():
    """Enregistrer une authentification réussie"""
    api_authentications_total.labels(status='success').inc()


def record_auth_failure():
    """Enregistrer une authentification échouée"""
    api_authentications_total.labels(status='failed').inc()


def get_metrics():
    """Retourne les métriques Prometheus au format texte"""
    return generate_latest(e2_registry)
