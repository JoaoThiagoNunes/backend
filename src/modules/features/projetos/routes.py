from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Dict, List, Optional, Set

from src.core.database import get_db
from src.core.logging_config import logger
from src.core.utils import obter_ano_letivo
from src.modules.features.escolas import Escola
from src.modules.features.uploads import Upload
from src.modules.features.projetos import LiberacoesProjeto, ProjetoService
from src.modules.schemas.parcelas import (
    RepasseResumoResponse,
    RepasseFolhaInfo,
    EscolaPrevisaoInfo,
)
from src.modules.schemas.projetos import (
    LiberarProjetosRequest,
    LiberarProjetosResponse,
    ListarLiberacoesProjetosResponse,
    AtualizarLiberacaoProjetoRequest,
    LiberacaoProjetoResponse,
    LiberacaoProjetoInfo,
)


projeto_router = APIRouter()


def _mapear_liberacao_projeto(liberacao: LiberacoesProjeto) -> LiberacaoProjetoInfo:
    escola = liberacao.escola

    return LiberacaoProjetoInfo(
        id=liberacao.id,
        escola_id=escola.id if escola else liberacao.escola_id,
        nome_uex=escola.nome_uex if escola else "",
        dre=escola.dre if escola else None,
        liberada=liberacao.liberada,
        numero_folha=liberacao.numero_folha,
        data_liberacao=liberacao.data_liberacao,
        valor_projetos_aprovados=liberacao.valor_projetos_aprovados,
        created_at=liberacao.created_at,
        updated_at=liberacao.updated_at,
    )


