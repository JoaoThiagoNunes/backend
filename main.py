from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.modules.routes import *
from src.core.database import engine
from src.jobs.scheduler import start_scheduler, stop_scheduler
from src.modules.models import Base

# Criar todas as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
    print("Aplicação iniciada — scheduler ativo.")


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()
    print("Aplicação encerrando — scheduler parado.")


# =======
# ROTAS
# =======
app.include_router(admin_router, prefix="/admin")
app.include_router(ano_router, prefix="/anos")
app.include_router(upload_router, prefix="/uploads")
app.include_router(calculo_router, prefix="/calculos")

