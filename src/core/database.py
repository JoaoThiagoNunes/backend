from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
from src.core.logging_config import logger
from src.core.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

# Escape de usuário/senha para evitar problemas com caracteres especiais
escaped_user = quote_plus(DB_USER)
escaped_pass = quote_plus(DB_PASS)

DATABASE_URL = f"postgresql+psycopg2://{escaped_user}:{escaped_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Log de conexão (mascarado por segurança)
masked = DATABASE_URL.replace(f":{escaped_pass}@", ":****@")
logger.info(f"Conectando ao banco: {masked}")

# Engine / Session / Base
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependência do FastAPI para obter sessão do banco de dados.
    
    Yields:
        Session: Sessão do SQLAlchemy
        
    Exemplo:
        @router.get("/endpoint")
        def meu_endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
