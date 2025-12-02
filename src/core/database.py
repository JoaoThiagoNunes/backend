from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from contextlib import contextmanager
from src.core.logging_config import logger
from src.core.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

# Escape de usuário/senha para evitar problemas com caracteres especiais
escaped_user = quote_plus(DB_USER)
escaped_pass = quote_plus(DB_PASS)

DATABASE_URL = f"postgresql+psycopg2://{escaped_user}:{escaped_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Log de conexão (mascarado por segurança)
masked = DATABASE_URL.replace(f":{escaped_pass}@", ":****@")
logger.info(f"Conectando ao banco: {masked}")

# Engine / Session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def transaction(db: Session) -> Generator[Session, None, None]:
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
