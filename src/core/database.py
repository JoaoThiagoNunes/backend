import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "123456")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "profin_db")

# Escape de usuário/senha para evitar problemas com caracteres especiais
escaped_user = quote_plus(DB_USER)
escaped_pass = quote_plus(DB_PASS)

DATABASE_URL = f"postgresql+psycopg2://{escaped_user}:{escaped_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Print de debug 
masked = DATABASE_URL.replace(f":{escaped_pass}@", ":****@")
print("DATABASE_URL (masked):", masked)

# Engine / Session / Base
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
