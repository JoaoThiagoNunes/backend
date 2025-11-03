from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.schemas.ano import (
    AnoLetivoCreate, AnoLetivoRead, AnoLetivoListResponse,
    AnoLetivoDetailResponse, AnoLetivoCreateResponse,
    AnoLetivoArquivarResponse, AnoLetivoDeleteResponse
)
from src.modules.models import  AnoLetivo, StatusAnoLetivo
from datetime import datetime

router = APIRouter()

@router.get("", response_model=AnoLetivoListResponse, tags=["Anos"])
def listar_anos_letivos(db: Session = Depends(get_db)) -> AnoLetivoListResponse:
    """Lista todos os anos letivos (ativos e arquivados)"""
    anos = db.query(AnoLetivo).order_by(AnoLetivo.ano.desc()).all()
    return AnoLetivoListResponse(
        success=True,
        anos=[
            AnoLetivoRead(
                id=ano.id,
                ano=ano.ano,
                status=ano.status.value,
                created_at=ano.created_at,
                arquivado_em=ano.arquivado_em,
                total_uploads=len(ano.uploads)
            )
            for ano in anos
        ]
    )

@router.get("/ativo", response_model=AnoLetivoDetailResponse, tags=["Anos"])
def obter_ano_ativo(db: Session = Depends(get_db)) -> AnoLetivoDetailResponse:
    """Retorna o ano letivo ativo atual"""
    ano = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
    if not ano:
        raise HTTPException(status_code=404, detail="Nenhum ano letivo ativo encontrado")
    
    return AnoLetivoDetailResponse(
        success=True,
        ano=AnoLetivoRead(
            id=ano.id,
            ano=ano.ano,
            status=ano.status.value,
            created_at=ano.created_at,
            total_uploads=len(ano.uploads)
        )
    )

@router.post("", response_model=AnoLetivoCreateResponse, tags=["Anos"])
def criar_ano_letivo(data: AnoLetivoCreate, db: Session = Depends(get_db)) -> AnoLetivoCreateResponse:
    """
    Cria um novo ano letivo.
    Apenas um ano pode estar ATIVO por vez.
    """
    # Verificar se ano já existe
    ano_existente = db.query(AnoLetivo).filter(AnoLetivo.ano == data.ano).first()
    if ano_existente:
        raise HTTPException(status_code=400, detail=f"Ano letivo {data.ano} já existe")
    
    # Arquivar ano ativo atual (se houver)
    ano_ativo_atual = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
    if ano_ativo_atual:
        ano_ativo_atual.status = StatusAnoLetivo.ARQUIVADO
        ano_ativo_atual.arquivado_em = datetime.now()
    
    # Criar novo ano
    novo_ano = AnoLetivo(
        ano=data.ano,
        status=StatusAnoLetivo.ATIVO,
        created_at=datetime.now()
    )
    db.add(novo_ano)
    db.commit()
    db.refresh(novo_ano)
    
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

@router.put("/{ano_id}/arquivar", response_model=AnoLetivoArquivarResponse, tags=["Anos"])
def arquivar_ano_letivo(ano_id: int, db: Session = Depends(get_db)) -> AnoLetivoArquivarResponse:
    """Arquiva um ano letivo manualmente (requer admin)"""
    ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_id).first()
    if not ano:
        raise HTTPException(status_code=404, detail="Ano letivo não encontrado")
    
    if ano.status == StatusAnoLetivo.ARQUIVADO:
        raise HTTPException(status_code=400, detail="Ano letivo já está arquivado")
    
    ano.status = StatusAnoLetivo.ARQUIVADO
    ano.arquivado_em = datetime.now()
    db.commit()
    
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

@router.delete("/{ano_id}", response_model=AnoLetivoDeleteResponse, tags=["Anos"])
def deletar_ano_letivo(ano_id: int, db: Session = Depends(get_db)) -> AnoLetivoDeleteResponse:
    """
    Deleta um ano letivo (apenas admin).
    Nota: Anos são deletados automaticamente após 5 anos de arquivamento.
    """
    ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_id).first()
    if not ano:
        raise HTTPException(status_code=404, detail="Ano letivo não encontrado")
    
    ano_numero = ano.ano
    db.delete(ano)  # Cascade deleta tudo relacionado
    db.commit()
    
    return AnoLetivoDeleteResponse(
        success=True,
        message=f"Ano letivo {ano_numero} e todos os dados relacionados foram deletados"
    )