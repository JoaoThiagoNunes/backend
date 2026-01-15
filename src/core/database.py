from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from contextlib import contextmanager
from src.core.logging_config import logger
from src.core.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME
import psycopg2
from psycopg2 import sql

# Escape de usuário/senha para evitar problemas com caracteres especiais
escaped_user = quote_plus(DB_USER)
escaped_pass = quote_plus(DB_PASS)

DATABASE_URL = f"postgresql+psycopg2://{escaped_user}:{escaped_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def _ensure_database_exists():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database='postgres' 
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verificar se o banco existe
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_database WHERE datname = {}").format(
                sql.Literal(DB_NAME)
            )
        )
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Banco de dados '{DB_NAME}' não existe. Criando...")
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(DB_NAME)
                )
            )
            logger.info(f"Banco de dados '{DB_NAME}' criado com sucesso.")
        else:
            logger.info(f"Banco de dados '{DB_NAME}' já existe.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        # Tentar decodificar erro com diferentes encodings
        error_msg = str(e)
        if isinstance(e, UnicodeDecodeError):
            try:
                error_msg = str(e).encode('latin-1').decode('utf-8', errors='replace')
            except:
                pass
        logger.warning(f"Erro ao verificar/criar banco de dados: {error_msg}")
_ensure_database_exists()

# Log de conexão (mascarado por segurança)
masked = DATABASE_URL.replace(f":{escaped_pass}@", ":****@")
logger.info(f"Conectando ao banco: {masked}")

# Configurar encoding explícito para evitar problemas com caracteres especiais
# Também configurar encoding para mensagens de erro (alguns PostgreSQL retornam em latin-1)
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "client_encoding": "utf8",
        "options": "-c client_encoding=utf8"
    },
    pool_pre_ping=True,
    execution_options={
        "autocommit": False
    }
)

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
