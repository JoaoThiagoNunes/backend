# ===================
# ROUTERS
# ===================
from src.modules.features.admin.routes import admin_router
from src.modules.features.anos.routes import ano_router
from src.modules.features.uploads.routes import upload_router
from src.modules.features.calculos.routes import calculo_router
from src.modules.features.parcelas.routes import parcelas_router
from src.modules.features.projetos.routes import projeto_router

# ===================
# MODELS
# ===================
# Importar todos os models para registro no SQLAlchemy
from src.modules.features.anos import AnoLetivo
from src.modules.features.uploads import Upload
from src.modules.features.escolas import Escola
from src.modules.features.calculos import CalculosProfin
from src.modules.features.parcelas import ParcelasProfin, LiberacoesParcela
from src.modules.features.projetos import LiberacoesProjeto

__all__ = [
    # Routers
    "admin_router",
    "ano_router",
    "upload_router",
    "calculo_router",
    "parcelas_router",
    "projeto_router",
    # Models
    "AnoLetivo",
    "Upload",
    "Escola",
    "CalculosProfin",
    "ParcelasProfin",
    "LiberacoesParcela",
    "LiberacoesProjeto",
]

