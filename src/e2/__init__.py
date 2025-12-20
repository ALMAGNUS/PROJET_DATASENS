"""
DataSens E2 - FastAPI + RBAC
=============================
API REST avec authentification et contrôle d'accès par zone

RÈGLE: E2 utilise UNIQUEMENT E1DataReader (pas de modification E1)

Architecture OOP/SOLID/DRY:
- Schemas: Modèles Pydantic (validation)
- Services: Business logic (SRP)
- Dependencies: Injection de dépendances (DIP)
- Routes: Endpoints FastAPI (séparation des responsabilités)
"""

__version__ = "0.1.0"
__status__ = "IN_DEVELOPMENT"
