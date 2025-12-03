from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.core.database import get_db
from src.core.logging_config import logger
from src.core.exceptions import DomainException
from src.modules.features.projetos import ProjetoService
from src.modules.schemas.parcelas import RepasseResumoResponse
from src.modules.schemas.projetos import (
    LiberarProjetosRequest,
    LiberarProjetosResponse,
    ListarLiberacoesProjetosResponse,
    AtualizarLiberacaoProjetoRequest,
    LiberacaoProjetoResponse,
)


projeto_router = APIRouter()


@projeto_router.get("", response_model=RepasseResumoResponse, tags=["Projetos"])
def obter_projetos(
    ano_letivo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> RepasseResumoResponse:
    try:
        return ProjetoService.obter_projetos_agrupados(db, ano_letivo_id)
    except (HTTPException, DomainException):
        raise
    except Exception as e:
        logger.exception("Erro ao obter dados de projetos")
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados de projetos: {str(e)}")


@projeto_router.post("/liberacoes", response_model=LiberarProjetosResponse, tags=["Projetos"])
def liberar_escolas_projetos(
    request: LiberarProjetosRequest,
    db: Session = Depends(get_db),
) -> LiberarProjetosResponse:
    try:
        if not request.escola_ids:
            raise HTTPException(status_code=400, detail="Informe ao menos uma escola para liberar")

        if request.numero_folha <= 0:
            raise HTTPException(
                status_code=400,
                detail="numero_folha deve ser um inteiro maior ou igual a 1",
            )

        liberacoes_info = ProjetoService.liberar_escolas_projetos(
            db, request.escola_ids, request.numero_folha
        )

        return LiberarProjetosResponse(
            success=True,
            message=(
                f"{len(liberacoes_info)} escola(s) liberada(s) para projetos na folha "
                f"{request.numero_folha}"
            ),
            total_escolas_atualizadas=len(liberacoes_info),
            numero_folha=request.numero_folha,
            liberacoes=liberacoes_info,
        )

    except (HTTPException, DomainException):
        raise
    except Exception as e:
        logger.exception("Erro ao liberar escolas em projetos")
        raise HTTPException(status_code=500, detail=f"Erro ao liberar projetos: {str(e)}")


@projeto_router.get("/liberacoes", response_model=ListarLiberacoesProjetosResponse, tags=["Projetos"])
def listar_liberacoes_projetos(
    numero_folha: Optional[int] = Query(None),
    liberada: Optional[bool] = Query(None),
    escola_id: Optional[int] = Query(None),
    ano_letivo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> ListarLiberacoesProjetosResponse:
    try:
        if numero_folha is not None and numero_folha <= 0:
            raise HTTPException(status_code=400, detail="numero_folha deve ser maior que 0")

        liberacoes_info = ProjetoService.listar_liberacoes_projetos(
            db, numero_folha, liberada, escola_id, ano_letivo_id
        )

        return ListarLiberacoesProjetosResponse(
            success=True,
            total=len(liberacoes_info),
            liberacoes=liberacoes_info,
        )

    except (HTTPException, DomainException):
        raise
    except Exception as e:
        logger.exception("Erro ao listar liberações de projetos")
        raise HTTPException(status_code=500, detail=f"Erro ao listar liberações: {str(e)}")


@projeto_router.put("/liberacoes/{liberacao_id}", response_model=LiberacaoProjetoResponse, tags=["Projetos"])
def atualizar_liberacao_projetos(
    liberacao_id: int,
    request: AtualizarLiberacaoProjetoRequest,
    db: Session = Depends(get_db),
) -> LiberacaoProjetoResponse:
    try:
        dados = request.model_dump(exclude_unset=True)
        if not dados:
            raise HTTPException(status_code=400, detail="Nenhum campo fornecido para atualização")

        liberacao_info = ProjetoService.atualizar_liberacao_projeto(
            db,
            liberacao_id,
            numero_folha=dados.get("numero_folha"),
            liberada=dados.get("liberada"),
            data_liberacao=dados.get("data_liberacao"),
        )

        return LiberacaoProjetoResponse(
            success=True,
            message="Liberação de projetos atualizada com sucesso",
            liberacao=liberacao_info,
        )

    except (HTTPException, DomainException):
        raise
    except Exception as e:
        logger.exception("Erro ao atualizar liberação de projetos")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar liberação: {str(e)}")


@projeto_router.delete("/liberacoes/{liberacao_id}", response_model=LiberacaoProjetoResponse, tags=["Projetos"])
def remover_liberacao_projetos(
    liberacao_id: int,
    db: Session = Depends(get_db),
) -> LiberacaoProjetoResponse:
    try:
        liberacao_info = ProjetoService.remover_liberacao_projeto(db, liberacao_id)

        return LiberacaoProjetoResponse(
            success=True,
            message="Liberação de projetos resetada com sucesso",
            liberacao=liberacao_info,
        )

    except (HTTPException, DomainException):
        raise
    except Exception as e:
        logger.exception("Erro ao remover liberação de projetos")
        raise HTTPException(status_code=500, detail=f"Erro ao remover liberação: {str(e)}")


@projeto_router.get(
    "/liberacoes/escola/{escola_id}",
    response_model=ListarLiberacoesProjetosResponse,
    tags=["Projetos"],
)
def listar_liberacoes_projetos_por_escola(
    escola_id: int,
    db: Session = Depends(get_db),
) -> ListarLiberacoesProjetosResponse:
    try:
        liberacoes_info = ProjetoService.listar_liberacoes_projetos(db, escola_id=escola_id)

        return ListarLiberacoesProjetosResponse(
            success=True,
            total=len(liberacoes_info),
            liberacoes=liberacoes_info,
        )

    except (HTTPException, DomainException):
        raise
    except Exception as e:
        logger.exception("Erro ao listar liberações de projetos por escola")
        raise HTTPException(status_code=500, detail=f"Erro ao listar liberações: {str(e)}")


@projeto_router.get(
    "/liberacoes/folha/{numero_folha}",
    response_model=ListarLiberacoesProjetosResponse,
    tags=["Projetos"],
)
def listar_liberacoes_projetos_por_folha(
    numero_folha: int,
    db: Session = Depends(get_db),
) -> ListarLiberacoesProjetosResponse:
    try:
        if numero_folha <= 0:
            raise HTTPException(status_code=400, detail="numero_folha deve ser maior que 0")

        liberacoes_info = ProjetoService.listar_liberacoes_projetos(
            db, numero_folha=numero_folha, liberada=True
        )

        return ListarLiberacoesProjetosResponse(
            success=True,
            total=len(liberacoes_info),
            liberacoes=liberacoes_info,
        )

    except (HTTPException, DomainException):
        raise
    except Exception as e:
        logger.exception("Erro ao listar liberações de projetos por folha")
        raise HTTPException(status_code=500, detail=f"Erro ao listar liberações: {str(e)}")

