from datetime import datetime

from src.modules.features.anos.models import AnoLetivo
from src.modules.features.uploads.models import Upload
from src.modules.features.uploads.utils import obter_ou_criar_upload_ativo
from src.modules.features.complemento.models import ComplementoUpload


def test_substituicao_upload_base_nao_apaga_complemento_vinculado(db_session):
    ano = AnoLetivo(ano=2026)
    db_session.add(ano)
    db_session.commit()
    db_session.refresh(ano)

    # Dois uploads legados no mesmo ano (cenário de consolidação)
    upload_canonico = Upload(
        ano_letivo_id=ano.id,
        filename="base_atual.xlsx",
        upload_date=datetime.now(),
        total_escolas=0,
    )
    upload_extra = Upload(
        ano_letivo_id=ano.id,
        filename="base_antiga.xlsx",
        upload_date=datetime.now(),
        total_escolas=0,
    )
    db_session.add_all([upload_canonico, upload_extra])
    db_session.commit()
    db_session.refresh(upload_canonico)
    db_session.refresh(upload_extra)

    # Complemento legado ainda vinculado ao upload extra
    comp = ComplementoUpload(
        ano_letivo_id=ano.id,
        upload_base_id=upload_extra.id,
        upload_complemento_id=upload_extra.id,
        filename="comp.xlsx",
        upload_date=datetime.now(),
        total_escolas_processadas=0,
    )
    db_session.add(comp)
    db_session.commit()
    db_session.refresh(comp)

    # Ao substituir o upload ativo, o consolidator tentará remover o upload_extra
    # e deve remapear o complemento para o upload canônico em vez de apagar o registro.
    upload_result = obter_ou_criar_upload_ativo(db_session, ano.id, "novo_base.xlsx")
    db_session.commit()

    comp_after = db_session.query(ComplementoUpload).filter(ComplementoUpload.id == comp.id).first()
    assert comp_after is not None
    assert comp_after.upload_base_id == upload_result.id
    assert comp_after.upload_complemento_id == upload_result.id

