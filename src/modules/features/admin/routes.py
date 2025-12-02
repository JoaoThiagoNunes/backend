from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.logging_config import logger
from src.core.auth import authenticate_admin, create_access_token, get_current_admin
from src.modules.schemas.admin import *
from src.modules.features.anos import AnoLetivo
from typing import  Optional


admin_router = APIRouter()

@admin_router.get("/", response_model=RootResponse, tags=["Admin"])
def read_root() -> RootResponse:
    return RootResponse(
        message="API funcionando!"
    )


@admin_router.post("/login", response_model=LoginResponse, tags=["Admin"])
def login(login_data: LoginRequest):
    if authenticate_admin(login_data.password):
        access_token = create_access_token(data={"sub": "admin", "role": "admin"})
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            message="Login realizado com sucesso"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta",
            headers={"WWW-Authenticate": "Bearer"},
        )


@admin_router.delete("/limpar-dados", response_model=LimparDadosResponse, tags=["Admin"])
def limpar_todos_dados(
    ano_letivo_id: Optional[int] = Query(None, description="Limpar apenas um ano específico"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin) 
) -> LimparDadosResponse:
    try:
        if ano_letivo_id:
            # Limpar apenas um ano específico
            ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_letivo_id).first()
            if not ano:
                raise HTTPException(status_code=404, detail="Ano letivo não encontrado")
            
            id_ano = ano.ano
            db.delete(ano)  # Cascade deleta tudo relacionado
            db.commit()  # Transação padronizada: commit único após todas as operações
            logger.warning(f"Ano letivo {id_ano} e todos os dados relacionados foram removidos")
            
            return LimparDadosResponse(
                success=True,
                message=f"Ano letivo {id_ano} e todos os dados relacionados foram removidos"
            )
        else:
            # Limpar TUDO 
            anos = db.query(AnoLetivo).all()
            count = len(anos)
            for ano in anos:
                db.delete(ano)
            db.commit()
            logger.warning(f"TODOS os dados foram removidos ({count} ano(s))")
            
            return LimparDadosResponse(
                success=True,
                message=f"{count} ano(s) letivo(s) e TODOS os dados foram removidos"
            )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar dados: {str(e)}")

