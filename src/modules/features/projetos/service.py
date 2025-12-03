from typing import Optional, List, Dict, Set
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from src.core.database import transaction
from src.core.logging_config import logger
from src.core.exceptions import EscolaNaoEncontradaException, NotFoundException, BadRequestException
from src.core.utils import obter_ano_letivo
from src.modules.features.escolas import Escola
from src.modules.features.calculos import CalculosProfin
from src.modules.features.uploads import Upload
from src.modules.features.projetos.constants import VALOR_PROJETO_UNITARIO
from src.modules.features.projetos import LiberacoesProjeto
from src.modules.schemas.parcelas import RepasseResumoResponse, RepasseFolhaInfo, EscolaPrevisaoInfo
from src.modules.schemas.projetos import LiberacaoProjetoInfo


class ProjetoService:

    @staticmethod
    def calcular_valor_projetos_aprovados(escola: Escola, calculo: Optional[CalculosProfin]) -> float:
        quantidade_planilha = max(escola.quantidade_projetos_aprovados or 0, 0)
        quantidade_direito = ProjetoService.obter_quantidade_direito_projeto(calculo)

        if quantidade_direito > 0:
            quantidade_pagar = min(quantidade_planilha, quantidade_direito)
        else:
            quantidade_pagar = 0

        valor_calculado = quantidade_pagar * VALOR_PROJETO_UNITARIO
        return round(valor_calculado, 2)
    
    @staticmethod
    def obter_quantidade_direito_projeto(calculo: Optional[CalculosProfin]) -> int:
        if not calculo or calculo.profin_projeto is None:
            return 0

        valor = calculo.profin_projeto or 0.0
        if valor <= 0:
            return 0

        return int(max(valor, 0))
    
    @staticmethod
    def calcular_quantidade_projetos_a_pagar(escola: Escola, calculo: Optional[CalculosProfin]) -> int:
        quantidade_direito = ProjetoService.obter_quantidade_direito_projeto(calculo)
        quantidade_planilha = max(escola.quantidade_projetos_aprovados or 0, 0)
        
        if quantidade_direito > 0:
            return min(quantidade_planilha, quantidade_direito)
        return 0
    
    @staticmethod
    def mapear_liberacao_projeto(liberacao: LiberacoesProjeto) -> LiberacaoProjetoInfo:
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
    
    @staticmethod
    def obter_projetos_agrupados(
        db: Session,
        ano_letivo_id: Optional[int] = None
    ) -> RepasseResumoResponse:
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
        escolas_por_folha: Dict[int, Dict[Optional[int], Set[int]]] = {}
        

        with transaction(db):
            for escola in escolas:
                valor_projetos_calculado = ProjetoService.calcular_valor_projetos_aprovados(escola, escola.calculos)
                quantidade_projetos_a_pagar = ProjetoService.calcular_quantidade_projetos_a_pagar(escola, escola.calculos)

                if not escola.calculos:
                    logger.info(
                        "Escola %s (%s) ainda não possui cálculos gerados; usando valor_projetos_calculado=%.2f",
                        escola.id,
                        escola.nome_uex,
                        valor_projetos_calculado,
                    )

                parcela = 1
                liberacao_projeto: Optional[LiberacoesProjeto] = escola.liberacoes_projetos if escola.liberacoes_projetos else None

                if liberacao_projeto:
                    if abs((liberacao_projeto.valor_projetos_aprovados or 0.0) - valor_projetos_calculado) > 0.009:
                        liberacao_projeto.valor_projetos_aprovados = valor_projetos_calculado
                    valor_projeto = valor_projetos_calculado
                    liberada = liberacao_projeto.liberada
                    folha = liberacao_projeto.numero_folha if liberacao_projeto.numero_folha is not None else None
                else:
                    liberada = False
                    folha = None
                    valor_projeto = valor_projetos_calculado

                if parcela not in agrupado:
                    agrupado[parcela] = {}
                    escolas_por_folha[parcela] = {}
                if folha not in agrupado[parcela]:
                    agrupado[parcela][folha] = []
                    escolas_por_folha[parcela][folha] = set()

                if escola.id in escolas_por_folha[parcela][folha]:
                    continue

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
    
    @staticmethod
    def liberar_escolas_projetos(
        db: Session,
        escola_ids: List[int],
        numero_folha: int
    ) -> List[LiberacaoProjetoInfo]:
        escola_ids_unicos = list(dict.fromkeys(escola_ids))

        escolas = (
            db.query(Escola)
            .options(joinedload(Escola.calculos))
            .filter(Escola.id.in_(escola_ids_unicos))
            .all()
        )

        if len(escolas) != len(escola_ids_unicos):
            ids_encontrados = {escola.id for escola in escolas}
            ids_invalidos = [eid for eid in escola_ids_unicos if eid not in ids_encontrados]
            raise EscolaNaoEncontradaException(escola_id=ids_invalidos[0] if ids_invalidos else None)

        liberacoes_existentes = (
            db.query(LiberacoesProjeto)
            .filter(LiberacoesProjeto.escola_id.in_(escola_ids_unicos))
            .all()
        )

        mapa_liberacoes: Dict[int, LiberacoesProjeto] = {
            liberacao.escola_id: liberacao for liberacao in liberacoes_existentes
        }

        agora = datetime.now()
        liberacoes_resultado: List[LiberacoesProjeto] = []

        with transaction(db):
            for escola in escolas:
                liberacao = mapa_liberacoes.get(escola.id)
                valor_projetos_calculado = ProjetoService.calcular_valor_projetos_aprovados(escola, escola.calculos)

                if liberacao:
                    liberacao.liberada = True
                    liberacao.numero_folha = numero_folha
                    liberacao.data_liberacao = agora
                    liberacao.valor_projetos_aprovados = valor_projetos_calculado
                else:
                    liberacao = LiberacoesProjeto(
                        escola_id=escola.id,
                        liberada=True,
                        numero_folha=numero_folha,
                        data_liberacao=agora,
                        valor_projetos_aprovados=valor_projetos_calculado,
                    )
                    db.add(liberacao)
                    mapa_liberacoes[escola.id] = liberacao

                liberacao.escola = escola
                liberacoes_resultado.append(liberacao)

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
        
        return [
            ProjetoService.mapear_liberacao_projeto(liberacoes_map[lib.id])
            for lib in liberacoes_resultado
        ]
    
    @staticmethod
    def listar_liberacoes_projetos(
        db: Session,
        numero_folha: Optional[int] = None,
        liberada: Optional[bool] = None,
        escola_id: Optional[int] = None,
        ano_letivo_id: Optional[int] = None,
    ) -> List[LiberacaoProjetoInfo]:
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

        return [ProjetoService.mapear_liberacao_projeto(l) for l in liberacoes]
    
    @staticmethod
    def atualizar_liberacao_projeto(
        db: Session,
        liberacao_id: int,
        numero_folha: Optional[int] = None,
        liberada: Optional[bool] = None,
        data_liberacao: Optional[datetime] = None,
    ) -> LiberacaoProjetoInfo:
        liberacao = (
            db.query(LiberacoesProjeto)
            .options(joinedload(LiberacoesProjeto.escola))
            .filter(LiberacoesProjeto.id == liberacao_id)
            .first()
        )

        if not liberacao:
            raise NotFoundException("Liberação de projetos não encontrada")

        with transaction(db):
            if numero_folha is not None:
                if numero_folha <= 0:
                    raise BadRequestException("numero_folha deve ser maior que 0")
                liberacao.numero_folha = numero_folha

            if liberada is not None:
                liberacao.liberada = liberada

                if liberada and data_liberacao is None and liberacao.data_liberacao is None:
                    liberacao.data_liberacao = datetime.now()

                if not liberada and data_liberacao is None:
                    liberacao.data_liberacao = None

            if data_liberacao is not None:
                liberacao.data_liberacao = data_liberacao

        db.refresh(liberacao)
        return ProjetoService.mapear_liberacao_projeto(liberacao)
    
    @staticmethod
    def remover_liberacao_projeto(
        db: Session,
        liberacao_id: int
    ) -> LiberacaoProjetoInfo:
        liberacao = (
            db.query(LiberacoesProjeto)
            .options(joinedload(LiberacoesProjeto.escola))
            .filter(LiberacoesProjeto.id == liberacao_id)
            .first()
        )

        if not liberacao:
            raise NotFoundException("Liberação de projetos não encontrada")

        with transaction(db):
            liberacao.liberada = False
            liberacao.numero_folha = None
            liberacao.data_liberacao = None

        db.refresh(liberacao)
        return ProjetoService.mapear_liberacao_projeto(liberacao)

