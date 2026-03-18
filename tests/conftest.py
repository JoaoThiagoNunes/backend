import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.modules.shared.base import Base


@pytest.fixture(scope="function")
def db_session():
    """
    Sessão de banco para testes usando SQLite in-memory.
    Importante: não importa `main.py` (evita side-effects de Postgres).
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Importar agregador para registrar TODOS os models/relationships no metadata
    # (evita erros de mapeamento por classes referenciadas apenas por string)
    import src.modules.api  # noqa: F401

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

