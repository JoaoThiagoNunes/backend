from typing import Optional, Tuple, Union
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.modules.features.anos import AnoLetivo, StatusAnoLetivo

def obter_ano_letivo(
    db: Session,
    ano_letivo_id: Optional[int] = None,
    raise_if_not_found: bool = True,
) -> Union[Tuple[AnoLetivo, int], Tuple[None, None]]:
    if ano_letivo_id is None:
        # Buscar ano letivo ativo
        ano_letivo = (
            db.query(AnoLetivo)
            .filter(AnoLetivo.status == StatusAnoLetivo.ATIVO)
            .first()
        )

        if not ano_letivo:
            if raise_if_not_found:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhum ano letivo ativo encontrado. Crie um ano primeiro.",
                )
            return None, None

        ano_letivo_id = ano_letivo.id
    else:
        # Buscar ano letivo por ID
        ano_letivo = (
            db.query(AnoLetivo)
            .filter(AnoLetivo.id == ano_letivo_id)
            .first()
        )

        if not ano_letivo:
            if raise_if_not_found:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ano letivo ID {ano_letivo_id} não encontrado",
                )
            return None, None

    return ano_letivo, ano_letivo_id


