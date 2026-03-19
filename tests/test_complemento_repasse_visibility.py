from datetime import datetime

from src.modules.features.anos.models import AnoLetivo
from src.modules.features.uploads.models import Upload
from src.modules.features.escolas.models import Escola
from src.modules.features.complemento.models import (
    ComplementoUpload,
    ComplementoEscola,
    LiberacoesComplemento,
    StatusComplemento,
)
from src.modules.features.complemento.service import ComplementoService


def test_repasse_ignora_upload_base_ativo(db_session):
    """
    O repasse não deve depender do "upload base ativo". Ele deve montar o resumo
    diretamente a partir do complemento_upload_id informado.
    """
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
    upload_compl = Upload(
        ano_letivo_id=ano.id,
        filename="compl.xlsx",
        upload_date=datetime.now(),
        total_escolas=0,
    )
    db_session.add_all([upload_base, upload_compl])
    db_session.commit()
    db_session.refresh(upload_base)
    db_session.refresh(upload_compl)

    escola = Escola(
        upload_id=upload_base.id,
        nome_uex="Escola X",
        dre="DRE-01",
        total_alunos=100,
        cnpj="11111111000111",
    )
    db_session.add(escola)
    db_session.commit()
    db_session.refresh(escola)

    comp_upload = ComplementoUpload(
        ano_letivo_id=ano.id,
        upload_base_id=upload_base.id,
        upload_complemento_id=upload_compl.id,
        filename="comp_upload.xlsx",
        upload_date=datetime.now(),
        total_escolas_processadas=1,
    )
    db_session.add(comp_upload)
    db_session.commit()
    db_session.refresh(comp_upload)

    comp_escola = ComplementoEscola(
        complemento_upload_id=comp_upload.id,
        escola_id=escola.id,
        status=StatusComplemento.AUMENTO,
        total_alunos_antes=100,
        total_alunos_depois=120,
        total_alunos_diferenca=20,
        valor_complemento_total=5000.0,
        valor_complemento_gestao=5000.0,
        valor_complemento_kit_escolar=0.0,
        valor_complemento_uniforme=0.0,
        valor_complemento_merenda=0.0,
        valor_complemento_sala_recurso=0.0,
    )
    db_session.add(comp_escola)
    db_session.commit()
    db_session.refresh(comp_escola)

    lib = LiberacoesComplemento(
        escola_id=escola.id,
        complemento_upload_id=comp_upload.id,
        liberada=True,
        numero_folha=1,
        data_liberacao=datetime.now(),
    )
    db_session.add(lib)
    db_session.commit()

    resp = ComplementoService.obter_complementos_agrupados(
        db_session, ano_letivo_id=ano.id, complemento_upload_id=comp_upload.id
    )

    assert resp["success"] is True
    assert resp["total_escolas"] == 1
    assert resp["total_folhas"] == 1
    assert resp["folhas"][0].numero_folha == 1

