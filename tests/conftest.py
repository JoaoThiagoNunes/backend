"""
Configuração de testes - Fixtures compartilhadas
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.core.database import get_db
from src.modules.shared.base import Base
from main import app
import io
import pandas as pd


# Banco de dados em memória para testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Cria uma sessão de banco de dados para cada teste"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Cria um cliente de teste FastAPI com banco de dados mockado"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_ano_letivo(db_session):
    """Cria um ano letivo de exemplo"""
    from src.modules.features.anos.models import AnoLetivo
    ano = AnoLetivo(ano=2026)
    db_session.add(ano)
    db_session.commit()
    db_session.refresh(ano)
    return ano


@pytest.fixture
def sample_upload(db_session, sample_ano_letivo):
    """Cria um upload de exemplo"""
    from src.modules.features.uploads.models import Upload
    upload = Upload(
        ano_letivo_id=sample_ano_letivo.id,
        filename="test_upload.xlsx",
        total_escolas=2
    )
    db_session.add(upload)
    db_session.commit()
    db_session.refresh(upload)
    return upload


@pytest.fixture
def sample_escolas(db_session, sample_ano_letivo, sample_upload):
    """Cria escolas de exemplo"""
    from src.modules.features.escolas.models import Escola
    escolas = [
        Escola(
            upload_id=sample_upload.id,
            nome_uex="Escola Teste 1",
            dre="DRE-01",
            total_alunos=100
        ),
        Escola(
            upload_id=sample_upload.id,
            nome_uex="Escola Teste 2",
            dre="DRE-02",
            total_alunos=200
        )
    ]
    for escola in escolas:
        db_session.add(escola)
    db_session.commit()
    for escola in escolas:
        db_session.refresh(escola)
    return escolas


@pytest.fixture
def sample_complemento_upload(db_session, sample_ano_letivo, sample_upload):
    """Cria um upload de complemento de exemplo"""
    from src.modules.features.complemento.models import ComplementoUpload
    # Criar um segundo upload para ser o upload_complemento_id
    from src.modules.features.uploads.models import Upload
    upload_complemento = Upload(
        ano_letivo_id=sample_ano_letivo.id,
        filename="complemento_upload.xlsx",
        total_escolas=2
    )
    db_session.add(upload_complemento)
    db_session.commit()
    db_session.refresh(upload_complemento)
    
    complemento_upload = ComplementoUpload(
        ano_letivo_id=sample_ano_letivo.id,
        filename="complemento_test.xlsx",
        upload_base_id=sample_upload.id,
        upload_complemento_id=upload_complemento.id,
        total_escolas_processadas=2,
        escolas_com_aumento=1,
        escolas_sem_mudanca=1,
        escolas_com_diminuicao=0,
        escolas_com_erro=0
    )
    db_session.add(complemento_upload)
    db_session.commit()
    db_session.refresh(complemento_upload)
    return complemento_upload


@pytest.fixture
def sample_complemento_escolas(db_session, sample_complemento_upload, sample_escolas):
    """Cria complementos de escola de exemplo"""
    from src.modules.features.complemento.models import ComplementoEscola, StatusComplemento
    complementos = [
        ComplementoEscola(
            complemento_upload_id=sample_complemento_upload.id,
            escola_id=sample_escolas[0].id,
            status=StatusComplemento.AUMENTO,
            total_alunos_antes=100,
            total_alunos_depois=150,
            total_alunos_diferenca=50,
            valor_complemento_total=5000.0,
            valor_complemento_gestao=1000.0,
            valor_complemento_merenda=2000.0,
            valor_complemento_kit_escolar=1000.0,
            valor_complemento_uniforme=500.0,
            valor_complemento_sala_recurso=500.0
        ),
        ComplementoEscola(
            complemento_upload_id=sample_complemento_upload.id,
            escola_id=sample_escolas[1].id,
            status=StatusComplemento.SEM_MUDANCA,
            total_alunos_antes=200,
            total_alunos_depois=200,
            total_alunos_diferenca=0,
            valor_complemento_total=0.0
        )
    ]
    for complemento in complementos:
        db_session.add(complemento)
    db_session.commit()
    for complemento in complementos:
        db_session.refresh(complemento)
    return complementos


@pytest.fixture
def sample_excel_file():
    """Cria um arquivo Excel de exemplo em memória"""
    data = {
        'nome_uex': ['Escola Teste 1', 'Escola Teste 2'],
        'dre': ['DRE-01', 'DRE-02'],
        'total_alunos': [150, 200],
        'fundamental_inicial': [50, 60],
        'fundamental_final': [50, 70],
        'fundamental_integral': [30, 40],
        'medio_regular': [20, 30]
    }
    df = pd.DataFrame(data)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    return buffer


@pytest.fixture
def sample_liberacao(db_session, sample_complemento_upload, sample_escolas):
    """Cria uma liberação de exemplo"""
    from src.modules.features.complemento.models import LiberacoesComplemento
    from datetime import datetime
    liberacao = LiberacoesComplemento(
        escola_id=sample_escolas[0].id,
        complemento_upload_id=sample_complemento_upload.id,
        liberada=True,
        numero_folha=1,
        data_liberacao=datetime.now()
    )
    db_session.add(liberacao)
    db_session.commit()
    db_session.refresh(liberacao)
    return liberacao
