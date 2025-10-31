from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.schemas.ano import *
from src.modules.models import  AnoLetivo, StatusAnoLetivo
from datetime import datetime

router = APIRouter()

@router.get("/get-anos-letivos", tags=["Anos"])
def listar_anos_letivos(db: Session = Depends(get_db)):
    """Lista todos os anos letivos (ativos e arquivados)"""
    anos = db.query(AnoLetivo).order_by(AnoLetivo.ano.desc()).all()
    return {
        "success": True,
        "anos": [
            {
                "id": ano.id,
                "ano": ano.ano,
                "status": ano.status.value,
                "created_at": ano.created_at,
                "arquivado_em": ano.arquivado_em,
                "total_uploads": len(ano.uploads)
            }
            for ano in anos
        ]
    }

@router.get("/anos-letivos/ativo", tags=["Anos"])
def obter_ano_ativo(db: Session = Depends(get_db)):
    """Retorna o ano letivo ativo atual"""
    ano = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
    if not ano:
        raise HTTPException(status_code=404, detail="Nenhum ano letivo ativo encontrado")
    
    return {
        "success": True,
        "ano": {
            "id": ano.id,
            "ano": ano.ano,
            "status": ano.status.value,
            "created_at": ano.created_at,
            "total_uploads": len(ano.uploads)
        }
    }

@router.post("/anos-letivos", tags=["Anos"])
def criar_ano_letivo(data: AnoLetivoCreate, db: Session = Depends(get_db)):
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
    
    return {
        "success": True,
        "message": f"Ano letivo {data.ano} criado com sucesso",
        "ano": {
            "id": novo_ano.id,
            "ano": novo_ano.ano,
            "status": novo_ano.status.value,
            "created_at": novo_ano.created_at
        }
    }

@router.put("/anos-letivos/{ano_id}/arquivar", tags=["Anos"])
def arquivar_ano_letivo(ano_id: int, db: Session = Depends(get_db)):
    """Arquiva um ano letivo manualmente (requer admin)"""
    ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_id).first()
    if not ano:
        raise HTTPException(status_code=404, detail="Ano letivo não encontrado")
    
    if ano.status == StatusAnoLetivo.ARQUIVADO:
        raise HTTPException(status_code=400, detail="Ano letivo já está arquivado")
    
    ano.status = StatusAnoLetivo.ARQUIVADO
    ano.arquivado_em = datetime.now()
    db.commit()
    
    return {
        "success": True,
        "message": f"Ano letivo {ano.ano} arquivado com sucesso",
        "ano": {
            "id": ano.id,
            "ano": ano.ano,
            "status": ano.status.value,
            "arquivado_em": ano.arquivado_em
        }
    }

@router.delete("/anos-letivos/{ano_id}", tags=["Anos"])
def deletar_ano_letivo(ano_id: int, db: Session = Depends(get_db)):
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
    
    return {
        "success": True,
        "message": f"Ano letivo {ano_numero} e todos os dados relacionados foram deletados"
    }