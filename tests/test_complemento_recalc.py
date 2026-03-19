from io import BytesIO
from datetime import datetime

import pandas as pd

from src.modules.features.anos.models import AnoLetivo
from src.modules.features.uploads.models import Upload
from src.modules.features.escolas.models import Escola
from src.modules.features.complemento.models import LiberacoesComplemento
from src.modules.features.complemento.service import ComplementoService


def _excel_bytes(rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows)
    buf = BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.read()


def test_complemento_recalc_preserves_releases(db_session):
    # Arrange: ano letivo e upload base com 1 escola
    ano = AnoLetivo(ano=2026)
    db_session.add(ano)
    db_session.commit()
    db_session.refresh(ano)

    upload_base = Upload(
        ano_letivo_id=ano.id,
        filename="base.xlsx",
        upload_date=datetime.now(),
        total_escolas=1,
    )
    db_session.add(upload_base)
    db_session.commit()
    db_session.refresh(upload_base)

    escola = Escola(
        upload_id=upload_base.id,
        nome_uex="Escola Complemento",
        dre="DRE-01",
        total_alunos=100,
    )
    db_session.add(escola)
    db_session.commit()
    db_session.refresh(escola)

    # Primeiro complemento: aumento simples
    content1 = _excel_bytes(
        [
            {
                "NOME DA UEX": "Escola Complemento",
                "DRE": "DRE-01",
                "TOTAL": 120,
            }
        ]
    )
    r1 = ComplementoService.processar_planilha_complemento(
        db_session, content1, "comp1.xlsx", ano_letivo_id=ano.id, upload_base_id=upload_base.id
    )
    comp_id_1 = r1["complemento_upload_id"]

    # Liberação vinculada ao primeiro complemento
    lib1 = LiberacoesComplemento(
        escola_id=escola.id,
        complemento_upload_id=comp_id_1,
        liberada=True,
        numero_folha=1,
        data_liberacao=datetime.now(),
    )
    db_session.add(lib1)
    db_session.commit()

    # Segundo complemento (reprocessar) com outro TOTAL
    content2 = _excel_bytes(
        [
            {
                "NOME DA UEX": "Escola Complemento",
                "DRE": "DRE-01",
                "TOTAL": 130,
            }
        ]
    )
    r2 = ComplementoService.processar_planilha_complemento(
        db_session, content2, "comp2.xlsx", ano_letivo_id=ano.id, upload_base_id=upload_base.id
    )
    comp_id_2 = r2["complemento_upload_id"]

    # Assert: existe apenas 1 ComplementoUpload ativo para o ano (substituição)
    from src.modules.features.complemento.models import ComplementoUpload

    uploads_comp = (
        db_session.query(ComplementoUpload)
        .filter(ComplementoUpload.ano_letivo_id == ano.id)
        .all()
    )
    assert len(uploads_comp) == 1
    assert uploads_comp[0].id == comp_id_2

    # Liberação antiga foi migrada para o novo complemento (não deve ficar vinculada ao antigo)
    lib_nova = (
        db_session.query(LiberacoesComplemento)
        .filter(
            LiberacoesComplemento.escola_id == escola.id,
            LiberacoesComplemento.complemento_upload_id == comp_id_2,
        )
        .first()
    )
    assert lib_nova is not None
    assert lib_nova.liberada is True
    assert lib_nova.numero_folha == 1

    # Não deve existir liberação pendurada no complemento antigo
    lib_antiga = (
        db_session.query(LiberacoesComplemento)
        .filter(
            LiberacoesComplemento.escola_id == escola.id,
            LiberacoesComplemento.complemento_upload_id == comp_id_1,
        )
        .first()
    )
    assert lib_antiga is None

