# src/modules/routes/__init__.py
from .admin_routes import router as admin_router
from .ano_routes import router as ano_router
from .upload_routes import router as upload_router
from .calculos_routes import router as calculo_router
from .parcelas_routes import router as parcelas_router


__all__ = ["admin_router","ano_router", "upload_router", "calculo_router", "parcelas_router"]
