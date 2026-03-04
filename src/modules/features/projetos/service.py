from typing import Optional, List, Dict, Set
from datetime import datetime
from sqlalchemy.orm import Session
from src.core.database import transaction
from src.core.logging_config import logger
from src.core.exceptions import NotFoundException, BadRequestException
from src.modules.features.anos import obter_ano_letivo
from src.modules.features.escolas import Escola
from src.modules.features.escolas.repository import EscolaRepository
from src.modules.features.calculos import CalculosProfin
from src.modules.features.calculos.repository import CalculoRepository
from src.modules.shared.constants import VALOR_PROJETO_UNITARIO
from src.modules.features.projetos import LiberacoesProjeto
from src.modules.features.projetos.repository import ProjetoRepository
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
        
        if calculo.profin_projeto <= 0:
            return 0
    
        return int(calculo.profin_projeto)
    
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
        
        # Calcular quantidades
        calculo = escola.calculos if escola else None
        quantidade_direito = ProjetoService.obter_quantidade_direito_projeto(calculo)
        quantidade_a_pagar = ProjetoService.calcular_quantidade_projetos_a_pagar(escola, calculo) if escola else 0
        quantidade_planilha = escola.quantidade_projetos_aprovados if escola else None
        
        # Calcular valor usando a comparação
        valor_calculado = ProjetoService.calcular_valor_projetos_aprovados(escola, calculo) if escola else 0.0
        
        resultado = LiberacaoProjetoInfo(
            id=liberacao.id,
            escola_id=escola.id if escola else liberacao.escola_id,
            nome_uex=escola.nome_uex if escola else "",
            dre=escola.dre if escola else None,
            liberada=liberacao.liberada,
            numero_folha=liberacao.numero_folha,
            data_liberacao=liberacao.data_liberacao,
            valor_projetos_aprovados=valor_calculado,
            quantidade_projetos_direito=quantidade_direito if quantidade_direito > 0 else None,
            quantidade_projetos_a_pagar=quantidade_a_pagar if quantidade_a_pagar > 0 else None,
            quantidade_projetos_aprovados=quantidade_planilha,
            created_at=liberacao.created_at,
            updated_at=liberacao.updated_at,
        )
        
        return resultado
    
    @staticmethod
    def obter_projetos_agrupados(
        db: Session,
        ano_letivo_id: Optional[int] = None
    ) -> RepasseResumoResponse:
        _, ano_id = obter_ano_letivo(db, ano_letivo_id)

        # Buscar upload ativo para filtrar apenas escolas do upload ativo
        from src.modules.features.uploads.repository import ContextoAtivoRepository, UploadRepository
        contexto_repo = ContextoAtivoRepository(db)
        upload_ativo = contexto_repo.find_upload_ativo(ano_id)
        
        if not upload_ativo:
            # Fallback para o mais recente se não houver contexto ativo
            upload_repo = UploadRepository(db)
            upload_ativo = upload_repo.find_latest(ano_id)
            if not upload_ativo:
                return RepasseResumoResponse(
                    success=True,
                    total_parcelas=0,
                    total_folhas=0,
                    total_escolas=0,
                    valor_total_reais=0.0,
                    folhas=[],
                )
        
        # Buscar apenas escolas do upload ativo com relacionamentos
        from sqlalchemy.orm import joinedload
        escolas = (
            db.query(Escola)
            .filter(Escola.upload_id == upload_ativo.id)
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

        escola_repo = EscolaRepository(db)
        escolas = escola_repo.find_by_ids(escola_ids_unicos)

        if len(escolas) != len(escola_ids_unicos):
            ids_encontrados = {escola.id for escola in escolas}
            ids_invalidos = [eid for eid in escola_ids_unicos if eid not in ids_encontrados]
            from src.core.exceptions import EscolaNaoEncontradaException
            raise EscolaNaoEncontradaException(escola_id=ids_invalidos[0] if ids_invalidos else None)

        projeto_repo = ProjetoRepository(db)
        mapa_liberacoes = projeto_repo.create_map_by_escola_id(escola_ids_unicos)

        agora = datetime.now()
        liberacoes_resultado: List[LiberacoesProjeto] = []

        # Carregar escolas com cálculos
        escola_repo = EscolaRepository(db)
        escolas_com_calculos = escola_repo.find_by_ids(escola_ids_unicos)
        calculo_repo = CalculoRepository(db)

        with transaction(db):
            for escola in escolas_com_calculos:
                # Buscar cálculo da escola
                calculo = calculo_repo.find_by_escola_id(escola.id)
                
                liberacao = mapa_liberacoes.get(escola.id)
                valor_projetos_calculado = ProjetoService.calcular_valor_projetos_aprovados(escola, calculo)

                if liberacao:
                    projeto_repo.update(
                        liberacao,
                        liberada=True,
                        numero_folha=numero_folha,
                        data_liberacao=agora,
                        valor_projetos_aprovados=valor_projetos_calculado
                    )
                else:
                    liberacao = projeto_repo.create(
                        escola_id=escola.id,
                        liberada=True,
                        numero_folha=numero_folha,
                        data_liberacao=agora,
                        valor_projetos_aprovados=valor_projetos_calculado
                    )
                    mapa_liberacoes[escola.id] = liberacao

                liberacao.escola = escola
                liberacoes_resultado.append(liberacao)

        # Buscar liberações atualizadas com relacionamentos
        liberacoes_ids = [lib.id for lib in liberacoes_resultado]
        liberacoes_atualizadas = []
        for lib_id in liberacoes_ids:
            lib = projeto_repo.find_by_id(lib_id)
            if lib:
                liberacoes_atualizadas.append(lib)

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
        projeto_repo = ProjetoRepository(db)
        liberacoes = projeto_repo.find_all_with_filters(
            numero_folha=numero_folha,
            liberada=liberada,
            escola_id=escola_id,
            ano_letivo_id=ano_letivo_id
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
        projeto_repo = ProjetoRepository(db)
        liberacao = projeto_repo.find_by_id(liberacao_id)

        if not liberacao:
            raise NotFoundException("Liberação de projetos não encontrada")

        update_data = {}
        
        if numero_folha is not None:
            if numero_folha <= 0:
                raise BadRequestException("numero_folha deve ser maior que 0")
            update_data["numero_folha"] = numero_folha

        if liberada is not None:
            update_data["liberada"] = liberada

            if liberada and data_liberacao is None and liberacao.data_liberacao is None:
                update_data["data_liberacao"] = datetime.now()

            if not liberada and data_liberacao is None:
                update_data["data_liberacao"] = None

        if data_liberacao is not None:
            update_data["data_liberacao"] = data_liberacao

        with transaction(db):
            if update_data:
                projeto_repo.update(liberacao, **update_data)

        db.refresh(liberacao)
        return ProjetoService.mapear_liberacao_projeto(liberacao)
    
    @staticmethod
    def remover_liberacao_projeto(
        db: Session,
        liberacao_id: int
    ) -> LiberacaoProjetoInfo:
        projeto_repo = ProjetoRepository(db)
        liberacao = projeto_repo.find_by_id(liberacao_id)

        if not liberacao:
            raise NotFoundException("Liberação de projetos não encontrada")

        with transaction(db):
            projeto_repo.update(
                liberacao,
                liberada=False,
                numero_folha=None,
                data_liberacao=None
            )

        db.refresh(liberacao)
        return ProjetoService.mapear_liberacao_projeto(liberacao)

