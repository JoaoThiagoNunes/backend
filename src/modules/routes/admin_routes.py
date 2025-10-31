from fastapi import APIRouter, Depends, HTTPException, HTTPException, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.models import  *
from typing import  Optional


router = APIRouter()

@router.get("/", tags=["Admin"])
def read_root():
    return {"message": "API funcionando!", "versao": "2.0 - Com Anos Letivos"}



@router.delete("/limpar-dados", tags=["Admin"])
def limpar_todos_dados(
    ano_letivo_id: Optional[int] = Query(None, description="Limpar apenas um ano específico"),
    db: Session = Depends(get_db)
):
    """
    CUIDADO: Apaga dados do banco.
    Se ano_letivo_id fornecido: apaga apenas aquele ano.
    Se não fornecido: apaga TUDO.
    """
    try:
        if ano_letivo_id:
            # Limpar apenas um ano específico
            ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_letivo_id).first()
            if not ano:
                raise HTTPException(status_code=404, detail="Ano letivo não encontrado")
            
            ano_numero = ano.ano
            db.delete(ano)  # Cascade deleta tudo relacionado
            db.commit()
            
            return {
                "success": True,
                "message": f"✅ Ano letivo {ano_numero} e todos os dados relacionados foram removidos"
            }
        else:
            # Limpar TUDO
            anos = db.query(AnoLetivo).all()
            count = len(anos)
            for ano in anos:
                db.delete(ano)
            db.commit()
            
            return {
                "success": True,
                "message": f"✅ {count} ano(s) letivo(s) e TODOS os dados foram removidos"
            }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar dados: {str(e)}")

@router.get("/status-dados", tags=["Admin"])
def status_dados(db: Session = Depends(get_db)):
    """Retorna estatísticas gerais do banco de dados"""
    total_anos = db.query(AnoLetivo).count()
    total_uploads = db.query(Upload).count()
    total_escolas = db.query(Escola).count()
    total_calculos = db.query(CalculosProfin).count()
    
    ano_ativo = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
    
    anos_lista = []
    for ano in db.query(AnoLetivo).order_by(AnoLetivo.ano.desc()).all():
        uploads_count = len(ano.uploads)
        escolas_count = sum([len(up.escolas) for up in ano.uploads])
        
        anos_lista.append({
            "id": ano.id,
            "ano": ano.ano,
            "status": ano.status.value,
            "uploads": uploads_count,
            "escolas": escolas_count,
            "created_at": ano.created_at,
            "arquivado_em": ano.arquivado_em
        })
    
    return {
        "success": True,
        "resumo": {
            "total_anos_letivos": total_anos,
            "total_uploads": total_uploads,
            "total_escolas": total_escolas,
            "total_calculos": total_calculos
        },
        "ano_ativo": {
            "id": ano_ativo.id,
            "ano": ano_ativo.ano,
            "status": ano_ativo.status.value
        } if ano_ativo else None,
        "anos": anos_lista
    }

@router.get("/health", tags=["Admin"])
def health_check():
    return {
        "status": "healthy",
        "versao": "2.0",
        "features": ["anos_letivos", "arquivamento_automatico", "isolamento_por_ano"]
    }
        