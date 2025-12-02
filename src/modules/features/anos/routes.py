from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.schemas.ano import *
from src.modules.features.anos import AnoLetivoService

ano_router = APIRouter()

@ano_router.get("", response_model=AnoLetivoListResponse, tags=["Anos"])
def listar_anos_letivos(db: Session = Depends(get_db)) -> AnoLetivoListResponse:
    anos = AnoLetivoService.listar_anos_letivos(db)
    return AnoLetivoListResponse(
        success=True,
        anos=anos
    )


@ano_router.post("", response_model=AnoLetivoCreateResponse, tags=["Anos"])
def criar_ano_letivo(data: AnoLetivoCreate, db: Session = Depends(get_db)) -> AnoLetivoCreateResponse:
    novo_ano = AnoLetivoService.criar_ano_letivo(db, data)
    
    return AnoLetivoCreateResponse(
        success=True,
        message=f"Ano letivo {data.ano} criado com sucesso",
        ano=AnoLetivoRead(
            id=novo_ano.id,
            ano=novo_ano.ano,
            status=novo_ano.status.value,
            created_at=novo_ano.created_at
        )
    )

@ano_router.put("/{ano_id}/arquivar", response_model=AnoLetivoArquivarResponse, tags=["Anos"])
def arquivar_ano_letivo(ano_id: int, db: Session = Depends(get_db)) -> AnoLetivoArquivarResponse:
    ano = AnoLetivoService.arquivar_ano_letivo(db, ano_id)
    
    return AnoLetivoArquivarResponse(
        success=True,
        message=f"Ano letivo {ano.ano} arquivado com sucesso",
        ano=AnoLetivoRead(
            id=ano.id,
            ano=ano.ano,
            status=ano.status.value,
            arquivado_em=ano.arquivado_em
        )
    )

@ano_router.delete("/{ano_id}", response_model=AnoLetivoDeleteResponse, tags=["Anos"])
def deletar_ano_letivo(ano_id: int, db: Session = Depends(get_db)) -> AnoLetivoDeleteResponse:
    ano_numero = AnoLetivoService.deletar_ano_letivo(db, ano_id)
    
    return AnoLetivoDeleteResponse(
        success=True,
        message=f"Ano letivo {ano_numero} e todos os dados relacionados foram deletados"
    )

