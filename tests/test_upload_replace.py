from io import BytesIO

import pandas as pd

from src.modules.features.anos.models import AnoLetivo
from src.modules.features.uploads.models import Upload
from src.modules.features.escolas.models import Escola
from src.modules.features.parcelas.models import LiberacoesParcela
from src.modules.features.uploads.service import UploadService


def _excel_bytes(rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows)
    buf = BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.read()


def test_same_year_upload_is_replaced_and_releases_preserved(db_session):
    # Arrange: ano letivo
    ano = AnoLetivo(ano=2026)
    db_session.add(ano)
    db_session.commit()
    db_session.refresh(ano)

    # Upload 1
    content1 = _excel_bytes(
        [
            {
                "NOME DA UEX": "Escola A",
                "DRE": "DRE-01",
                "CNPJ": "12.345.678/0001-90",
                "TOTAL": 100,
            }
        ]
    )
    r1 = UploadService.processar_planilha_excel(db_session, content1, "u1.xlsx", ano.id)
    assert r1["upload_id"] is not None

    uploads_ano = db_session.query(Upload).filter(Upload.ano_letivo_id == ano.id).all()
    assert len(uploads_ano) == 1
    upload_id = uploads_ano[0].id

    escola = (
        db_session.query(Escola)
        .filter(Escola.upload_id == upload_id, Escola.cnpj == "12.345.678/0001-90")
        .first()
    )
    assert escola is not None
    escola_id = escola.id
    assert escola.total_alunos == 100

    # Criar liberação da parcela 1 para a escola
    lib = LiberacoesParcela(escola_id=escola_id, numero_parcela=1, liberada=True)
    db_session.add(lib)
    db_session.commit()

    # Act: Upload 2 no mesmo ano (substituição), com novos alunos
    content2 = _excel_bytes(
        [
            {
                "NOME DA UEX": "Escola A (nome pode mudar)",
                "DRE": "DRE-01",
                "CNPJ": "12345678000190",  # formato diferente; mesma escola via CNPJ normalizado
                "TOTAL": 150,
            }
        ]
    )
    r2 = UploadService.processar_planilha_excel(db_session, content2, "u2.xlsx", ano.id)
    assert r2["upload_id"] == upload_id  # mesmo upload (não acumula)

    uploads_ano_2 = db_session.query(Upload).filter(Upload.ano_letivo_id == ano.id).all()
    assert len(uploads_ano_2) == 1

    escola2 = db_session.query(Escola).filter(Escola.id == escola_id).first()
    assert escola2 is not None
    assert escola2.total_alunos == 150  # atualizado

    # Liberação deve permanecer (não pode ser perdida)
    lib2 = (
        db_session.query(LiberacoesParcela)
        .filter(LiberacoesParcela.escola_id == escola_id, LiberacoesParcela.numero_parcela == 1)
        .first()
    )
    assert lib2 is not None
    assert lib2.liberada is True


def test_different_year_creates_new_upload(db_session):
    # Arrange: dois anos
    ano1 = AnoLetivo(ano=2026)
    ano2 = AnoLetivo(ano=2027)
    db_session.add_all([ano1, ano2])
    db_session.commit()
    db_session.refresh(ano1)
    db_session.refresh(ano2)

    content = _excel_bytes(
        [
            {"NOME DA UEX": "Escola A", "DRE": "DRE-01", "CNPJ": "11111111000111", "TOTAL": 10},
        ]
    )

    UploadService.processar_planilha_excel(db_session, content, "a1.xlsx", ano1.id)
    UploadService.processar_planilha_excel(db_session, content, "a2.xlsx", ano2.id)

    uploads_ano1 = db_session.query(Upload).filter(Upload.ano_letivo_id == ano1.id).all()
    uploads_ano2 = db_session.query(Upload).filter(Upload.ano_letivo_id == ano2.id).all()
    assert len(uploads_ano1) == 1
    assert len(uploads_ano2) == 1
    assert uploads_ano1[0].id != uploads_ano2[0].id

