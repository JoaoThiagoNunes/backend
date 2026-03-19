from io import BytesIO

import pandas as pd

from src.modules.features.anos.models import AnoLetivo
from src.modules.features.escolas.models import Escola
from src.modules.features.uploads.service import UploadService


def _excel_bytes(rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows)
    buf = BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.read()


def test_upload_persiste_e_retorna_novas_colunas_escolas(db_session):
    ano = AnoLetivo(ano=2026)
    db_session.add(ano)
    db_session.commit()
    db_session.refresh(ano)

    content = _excel_bytes(
        [
            {
                "NOME DA UEX": "Escola X",
                "DRE": "DRE-01",
                "CNPJ": "11111111000111",
                "TOTAL": 100,
                "FIC SENAC": 12,
                "ESPECIAL PROFISSIONALIZANTE PARCIAL": 7,
                "ESPECIAL PROFISSIONALIZANTE INTEGRADO": 5,
            }
        ]
    )

    result = UploadService.processar_planilha_excel(db_session, content, "novas_colunas.xlsx", ano.id)
    assert result["upload_id"] is not None

    escola = db_session.query(Escola).filter(Escola.cnpj == "11111111000111").first()
    assert escola is not None
    assert escola.fic_senac == 12
    assert escola.especial_profissionalizante_parcial == 7
    assert escola.especial_profissionalizante_integrado == 5

    detalhe = UploadService.obter_upload_detalhado(db_session, ano_letivo_id=ano.id)
    assert len(detalhe["escolas"]) == 1
    dados = detalhe["escolas"][0].dados_planilha
    assert dados["fic_senac"] == 12
    assert dados["especial_profissionalizante_parcial"] == 7
    assert dados["especial_profissionalizante_integrado"] == 5

