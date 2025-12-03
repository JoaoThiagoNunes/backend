from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.logging_config import logger
from src.core.exceptions import DomainException
from src.modules.schemas.calculos import ResponseCalculos
from src.modules.features.calculos import CalculoService
from typing import Optional

calculo_router = APIRouter()


@calculo_router.get("", response_model=ResponseCalculos, tags=["Calculos"])
def listar_calculos(
    ano_letivo_id: Optional[int] = Query(None, description="ID do ano letivo (usa ano ativo se não informado)"),
    db: Session = Depends(get_db)
) -> ResponseCalculos:
    resultado = CalculoService.listar_calculos(db, ano_letivo_id)

    return ResponseCalculos(
        success=True,
        message=f"Cálculos do ano {resultado['ano_letivo'].ano}",
        total_escolas=len(resultado['escolas_calculadas']),
        valor_total_geral=resultado['valor_total_geral'],
        escolas=resultado['escolas_calculadas'],
        upload_id=resultado['upload_id'],
        ano_letivo_id=resultado['ano_letivo_id'],
    )


@calculo_router.post("", response_model=ResponseCalculos, tags=["Calculos"])
async def calcular_valores(
    ano_letivo_id: Optional[int] = Query(None, description="ID do ano letivo (usa ano ativo se não informado)"),
    db: Session = Depends(get_db)
):
    try:
        resultado = CalculoService.calcular_valores_para_ano(db, ano_letivo_id)
        
        return ResponseCalculos(
            success=True,
            message=f"Cálculos realizados para {len(resultado['escolas_calculadas'])} escolas do ano {resultado['ano_letivo'].ano}",
            total_escolas=len(resultado['escolas_calculadas']),
            valor_total_geral=resultado['valor_total_geral'],
            escolas=resultado['escolas_calculadas'],
            upload_id=resultado['upload_id'],
            ano_letivo_id=resultado['ano_letivo_id']
        )
        
    except (HTTPException, DomainException):
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Erro ao calcular valores")
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valores: {str(e)}")

