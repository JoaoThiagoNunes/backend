from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from src.core.database import get_db
from src.core.logging_config import logger
from src.core.auth import authenticate_admin, create_access_token, get_current_admin
from src.modules.schemas.auth import LoginRequest, LoginResponse
from src.modules.schemas.admin import (
    RootResponse, LimparDadosResponse, StatusDadosResponse,
    HealthCheckResponse, ResumoDados, AnoAtivoInfo, AnoStatusInfo
)
from src.modules.models import  *
from typing import  Optional


router = APIRouter()

@router.get("/", response_model=RootResponse, tags=["Admin"])
def read_root() -> RootResponse:
    """Endpoint raiz da API"""
    return RootResponse(
        message="API funcionando!",
        versao="2.0 - Com Anos Letivos"
    )


@router.post("/login", response_model=LoginResponse, tags=["Admin"])
def login(login_data: LoginRequest):
    """
    Endpoint de autenticação.
    
    Recebe a senha e retorna um token JWT válido por 24 horas.
    Use este token no header 'Authorization: Bearer <token>' para acessar endpoints protegidos.
    
    Senha padrão: profin2024 (pode ser alterada via variável de ambiente ADMIN_PASSWORD)
    """
    if authenticate_admin(login_data.password):
        # Criar token JWT
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


@router.delete("/limpar-dados", response_model=LimparDadosResponse, tags=["Admin"])
def limpar_todos_dados(
    ano_letivo_id: Optional[int] = Query(None, description="Limpar apenas um ano específico"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)  # Proteção: requer autenticação
) -> LimparDadosResponse:
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
            db.commit()  # Transação padronizada: commit único após todas as operações
            logger.warning(f"⚠️ Ano letivo {ano_numero} e todos os dados relacionados foram removidos")
            
            return LimparDadosResponse(
                success=True,
                message=f"✅ Ano letivo {ano_numero} e todos os dados relacionados foram removidos"
            )
        else:
            # Limpar TUDO (transação padronizada: commit único)
            anos = db.query(AnoLetivo).all()
            count = len(anos)
            for ano in anos:
                db.delete(ano)
            db.commit()
            logger.warning(f"⚠️ TODOS os dados foram removidos ({count} ano(s))")
            
            return LimparDadosResponse(
                success=True,
                message=f"✅ {count} ano(s) letivo(s) e TODOS os dados foram removidos"
            )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar dados: {str(e)}")

@router.get("/status-dados", response_model=StatusDadosResponse, tags=["Admin"])
def status_dados(db: Session = Depends(get_db)) -> StatusDadosResponse:
    """Retorna estatísticas gerais do banco de dados"""
    total_anos = db.query(AnoLetivo).count()
    total_uploads = db.query(Upload).count()
    total_escolas = db.query(Escola).count()
    total_calculos = db.query(CalculosProfin).count()
    
    ano_ativo = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
    
    # Otimização: usar eager loading para evitar queries N+1
    # Carrega anos com uploads e escolas em uma única query
    anos = db.query(AnoLetivo)\
        .options(
            joinedload(AnoLetivo.uploads).joinedload(Upload.escolas)
        )\
        .order_by(AnoLetivo.ano.desc())\
        .all()
    
    anos_lista = [
        AnoStatusInfo(
            id=ano.id,
            ano=ano.ano,
            status=ano.status.value,
            uploads=len(ano.uploads),
            escolas=sum(len(up.escolas) for up in ano.uploads),
            created_at=ano.created_at,
            arquivado_em=ano.arquivado_em
        )
        for ano in anos
    ]
    
    return StatusDadosResponse(
        success=True,
        resumo=ResumoDados(
            total_anos_letivos=total_anos,
            total_uploads=total_uploads,
            total_escolas=total_escolas,
            total_calculos=total_calculos
        ),
        ano_ativo=AnoAtivoInfo(
            id=ano_ativo.id,
            ano=ano_ativo.ano,
            status=ano_ativo.status.value
        ) if ano_ativo else None,
        anos=anos_lista
    )

@router.get("/health", response_model=HealthCheckResponse, tags=["Admin"])
def health_check() -> HealthCheckResponse:
    """Health check da API"""
    return HealthCheckResponse(
        status="healthy",
        versao="2.0",
        features=["anos_letivos", "arquivamento_automatico", "isolamento_por_ano"]
    )
        