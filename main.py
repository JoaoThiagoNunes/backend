from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.database import engine
from src.core.logging_config import logger, setup_logging
from src.core.config import CORS_ORIGINS
from src.core.middleware import logging_middleware, error_handler_middleware
from src.core.config_validator import ConfigValidator
from src.core.jobs.scheduler import start_scheduler, stop_scheduler
from src.modules.shared.base import Base

# Importar routers e models centralizados
from src.modules.api import (
    # Routers
    admin_router,
    ano_router,
    upload_router,
    calculo_router,
    parcelas_router,
    projeto_router,
    complemento_router,
    # Models (para registro no SQLAlchemy)
    AnoLetivo,
    Upload,
    Escola,
    CalculosProfin,
    ParcelasProfin,
    LiberacoesParcela,
    LiberacoesProjeto,
    ComplementoUpload,
    ComplementoEscola,
)

# Configurar logging antes de qualquer coisa
setup_logging()

# Validar configurações
try:
    ConfigValidator.validate_all()
except Exception as e:
    logger.error(f"Erro na validação de configurações: {e}")
    raise

# Criar todas as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PROFIN API",
    description="API para cálculo e gerenciamento de valores PROFIN por escola",
    version="2.0"
)

# Configurar middlewares
# Ordem importa: error_handler deve ser o primeiro, logging depois, CORS por último
app.middleware("http")(error_handler_middleware)
app.middleware("http")(logging_middleware)

# Configurar CORS (usando configuração centralizada)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# SCHEDULER PARA TAREFAS AUTOMÁTICAS (core/jobs/scheduler.py)
# ==========================================================

@app.on_event("startup")
def on_startup():
    start_scheduler()
    logger.info("Aplicação iniciada — scheduler ativo.")


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()
    logger.info("Aplicação encerrando — scheduler parado.")


# =======
# ROTAS
# =======
app.include_router(admin_router, prefix="/admin")
app.include_router(ano_router, prefix="/anos")
app.include_router(upload_router, prefix="/uploads")
app.include_router(calculo_router, prefix="/calculos")
app.include_router(parcelas_router, prefix="/parcelas")
app.include_router(projeto_router, prefix="/projetos")
app.include_router(complemento_router, prefix="/complemento")

