from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.modules.routes import *
from src.core.database import engine
from src.core.logging_config import logger, setup_logging
from src.core.config import CORS_ORIGINS
from src.jobs.scheduler import start_scheduler, stop_scheduler
from src.modules.models import Base

# Configurar logging antes de qualquer coisa
setup_logging()

# Criar todas as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PROFIN API",
    description="API para cálculo e gerenciamento de valores PROFIN por escola",
    version="2.0"
)

# Configurar CORS (usando configuração centralizada)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# SCHEDULER PARA TAREFAS AUTOMÁTICAS (modules/jobs/tasks.py)
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