@projeto_router.get("", response_model=RepasseResumoResponse, tags=["Projetos"])
def obter_projetos(
    ano_letivo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> RepasseResumoResponse:
    try:
        _, ano_id = obter_ano_letivo(db, ano_letivo_id)

        escolas = (
            db.query(Escola)
            .join(Upload, Escola.upload_id == Upload.id)
            .filter(Upload.ano_letivo_id == ano_id)
            .options(
                joinedload(Escola.calculos),
                joinedload(Escola.liberacoes_projetos)
            )
            .all()
        )

        if not escolas:
            return RepasseResumoResponse(
                success=True,
                total_parcelas=0,
                total_folhas=0,
                total_escolas=0,
                valor_total_reais=0.0,
                folhas=[],
            )

        agrupado: Dict[int, Dict[Optional[int], List[EscolaPrevisaoInfo]]] = {}
        # Rastrear escolas já adicionadas por folha para evitar duplicatas
        escolas_por_folha: Dict[int, Dict[Optional[int], Set[int]]] = {}
        liberacoes_atualizadas = False

        for escola in escolas:
            quantidade_direito = ProjetoService.obter_quantidade_direito_projeto(escola.calculos)
            quantidade_planilha = max(escola.quantidade_projetos_aprovados or 0, 0)
            valor_projetos_calculado = ProjetoService.calcular_valor_projetos_aprovados(escola, escola.calculos)
            
            # Calcula a quantidade a pagar (menor entre direito e planilha)
            if quantidade_direito > 0:
                quantidade_projetos_a_pagar = min(quantidade_planilha, quantidade_direito)
            else:
                quantidade_projetos_a_pagar = 0

            if not escola.calculos:
                logger.info(
                    "Escola %s (%s) ainda não possui cálculos gerados; usando valor_projetos_calculado=%.2f",
                    escola.id,
                    escola.nome_uex,
                    valor_projetos_calculado,
                )

            # Projetos não têm parcelas, sempre usar parcela = 1 para compatibilidade com schema
            parcela = 1

            # Uma escola tem apenas uma liberação de projetos (relacionamento one-to-one)
            liberacao_projeto: Optional[LiberacoesProjeto] = escola.liberacoes_projetos if escola.liberacoes_projetos else None

            # Se existir liberação, sincronizar o valor salvo com o valor calculado
            if liberacao_projeto:
                if abs((liberacao_projeto.valor_projetos_aprovados or 0.0) - valor_projetos_calculado) > 0.009:
                    liberacao_projeto.valor_projetos_aprovados = valor_projetos_calculado
                    liberacoes_atualizadas = True
                valor_projeto = valor_projetos_calculado
                liberada = liberacao_projeto.liberada
                folha = liberacao_projeto.numero_folha if liberacao_projeto.numero_folha is not None else None
            else:
                liberada = False
                folha = None
                valor_projeto = valor_projetos_calculado

            # Inicializar estruturas se necessário
            if parcela not in agrupado:
                agrupado[parcela] = {}
                escolas_por_folha[parcela] = {}
            if folha not in agrupado[parcela]:
                agrupado[parcela][folha] = []
                escolas_por_folha[parcela][folha] = set()

            # Verificar se a escola já foi adicionada nesta folha
            if escola.id in escolas_por_folha[parcela][folha]:
                continue

            # Marcar escola como adicionada
            escolas_por_folha[parcela][folha].add(escola.id)

            info = EscolaPrevisaoInfo(
                escola_id=escola.id,
                nome_uex=escola.nome_uex,
                dre=escola.dre,
                numero_parcela=parcela,
                liberada=liberada,
                numero_folha=folha,
                valor_total_reais=round(valor_projeto, 2),
                quantidade_projetos_aprovados=escola.quantidade_projetos_aprovados,
                quantidade_projetos_a_pagar=quantidade_projetos_a_pagar,
            )

            agrupado[parcela][folha].append(info)

        if liberacoes_atualizadas:
            db.commit()

        if not agrupado:
            return RepasseResumoResponse(
                success=True,
                total_parcelas=0,
                total_folhas=0,
                total_escolas=0,
                valor_total_reais=0.0,
                folhas=[],
            )

        folhas_info: List[RepasseFolhaInfo] = []
        total_valor = 0.0
        total_escolas = 0

        for parcela, folhas in sorted(agrupado.items()):
            for folha, infos_escola in sorted(
                folhas.items(),
                key=lambda item: (
                    item[0] is None,
                    item[0] if item[0] is not None else 0,
                ),
            ):
                if not infos_escola:
                    continue

                valor_folha = sum(info.valor_total_reais for info in infos_escola)
                total_escolas += len(infos_escola)
                total_valor += valor_folha

                folhas_info.append(
                    RepasseFolhaInfo(
                        numero_parcela=parcela,
                        numero_folha=folha,
                        total_escolas=len(infos_escola),
                        valor_total_reais=round(valor_folha, 2),
                        escolas=infos_escola,
                    )
                )

        if not folhas_info:
            return RepasseResumoResponse(
                success=True,
                total_parcelas=0,
                total_folhas=0,
                total_escolas=0,
                valor_total_reais=0.0,
                folhas=[],
            )

        return RepasseResumoResponse(
            success=True,
            total_parcelas=len(agrupado),
            total_folhas=len(folhas_info),
            total_escolas=total_escolas,
            valor_total_reais=round(total_valor, 2),
            folhas=folhas_info,
        )

    except HTTPException:
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

        escola_ids_unicos = list(dict.fromkeys(request.escola_ids))

        escolas = (
            db.query(Escola)
            .options(joinedload(Escola.calculos))
            .filter(Escola.id.in_(escola_ids_unicos))
            .all()
        )

        if len(escolas) != len(escola_ids_unicos):
            ids_encontrados = {escola.id for escola in escolas}
            ids_invalidos = [eid for eid in escola_ids_unicos if eid not in ids_encontrados]
            raise HTTPException(
                status_code=404,
                detail=f"Escolas não encontradas: {ids_invalidos}",
            )

        liberacoes_existentes = (
            db.query(LiberacoesProjeto)
            .filter(
                LiberacoesProjeto.escola_id.in_(escola_ids_unicos),
            )
            .all()
        )

        mapa_liberacoes: Dict[int, LiberacoesProjeto] = {
            liberacao.escola_id: liberacao for liberacao in liberacoes_existentes
        }

        agora = datetime.now()
        liberacoes_resultado: List[LiberacoesProjeto] = []

        for escola in escolas:
            liberacao = mapa_liberacoes.get(escola.id)
            valor_projetos_calculado = ProjetoService.calcular_valor_projetos_aprovados(escola, escola.calculos)

            if liberacao:
                liberacao.liberada = True
                liberacao.numero_folha = request.numero_folha
                liberacao.data_liberacao = agora
                liberacao.valor_projetos_aprovados = valor_projetos_calculado
            else:
                liberacao = LiberacoesProjeto(
                    escola_id=escola.id,
                    liberada=True,
                    numero_folha=request.numero_folha,
                    data_liberacao=agora,
                )
                liberacao.valor_projetos_aprovados = valor_projetos_calculado
                db.add(liberacao)
                mapa_liberacoes[escola.id] = liberacao

            liberacao.escola = escola
            liberacoes_resultado.append(liberacao)

        db.commit()

        liberacoes_ids = [lib.id for lib in liberacoes_resultado]
        liberacoes_atualizadas = (
            db.query(LiberacoesProjeto)
            .options(joinedload(LiberacoesProjeto.escola))
            .filter(LiberacoesProjeto.id.in_(liberacoes_ids))
            .all()
        )

        liberacoes_map: Dict[int, LiberacoesProjeto] = {
            liberacao.id: liberacao for liberacao in liberacoes_atualizadas
        }
        liberacoes_info = [
            _mapear_liberacao_projeto(liberacoes_map[lib.id]) for lib in liberacoes_resultado
        ]

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

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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

        ano_id: Optional[int] = None
        if ano_letivo_id is not None:
            _, ano_id = obter_ano_letivo(db, ano_letivo_id)

        query = db.query(LiberacoesProjeto).join(Escola)

        if ano_id is not None:
            query = query.join(Upload, Escola.upload_id == Upload.id)
            query = query.filter(Upload.ano_letivo_id == ano_id)

        if numero_folha is not None:
            query = query.filter(LiberacoesProjeto.numero_folha == numero_folha)

        if liberada is not None:
            query = query.filter(LiberacoesProjeto.liberada == liberada)

        if escola_id is not None:
            query = query.filter(LiberacoesProjeto.escola_id == escola_id)

        liberacoes = (
            query.options(joinedload(LiberacoesProjeto.escola))
            .order_by(
                LiberacoesProjeto.numero_folha.nulls_last(),
                Escola.nome_uex,
            )
            .all()
        )

        liberacoes_info = [_mapear_liberacao_projeto(l) for l in liberacoes]

        return ListarLiberacoesProjetosResponse(
            success=True,
            total=len(liberacoes_info),
            liberacoes=liberacoes_info,
        )

    except HTTPException:
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
        liberacao = (
            db.query(LiberacoesProjeto)
            .options(joinedload(LiberacoesProjeto.escola))
            .filter(
                LiberacoesProjeto.id == liberacao_id,
            )
            .first()
        )

        if not liberacao:
            raise HTTPException(status_code=404, detail="Liberação de projetos não encontrada")

        dados = request.model_dump(exclude_unset=True)
        if not dados:
            raise HTTPException(status_code=400, detail="Nenhum campo fornecido para atualização")

        if "numero_folha" in dados:
            numero_folha = dados["numero_folha"]
            if numero_folha is not None and numero_folha <= 0:
                raise HTTPException(status_code=400, detail="numero_folha deve ser maior que 0")
            liberacao.numero_folha = numero_folha

        if "liberada" in dados:
            liberada = dados["liberada"]
            liberacao.liberada = liberada

            if liberada and "data_liberacao" not in dados and liberacao.data_liberacao is None:
                liberacao.data_liberacao = datetime.now()

            if not liberada and "data_liberacao" not in dados:
                liberacao.data_liberacao = None

        if "data_liberacao" in dados:
            liberacao.data_liberacao = dados["data_liberacao"]

        db.commit()
        db.refresh(liberacao)

        return LiberacaoProjetoResponse(
            success=True,
            message="Liberação de projetos atualizada com sucesso",
            liberacao=_mapear_liberacao_projeto(liberacao),
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Erro ao atualizar liberação de projetos")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar liberação: {str(e)}")


@projeto_router.delete("/liberacoes/{liberacao_id}", response_model=LiberacaoProjetoResponse, tags=["Projetos"])
def remover_liberacao_projetos(
    liberacao_id: int,
    db: Session = Depends(get_db),
) -> LiberacaoProjetoResponse:
    try:
        liberacao = (
            db.query(LiberacoesProjeto)
            .options(joinedload(LiberacoesProjeto.escola))
            .filter(
                LiberacoesProjeto.id == liberacao_id,
            )
            .first()
        )

        if not liberacao:
            raise HTTPException(status_code=404, detail="Liberação de projetos não encontrada")

        liberacao.liberada = False
        liberacao.numero_folha = None
        liberacao.data_liberacao = None

        db.commit()
        db.refresh(liberacao)

        return LiberacaoProjetoResponse(
            success=True,
            message="Liberação de projetos resetada com sucesso",
            liberacao=_mapear_liberacao_projeto(liberacao),
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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
        liberacoes = (
            db.query(LiberacoesProjeto)
            .options(joinedload(LiberacoesProjeto.escola))
            .filter(
                LiberacoesProjeto.escola_id == escola_id,
            )
            .order_by(LiberacoesProjeto.numero_folha.nulls_last())
            .all()
        )

        if not liberacoes:
            escola = db.query(Escola).filter(Escola.id == escola_id).first()
            if not escola:
                raise HTTPException(status_code=404, detail="Escola não encontrada")

        liberacoes_info = [_mapear_liberacao_projeto(l) for l in liberacoes]

        return ListarLiberacoesProjetosResponse(
            success=True,
            total=len(liberacoes_info),
            liberacoes=liberacoes_info,
        )

    except HTTPException:
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

        liberacoes = (
            db.query(LiberacoesProjeto)
            .options(joinedload(LiberacoesProjeto.escola))
            .filter(
                LiberacoesProjeto.numero_folha == numero_folha,
                LiberacoesProjeto.liberada.is_(True),
            )
            .order_by(Escola.nome_uex)
            .all()
        )

        liberacoes_info = [_mapear_liberacao_projeto(l) for l in liberacoes]

        return ListarLiberacoesProjetosResponse(
            success=True,
            total=len(liberacoes_info),
            liberacoes=liberacoes_info,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao listar liberações de projetos por folha")
        raise HTTPException(status_code=500, detail=f"Erro ao listar liberações: {str(e)}")

