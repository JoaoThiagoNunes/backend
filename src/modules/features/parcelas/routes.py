from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Dict, List, Optional
from src.modules.features.parcelas.utils import dividir_cota_em_parcelas_por_ensino
from src.core.database import get_db
from src.core.logging_config import logger
from src.modules.features.anos import obter_ano_letivo
from src.modules.features.parcelas import calcular_porcentagens_ensino
from src.modules.features.calculos import CalculosProfin, TipoCota, TipoEnsino
from src.modules.features.escolas import Escola
from src.modules.features.escolas.utils import escola_esta_liberada
from src.modules.features.parcelas import ParcelasProfin, LiberacoesParcela, ParcelaService
from src.modules.features.projetos import LiberacoesProjeto
from src.modules.features.uploads import Upload
from src.modules.schemas.parcelas import (
    SepararParcelasRequest,
    SepararParcelasResponse,
    EscolaParcelas,
    ParcelaPorCota,
    LiberarParcelasRequest,
    LiberarParcelasResponse,
    ListarLiberacoesResponse,
    LiberacaoParcelaResponse,
    AtualizarLiberacaoParcelaRequest,
    ParcelasEscolaResponse,
    ParcelaDetalhe,
    AtualizarFolhaRequest,
    AtualizarEscolaRequest,
    EscolaAtualizadaResponse,
    PrevisaoLiberacaoResponse,
    EscolaPrevisaoInfo,
    RepasseResumoResponse,
    RepasseFolhaInfo,
)
from datetime import datetime


parcelas_router = APIRouter()

_COTAS_PROCESSAR = [
    ("merenda", "profin_merenda", "merenda", 2),
    ("gestao", "profin_gestao", "gestao", 2),
    ("preuni", "profin_preuni", "preuni", 2),
    #("climatizacao", "profin_climatizacao", "climatizacao", 2), # Desativado temporariamente
    ("sala_recurso", "profin_sala_recurso", "sala_recurso", 2),
    ("uniforme", "profin_uniforme", "uniforme", 1),
    #("permanente", "profin_permanente", "permanente", 2), # Desativado temporariamente
    ("kit_escolar", "profin_kit_escolar", "kit_escolar", 1),
]
_COTAS_PROCESSAR_ENUM = [TipoCota(item[2]) for item in _COTAS_PROCESSAR]
_COTA_BY_ENUM = {
    item[2]: (item[0], item[1], item[3]) for item in _COTAS_PROCESSAR
}


@parcelas_router.get("/liberacoes", response_model=ListarLiberacoesResponse, tags=["Parcelas"])
def listar_liberacoes(
    numero_parcela: Optional[int] = Query(None),
    numero_folha: Optional[int] = Query(None),
    liberada: Optional[bool] = Query(None),
    escola_id: Optional[int] = Query(None),
    ano_letivo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> ListarLiberacoesResponse:
    try:
        if numero_parcela is not None and numero_parcela not in (1, 2):
            raise HTTPException(status_code=400, detail="numero_parcela deve ser 1 ou 2")

        if numero_folha is not None and numero_folha <= 0:
            raise HTTPException(status_code=400, detail="numero_folha deve ser maior que 0")

        if ano_letivo_id is not None:
            _, ano_letivo_id = obter_ano_letivo(db, ano_letivo_id)

        query = db.query(LiberacoesParcela).join(Escola)

        if ano_letivo_id is not None:
            # Filtrar apenas por escolas do upload ativo
            from src.modules.features.uploads.repository import ContextoAtivoRepository, UploadRepository
            
            contexto_repo = ContextoAtivoRepository(db)
            upload_ativo = contexto_repo.find_upload_ativo(ano_letivo_id)
            
            if not upload_ativo:
                upload_repo = UploadRepository(db)
                upload_ativo = upload_repo.find_latest(ano_letivo_id)
            
            if upload_ativo:
                query = query.filter(Escola.upload_id == upload_ativo.id)

        if numero_parcela is not None:
            query = query.filter(LiberacoesParcela.numero_parcela == numero_parcela)

        if numero_folha is not None:
            query = query.filter(LiberacoesParcela.numero_folha == numero_folha)

        if liberada is not None:
            query = query.filter(LiberacoesParcela.liberada == liberada)

        if escola_id is not None:
            query = query.filter(LiberacoesParcela.escola_id == escola_id)

        liberacoes = query.options(joinedload(LiberacoesParcela.escola))
        liberacoes = liberacoes.order_by(
            LiberacoesParcela.numero_parcela,
            LiberacoesParcela.numero_folha.nulls_last(),
            Escola.nome_uex
        ).all()

        liberacoes_info = [ParcelaService.mapear_liberacao_parcela(l) for l in liberacoes]

        return ListarLiberacoesResponse(
            success=True,
            total=len(liberacoes_info),
            liberacoes=liberacoes_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao listar liberações")
        raise HTTPException(status_code=500, detail=f"Erro ao listar liberações: {str(e)}")


@parcelas_router.get("/escola/{escola_id}/liberacoes", response_model=ListarLiberacoesResponse, tags=["Parcelas"])
def listar_liberacoes_por_escola(
    escola_id: int,
    db: Session = Depends(get_db)
) -> ListarLiberacoesResponse:
    try:
        liberacoes = db.query(LiberacoesParcela)
        liberacoes = liberacoes.options(joinedload(LiberacoesParcela.escola))
        liberacoes = liberacoes.filter(LiberacoesParcela.escola_id == escola_id)
        liberacoes = liberacoes.order_by(LiberacoesParcela.numero_parcela, LiberacoesParcela.numero_folha).all()

        if not liberacoes:
            escola = db.query(Escola).filter(Escola.id == escola_id).first()
            if not escola:
                raise HTTPException(status_code=404, detail="Escola não encontrada")

        liberacoes_info = [ParcelaService.mapear_liberacao_parcela(l) for l in liberacoes]

        return ListarLiberacoesResponse(
            success=True,
            total=len(liberacoes_info),
            liberacoes=liberacoes_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao listar liberações por escola")
        raise HTTPException(status_code=500, detail=f"Erro ao listar liberações por escola: {str(e)}")


@parcelas_router.get("/previsao", response_model=PrevisaoLiberacaoResponse, tags=["Parcelas"])
def previsao_liberacao_escolas(
    numero_parcela: int = Query(..., ge=1, le=2),
    ano_letivo_id: Optional[int] = Query(None),
    somente_pendentes: bool = Query(True),
    db: Session = Depends(get_db)
) -> PrevisaoLiberacaoResponse:
    try:
        _, ano_id = obter_ano_letivo(db, ano_letivo_id)

        # Buscar apenas escolas do upload ativo
        from src.modules.features.uploads.repository import ContextoAtivoRepository, UploadRepository
        
        contexto_repo = ContextoAtivoRepository(db)
        upload_ativo = contexto_repo.find_upload_ativo(ano_id)
        
        if not upload_ativo:
            upload_repo = UploadRepository(db)
            upload_ativo = upload_repo.find_latest(ano_id)
            if not upload_ativo:
                raise HTTPException(
                    status_code=404,
                    detail=f"Nenhum upload encontrado para o ano letivo"
                )

        escolas = db.query(Escola)
        escolas = escolas.options(joinedload(Escola.calculos).joinedload(CalculosProfin.parcelas))
        escolas = escolas.filter(Escola.upload_id == upload_ativo.id)
        escolas = escolas.order_by(Escola.nome_uex).all()

        liberacoes = (
            db.query(LiberacoesParcela)
            .join(Escola)
            .join(Upload, Escola.upload_id == Upload.id)
            .filter(
                LiberacoesParcela.numero_parcela == numero_parcela,
                Upload.ano_letivo_id == ano_id
            )
            .options(joinedload(LiberacoesParcela.escola))
            .all()
        )

        mapa_liberacoes: Dict[int, LiberacoesParcela] = {
            liberacao.escola_id: liberacao for liberacao in liberacoes
        }

        escolas_info: List[EscolaPrevisaoInfo] = []

        for escola in escolas:
            calculo = escola.calculos
            if not calculo:
                continue

            valor_total = ParcelaService.calcular_total_parcela(calculo, numero_parcela)
            if valor_total <= 0:
                continue

            liberacao = mapa_liberacoes.get(escola.id)
            info = ParcelaService.build_previsao_info(escola, numero_parcela, liberacao)

            if somente_pendentes and info.liberada:
                continue

            escolas_info.append(info)

        return PrevisaoLiberacaoResponse(
            success=True,
            numero_parcela=numero_parcela,
            total_escolas=len(escolas_info),
            escolas=escolas_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao obter previsão de liberação")
        raise HTTPException(status_code=500, detail=f"Erro ao obter previsão de liberação: {str(e)}")


@parcelas_router.get("/repasse", response_model=RepasseResumoResponse, tags=["Parcelas"])
def obter_repasse(
    ano_letivo_id: Optional[int] = Query(None),
    numero_parcela: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> RepasseResumoResponse:
    try:
        if numero_parcela is not None and numero_parcela not in (1, 2):
            raise HTTPException(status_code=400, detail="numero_parcela deve ser 1 ou 2")

        _, ano_id = obter_ano_letivo(db, ano_letivo_id)

        # Buscar apenas liberações de escolas do upload ativo
        from src.modules.features.uploads.repository import ContextoAtivoRepository, UploadRepository
        
        contexto_repo = ContextoAtivoRepository(db)
        upload_ativo = contexto_repo.find_upload_ativo(ano_id)
        
        if not upload_ativo:
            upload_repo = UploadRepository(db)
            upload_ativo = upload_repo.find_latest(ano_id)
            if not upload_ativo:
                raise HTTPException(
                    status_code=404,
                    detail=f"Nenhum upload encontrado para o ano letivo"
                )

        liberacoes_query = db.query(LiberacoesParcela)
        liberacoes_query = liberacoes_query.filter(LiberacoesParcela.liberada.is_(True))
        liberacoes_query = liberacoes_query.options(
            joinedload(LiberacoesParcela.escola)
            .joinedload(Escola.calculos)
            .joinedload(CalculosProfin.parcelas)
        )
        liberacoes_query = liberacoes_query.join(Escola)
        liberacoes_query = liberacoes_query.filter(Escola.upload_id == upload_ativo.id)

        if numero_parcela is not None:
            liberacoes_query = liberacoes_query.filter(LiberacoesParcela.numero_parcela == numero_parcela)

        liberacoes = liberacoes_query.all()

        if not liberacoes:
            return RepasseResumoResponse(
                success=True,
                total_parcelas=0,
                total_folhas=0,
                total_escolas=0,
                valor_total_reais=0.0,
                folhas=[]
            )

        agrupado: Dict[int, Dict[Optional[int], List[LiberacoesParcela]]] = {}

        for liberacao in liberacoes:
            parcela = liberacao.numero_parcela
            folha = liberacao.numero_folha
            if parcela not in agrupado:
                agrupado[parcela] = {}
            if folha not in agrupado[parcela]:
                agrupado[parcela][folha] = []
            agrupado[parcela][folha].append(liberacao)

        folhas_info: List[RepasseFolhaInfo] = []
        total_valor = 0.0
        total_escolas = 0

        for parcela, folhas in sorted(agrupado.items()):
            for folha, liberacoes_folha in sorted(
                folhas.items(),
                key=lambda item: (
                    item[0] is None,
                    item[0] if item[0] is not None else 0
                )
            ):
                escolas_info: List[EscolaPrevisaoInfo] = []
                valor_folha = 0.0

                for liberacao in liberacoes_folha:
                    escola = liberacao.escola
                    if not escola or not escola.calculos:
                        continue

                    valor_escola = ParcelaService.calcular_total_parcela(escola.calculos, parcela)
                    valor_folha += valor_escola

                    info = EscolaPrevisaoInfo(
                        escola_id=escola.id,
                        nome_uex=escola.nome_uex,
                        dre=escola.dre,
                        numero_parcela=parcela,
                        liberada=True,
                        numero_folha=folha,
                        valor_total_reais=valor_escola
                    )
                    escolas_info.append(info)

                total_escolas += len(escolas_info)
                total_valor += valor_folha

                folhas_info.append(
                    RepasseFolhaInfo(
                        numero_parcela=parcela,
                        numero_folha=folha,
                        total_escolas=len(escolas_info),
                        valor_total_reais=round(valor_folha, 2),
                        escolas=escolas_info
                    )
                )

        return RepasseResumoResponse(
            success=True,
            total_parcelas=len(agrupado),
            total_folhas=len(folhas_info),
            total_escolas=total_escolas,
            valor_total_reais=round(total_valor, 2),
            folhas=folhas_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao obter dados de repasse")
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados de repasse: {str(e)}")


@parcelas_router.get("/escola/{escola_id}", response_model=ParcelasEscolaResponse, tags=["Parcelas"])
def obter_parcelas_escola(
    escola_id: int,
    db: Session = Depends(get_db)
) -> ParcelasEscolaResponse:
    try:
        # Carregar escola com relacionamento Upload
        escola = db.query(Escola).options(joinedload(Escola.upload)).filter(Escola.id == escola_id).first()
        if not escola:
            raise HTTPException(status_code=404, detail="Escola não encontrada")
        
        # Verificar se a escola pertence ao upload ativo do ano letivo dela
        # Se não pertencer, verificar se tem liberações (escolas com liberações devem ser preservadas)
        from src.modules.features.uploads.repository import ContextoAtivoRepository, UploadRepository
        
        contexto_repo = ContextoAtivoRepository(db)
        upload_ativo = contexto_repo.find_upload_ativo(escola.upload.ano_letivo_id)
        
        if not upload_ativo:
            upload_repo = UploadRepository(db)
            upload_ativo = upload_repo.find_latest(escola.upload.ano_letivo_id)
        
        # Verificar se a escola pertence ao upload ativo ou tem liberações
        escola_pertence_upload_ativo = upload_ativo and escola.upload_id == upload_ativo.id
        
        # Verificar se a escola tem liberações (parcelas ou projetos)
        tem_liberacoes_parcelas = db.query(LiberacoesParcela).filter(LiberacoesParcela.escola_id == escola_id).first() is not None
        tem_liberacoes_projetos = db.query(LiberacoesProjeto).filter(LiberacoesProjeto.escola_id == escola_id).first() is not None
        escola_tem_liberacoes = tem_liberacoes_parcelas or tem_liberacoes_projetos
        
        # Se a escola não pertence ao upload ativo e não tem liberações, bloquear acesso
        if not escola_pertence_upload_ativo and not escola_tem_liberacoes:
            raise HTTPException(
                status_code=404,
                detail=f"Escola não pertence ao upload ativo do ano letivo. Esta escola pertence ao upload ID {escola.upload_id}, mas o upload ativo é o ID {upload_ativo.id}."
            )
        
        # Buscar cálculo da escola, priorizando o cálculo do upload ativo
        # Isso garante que estamos usando o mesmo cálculo usado para criar as parcelas
        if upload_ativo:
            calculo = (
                db.query(CalculosProfin)
                .join(Escola, CalculosProfin.escola_id == Escola.id)
                .filter(
                    CalculosProfin.escola_id == escola_id,
                    Escola.upload_id == upload_ativo.id
                )
                .first()
            )
        else:
            calculo = db.query(CalculosProfin).filter(CalculosProfin.escola_id == escola_id).first()
        if not calculo:
            # Se a escola não tem cálculo, tentar buscar parcelas diretamente (pode ter parcelas de cálculos deletados)
            if escola_pertence_upload_ativo or escola_tem_liberacoes:
                # Buscar parcelas através de cálculos que podem ter sido deletados mas as parcelas ainda existem
                # Ou buscar parcelas diretamente pela escola se houver alguma forma de vinculação
                parcelas = (
                    db.query(ParcelasProfin)
                    .join(CalculosProfin, ParcelasProfin.calculo_id == CalculosProfin.id)
                    .filter(
                        CalculosProfin.escola_id == escola_id,
                        ParcelasProfin.tipo_cota.in_(_COTAS_PROCESSAR_ENUM),
                    )
                    .order_by(ParcelasProfin.tipo_cota, ParcelasProfin.numero_parcela, ParcelasProfin.tipo_ensino)
                    .all()
                )
                
                if parcelas:
                    # Se encontrou parcelas mesmo sem cálculo ativo, usar essas parcelas
                    pct_fundamental, pct_medio = calcular_porcentagens_ensino(escola)
                    
                    def mapear_cota_exibicao(enum_value: str) -> str:
                        info = _COTA_BY_ENUM.get(enum_value)
                        return info[0] if info else enum_value
                    
                    parcelas_detalhes = [
                        ParcelaDetalhe(
                            id=p.id,
                            tipo_cota=mapear_cota_exibicao(p.tipo_cota.value),
                            numero_parcela=p.numero_parcela,
                            tipo_ensino=p.tipo_ensino.value,
                            valor_reais=p.valor_reais,
                            valor_centavos=p.valor_centavos,
                            porcentagem_alunos=p.porcentagem_alunos,
                            created_at=p.created_at
                        )
                        for p in parcelas
                    ]
                    
                    return ParcelasEscolaResponse(
                        success=True,
                        escola_id=escola.id,
                        nome_uex=escola.nome_uex,
                        dre=escola.dre,
                        porcentagem_fundamental=pct_fundamental,
                        porcentagem_medio=pct_medio,
                        parcelas=parcelas_detalhes,
                        estado_liberacao=escola_esta_liberada(escola),
                        numeracao_folha=escola.numeracao_folha
                    )
                else:
                    # Escola não tem cálculos nem parcelas
                    # Retornar resposta com lista vazia em vez de erro 404
                    # Isso permite que o frontend veja que a escola existe e tem liberações, mas não tem parcelas
                    pct_fundamental, pct_medio = calcular_porcentagens_ensino(escola)
                    
                    return ParcelasEscolaResponse(
                        success=True,
                        escola_id=escola.id,
                        nome_uex=escola.nome_uex,
                        dre=escola.dre,
                        porcentagem_fundamental=pct_fundamental,
                        porcentagem_medio=pct_medio,
                        parcelas=[],  # Lista vazia - escola tem liberações mas não tem parcelas ativas
                        estado_liberacao=escola_esta_liberada(escola),
                        numeracao_folha=escola.numeracao_folha
                    )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Nenhum cálculo encontrado para esta escola. Execute /calculos e /parcelas primeiro."
                )
        
        parcelas = (
            db.query(ParcelasProfin)
            .filter(
                ParcelasProfin.calculo_id == calculo.id,
                ParcelasProfin.tipo_cota.in_(_COTAS_PROCESSAR_ENUM),
            )
            .order_by(ParcelasProfin.tipo_cota, ParcelasProfin.numero_parcela, ParcelasProfin.tipo_ensino)
            .all()
        )

        if not parcelas:
            # Retornar resposta com lista vazia de parcelas em vez de erro 404
            # Isso permite que o frontend veja que a escola existe e tem cálculo, mas ainda não tem parcelas
            pct_fundamental, pct_medio = calcular_porcentagens_ensino(escola)
            
            return ParcelasEscolaResponse(
                success=True,
                escola_id=escola.id,
                nome_uex=escola.nome_uex,
                dre=escola.dre,
                porcentagem_fundamental=pct_fundamental,
                porcentagem_medio=pct_medio,
                parcelas=[],  # Lista vazia - parcelas ainda não foram criadas
                estado_liberacao=escola_esta_liberada(escola),
                numeracao_folha=escola.numeracao_folha
            )

        pct_fundamental, pct_medio = calcular_porcentagens_ensino(escola)

        def mapear_cota_exibicao(enum_value: str) -> str:
            info = _COTA_BY_ENUM.get(enum_value)
            return info[0] if info else enum_value

        parcelas_detalhes = [
            ParcelaDetalhe(
                id=p.id,
                tipo_cota=mapear_cota_exibicao(p.tipo_cota.value),
                numero_parcela=p.numero_parcela,
                tipo_ensino=p.tipo_ensino.value,
                valor_reais=p.valor_reais,
                valor_centavos=p.valor_centavos,
                porcentagem_alunos=p.porcentagem_alunos,
                created_at=p.created_at
            )
            for p in parcelas
        ]
        
        return ParcelasEscolaResponse(
            success=True,
            escola_id=escola.id,
            nome_uex=escola.nome_uex,
            dre=escola.dre,
            porcentagem_fundamental=pct_fundamental,
            porcentagem_medio=pct_medio,
            parcelas=parcelas_detalhes,
            estado_liberacao=escola_esta_liberada(escola),
            numeracao_folha=escola.numeracao_folha
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao obter parcelas da escola {escola_id}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter parcelas da escola: {str(e)}")

@parcelas_router.post("", response_model=SepararParcelasResponse, tags=["Parcelas"])
def separar_valores_em_parcelas(
    request: SepararParcelasRequest,
    db: Session = Depends(get_db)
) -> SepararParcelasResponse:
    try:
        ano_letivo, ano_letivo_id = obter_ano_letivo(db, request.ano_letivo_id)
        calculation_version = request.calculation_version or f"v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info("="*60)
        logger.info(f"SEPARANDO VALORES EM PARCELAS - ANO LETIVO: {ano_letivo.ano}")
        logger.info(f"Versão do cálculo: {calculation_version}")
        logger.info("="*60)

        # Buscar apenas cálculos do upload ativo (evitar parcelas de uploads antigos)
        from src.modules.features.uploads.repository import ContextoAtivoRepository, UploadRepository
        
        contexto_repo = ContextoAtivoRepository(db)
        upload_ativo = contexto_repo.find_upload_ativo(ano_letivo_id)
        
        if not upload_ativo:
            # Fallback para o upload mais recente se não houver contexto ativo
            upload_repo = UploadRepository(db)
            upload_ativo = upload_repo.find_latest(ano_letivo_id)
            if not upload_ativo:
                raise HTTPException(
                    status_code=404,
                    detail=f"Nenhum upload encontrado para o ano letivo {ano_letivo.ano}"
                )
        
        logger.info(f"Usando upload ativo: ID {upload_ativo.id} - {upload_ativo.filename}")
        
        calculos = (
            db.query(CalculosProfin)
            .join(Escola, CalculosProfin.escola_id == Escola.id)
            .join(Upload, Escola.upload_id == Upload.id)
            .options(joinedload(CalculosProfin.escola))
            .filter(
                Escola.upload_id == upload_ativo.id
            )
            .all()
        )
        
        if not calculos:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum cálculo encontrado para o ano letivo {ano_letivo.ano}. Execute /calculos primeiro."
            )
        
        calculos_ids = [c.id for c in calculos]
        deve_deletar_parcelas = False
        
        if not request.recalcular:
            # Verificar parcelas apenas do upload ativo
            calculos_com_parcelas = (
                db.query(ParcelasProfin.calculo_id)
                .join(CalculosProfin, ParcelasProfin.calculo_id == CalculosProfin.id)
                .join(Escola, CalculosProfin.escola_id == Escola.id)
                .filter(
                    Escola.upload_id == upload_ativo.id,
                    ParcelasProfin.tipo_cota.in_(_COTAS_PROCESSAR_ENUM),
                )
                .distinct()
                .all()
            )
            
            if calculos_com_parcelas:
                calculos_ids_com_parcelas = {row[0] for row in calculos_com_parcelas}
                calculos_sem_parcelas = [c for c in calculos if c.id not in calculos_ids_com_parcelas]
                
                if not calculos_sem_parcelas:
                    logger.info("Todas as escolas já têm parcelas criadas. Use recalcular=true para recalcular.")
                    # Buscar parcelas apenas do upload ativo
                    parcelas_existentes = (
                        db.query(ParcelasProfin)
                        .join(CalculosProfin, ParcelasProfin.calculo_id == CalculosProfin.id)
                        .join(Escola, CalculosProfin.escola_id == Escola.id)
                        .filter(
                            Escola.upload_id == upload_ativo.id,
                            ParcelasProfin.tipo_cota.in_(_COTAS_PROCESSAR_ENUM),
                        )
                        .all()
                    )
                    
                    escolas_dict = {}
                    for parcela in parcelas_existentes:
                        calculo = parcela.calculo
                        escola = calculo.escola
                        escola_id = escola.id
                        
                        if escola_id not in escolas_dict:
                            pct_fund, pct_medio = calcular_porcentagens_ensino(escola)
                            escolas_dict[escola_id] = {
                                "escola": escola,
                                "pct_fundamental": pct_fund,
                                "pct_medio": pct_medio,
                                "parcelas_por_cota": {}
                            }
                        
                        cota_enum_value = parcela.tipo_cota.value
                        if cota_enum_value not in _COTA_BY_ENUM:
                            continue
                        nome_exibicao, campo_cota, num_parcelas = _COTA_BY_ENUM[cota_enum_value]
                        
                        if nome_exibicao not in escolas_dict[escola_id]["parcelas_por_cota"]:
                            valor_cota = getattr(calculo, campo_cota, 0.0)
                            
                            # Calcular saldo reprogramado (mesma lógica usada ao criar novas parcelas)
                            saldo_reprogramado = 0.0
                            escola_temp = escolas_dict[escola_id]["escola"]
                            # cota_enum_value é o valor do enum (ex: "merenda", "gestao", etc.)
                            if cota_enum_value == "gestao" and escola_temp.saldo_reprogramado_gestao:
                                saldo_reprogramado = escola_temp.saldo_reprogramado_gestao or 0.0
                            elif cota_enum_value == "merenda" and escola_temp.saldo_reprogramado_merenda:
                                saldo_reprogramado = escola_temp.saldo_reprogramado_merenda or 0.0
                            
                            cota_data = {
                                "tipo_cota": nome_exibicao,
                                "valor_total_reais": valor_cota,
                                "saldo_reprogramado": saldo_reprogramado,
                                "parcela_1": {"fundamental": 0.0, "medio": 0.0},
                                "porcentagens": {
                                    "fundamental": escolas_dict[escola_id]["pct_fundamental"],
                                    "medio": escolas_dict[escola_id]["pct_medio"]
                                }
                            }
                            if num_parcelas == 2:
                                cota_data["parcela_2"] = {"fundamental": 0.0, "medio": 0.0}
                            escolas_dict[escola_id]["parcelas_por_cota"][nome_exibicao] = cota_data
                        
                        if parcela.numero_parcela == 1 or (parcela.numero_parcela == 2 and num_parcelas == 2):
                            parcela_key = f"parcela_{parcela.numero_parcela}"
                            ensino_key = parcela.tipo_ensino.value
                            valor_reais = parcela.valor_centavos / 100.0
                            escolas_dict[escola_id]["parcelas_por_cota"][nome_exibicao][parcela_key][ensino_key] = valor_reais
                    
                    escolas_lista = []
                    for escola_id, dados in escolas_dict.items():
                        escolas_lista.append(
                            EscolaParcelas(
                                escola_id=escola_id,
                                nome_uex=dados["escola"].nome_uex,
                                dre=dados["escola"].dre,
                                porcentagem_fundamental=dados["pct_fundamental"],
                                porcentagem_medio=dados["pct_medio"],
                                parcelas_por_cota=[
                                    ParcelaPorCota(**cota_data)
                                    for cota_data in dados["parcelas_por_cota"].values()
                                ],
                                estado_liberacao=escola_esta_liberada(dados["escola"]),
                                numeracao_folha=dados["escola"].numeracao_folha
                            )
                        )
                    
                    return SepararParcelasResponse(
                        success=True,
                        message=f"Parcelas já existem para {len(escolas_lista)} escolas. Use recalcular=true para recalcular.",
                        total_escolas=len(calculos),
                        escolas_processadas=len(escolas_lista),
                        total_parcelas_criadas=len(parcelas_existentes),
                        ano_letivo_id=ano_letivo_id,
                        escolas=escolas_lista,
                        calculation_version=calculation_version
                    )
                else:
                    # Há alguns cálculos sem parcelas, vamos criar apenas para eles
                    deve_deletar_parcelas = False  # Não deletar, apenas criar para os que faltam
                    calculos = calculos_sem_parcelas
            else:
                # Não há parcelas existentes, então todos os cálculos precisam de parcelas
                deve_deletar_parcelas = False  # Não deletar, apenas criar novas
                # calculos já contém todos os cálculos que precisam de parcelas
        else:
            # recalcular=true: sempre deletar parcelas antigas antes de criar novas
            deve_deletar_parcelas = True
        
        # Deletar parcelas antigas se necessário (substituição completa)
        if deve_deletar_parcelas and calculos_ids:
            parcelas_deletadas = db.query(ParcelasProfin)\
                .filter(
                    ParcelasProfin.calculo_id.in_(calculos_ids),
                    ParcelasProfin.tipo_cota.in_(_COTAS_PROCESSAR_ENUM)
                )\
                .delete(synchronize_session=False)
            
            if parcelas_deletadas > 0:
                logger.info(f"Parcelas antigas deletadas: {parcelas_deletadas} parcela(s) para {len(calculos_ids)} cálculo(s)")
            db.flush()  # Garantir que a deleção foi commitada antes de criar novas
        
        # Criar novas parcelas
        escolas_processadas = []
        total_parcelas_criadas = 0
        
        for calculo in calculos:
            escola = calculo.escola
            if not escola:
                logger.warning(f"Escola não encontrada para cálculo {calculo.id}")
                continue
            pct_fundamental, pct_medio = calcular_porcentagens_ensino(escola)
            parcelas_por_cota = []

            for nome_exibicao, campo_cota, enum_valor, num_parcelas in _COTAS_PROCESSAR:
                valor_cota = getattr(calculo, campo_cota, 0.0)
                
                if valor_cota <= 0:
                    continue
                
                divisao = dividir_cota_em_parcelas_por_ensino(
                    valor_cota,
                    pct_fundamental,
                    pct_medio,
                    numero_parcelas=num_parcelas,
                    escola=escola,
                    tipo_cota=enum_valor
                )
                
                tipo_cota_enum = TipoCota(enum_valor)
                
                parcela_1_fund = ParcelasProfin(
                    calculo_id=calculo.id,
                    tipo_cota=tipo_cota_enum,
                    numero_parcela=1,
                    tipo_ensino=TipoEnsino.FUNDAMENTAL,
                    valor_centavos=divisao["parcela_1"]["fundamental"],
                    porcentagem_alunos=pct_fundamental,
                    calculation_version=calculation_version
                )
                db.add(parcela_1_fund)
                total_parcelas_criadas += 1
                
                parcela_1_medio = ParcelasProfin(
                    calculo_id=calculo.id,
                    tipo_cota=tipo_cota_enum,
                    numero_parcela=1,
                    tipo_ensino=TipoEnsino.MEDIO,
                    valor_centavos=divisao["parcela_1"]["medio"],
                    porcentagem_alunos=pct_medio,
                    calculation_version=calculation_version
                )
                db.add(parcela_1_medio)
                total_parcelas_criadas += 1
                
                if num_parcelas == 2:
                    parcela_2_fund = ParcelasProfin(
                        calculo_id=calculo.id,
                        tipo_cota=tipo_cota_enum,
                        numero_parcela=2,
                        tipo_ensino=TipoEnsino.FUNDAMENTAL,
                        valor_centavos=divisao["parcela_2"]["fundamental"],
                        porcentagem_alunos=pct_fundamental,
                        calculation_version=calculation_version
                    )
                    db.add(parcela_2_fund)
                    total_parcelas_criadas += 1
                    
                    parcela_2_medio = ParcelasProfin(
                        calculo_id=calculo.id,
                        tipo_cota=tipo_cota_enum,
                        numero_parcela=2,
                        tipo_ensino=TipoEnsino.MEDIO,
                        valor_centavos=divisao["parcela_2"]["medio"],
                        porcentagem_alunos=pct_medio,
                        calculation_version=calculation_version
                    )
                    db.add(parcela_2_medio)
                    total_parcelas_criadas += 1
                
                saldo_reprogramado = 0.0
                if enum_valor == "gestao" and escola.saldo_reprogramado_gestao:
                    saldo_reprogramado = escola.saldo_reprogramado_gestao or 0.0
                elif enum_valor == "merenda" and escola.saldo_reprogramado_merenda:
                    saldo_reprogramado = escola.saldo_reprogramado_merenda or 0.0

                parcela_por_cota_data = {
                    "tipo_cota": nome_exibicao,
                    "valor_total_reais": valor_cota,
                    "saldo_reprogramado": saldo_reprogramado,
                    "parcela_1": {
                        "fundamental": divisao["parcela_1"]["fundamental"] / 100.0,
                        "medio": divisao["parcela_1"]["medio"] / 100.0
                    },
                    "porcentagens": {
                        "fundamental": pct_fundamental,
                        "medio": pct_medio
                    }
                }
                
                if num_parcelas == 2:
                    parcela_por_cota_data["parcela_2"] = {
                        "fundamental": divisao["parcela_2"]["fundamental"] / 100.0,
                        "medio": divisao["parcela_2"]["medio"] / 100.0
                    }
                
                parcelas_por_cota.append(ParcelaPorCota(**parcela_por_cota_data))
            
            # Adicionar escola APENAS UMA VEZ após processar todas as cotas
            escolas_processadas.append(
                EscolaParcelas(
                    escola_id=escola.id,
                    nome_uex=escola.nome_uex,
                    dre=escola.dre,
                    porcentagem_fundamental=pct_fundamental,
                    porcentagem_medio=pct_medio,
                    parcelas_por_cota=parcelas_por_cota,
                    estado_liberacao=escola_esta_liberada(escola),
                    numeracao_folha=escola.numeracao_folha
                )
            )
        
        db.commit()
        
        logger.info(f"Parcelas criadas para {len(escolas_processadas)} escolas")
        logger.info(f"Total de parcelas: {total_parcelas_criadas}")
        logger.info("="*60)
        
        return SepararParcelasResponse(
            success=True,
            message=f"Parcelas criadas para {len(escolas_processadas)} escolas do ano {ano_letivo.ano}",
            total_escolas=len(calculos),
            escolas_processadas=len(escolas_processadas),
            total_parcelas_criadas=total_parcelas_criadas,
            ano_letivo_id=ano_letivo_id,
            escolas=escolas_processadas,
            calculation_version=calculation_version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Erro ao separar valores em parcelas")
        raise HTTPException(status_code=500, detail=f"Erro ao separar valores: {str(e)}")


@parcelas_router.post("/liberar", response_model=LiberarParcelasResponse, tags=["Parcelas"])
def liberar_escolas_em_parcela(
    request: LiberarParcelasRequest,
    db: Session = Depends(get_db)
) -> LiberarParcelasResponse:
    try:
        if not request.escola_ids:
            raise HTTPException(status_code=400, detail="Informe ao menos uma escola para liberar")

        numero_parcela = request.numero_parcela
        if numero_parcela not in (1, 2):
            raise HTTPException(status_code=400, detail="numero_parcela deve ser 1 ou 2")

        if request.numero_folha <= 0:
            raise HTTPException(status_code=400, detail="numero_folha deve ser um inteiro maior ou igual a 1")

        escola_ids_unicos = list(dict.fromkeys(request.escola_ids))

        escolas = db.query(Escola)
        escolas = escolas.options(joinedload(Escola.calculos).joinedload(CalculosProfin.parcelas))
        escolas = escolas.filter(Escola.id.in_(escola_ids_unicos)).all()

        if len(escolas) != len(escola_ids_unicos):
            ids_encontrados = {escola.id for escola in escolas}
            ids_invalidos = [eid for eid in escola_ids_unicos if eid not in ids_encontrados]
            raise HTTPException(
                status_code=404,
                detail=f"Escolas não encontradas: {ids_invalidos}"
            )

        liberacoes_existentes = db.query(LiberacoesParcela)
        liberacoes_existentes = liberacoes_existentes.filter(
            LiberacoesParcela.escola_id.in_(escola_ids_unicos),
            LiberacoesParcela.numero_parcela == numero_parcela
        ).all()

        mapa_liberacoes: Dict[int, LiberacoesParcela] = {
            liberacao.escola_id: liberacao for liberacao in liberacoes_existentes
        }

        agora = datetime.now()
        liberacoes_resultado: List[LiberacoesParcela] = []

        for escola in escolas:
            liberacao = mapa_liberacoes.get(escola.id)

            if liberacao:
                liberacao.liberada = True
                liberacao.numero_folha = request.numero_folha
                liberacao.data_liberacao = agora
            else:
                liberacao = LiberacoesParcela(
                    escola_id=escola.id,
                    numero_parcela=numero_parcela,
                    liberada=True,
                    numero_folha=request.numero_folha,
                    data_liberacao=agora
                )
                db.add(liberacao)
                mapa_liberacoes[escola.id] = liberacao

            liberacao.escola = escola
            liberacoes_resultado.append(liberacao)

        db.commit()

        liberacoes_ids = [lib.id for lib in liberacoes_resultado]
        liberacoes_atualizadas = (
            db.query(LiberacoesParcela)
            .options(joinedload(LiberacoesParcela.escola))
            .filter(LiberacoesParcela.id.in_(liberacoes_ids))
            .all()
        )
        liberacoes_map: Dict[int, LiberacoesParcela] = {lib.id: lib for lib in liberacoes_atualizadas}
        liberacoes_info = [
            ParcelaService.mapear_liberacao_parcela(liberacoes_map[lib.id])
            for lib in liberacoes_resultado
        ]

        return LiberarParcelasResponse(
            success=True,
            message=f"{len(liberacoes_info)} escola(s) liberada(s) para a parcela {numero_parcela}, folha {request.numero_folha}",
            total_escolas_atualizadas=len(liberacoes_info),
            numero_parcela=numero_parcela,
            numero_folha=request.numero_folha,
            liberacoes=liberacoes_info
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Erro ao liberar escolas em parcela")
        raise HTTPException(status_code=500, detail=f"Erro ao liberar escolas: {str(e)}")



@parcelas_router.put("/liberacoes/{liberacao_id}", response_model=LiberacaoParcelaResponse, tags=["Parcelas"])
def atualizar_liberacao_parcela(
    liberacao_id: int,
    request: AtualizarLiberacaoParcelaRequest,
    db: Session = Depends(get_db)
) -> LiberacaoParcelaResponse:
    try:
        liberacao = db.query(LiberacoesParcela)
        liberacao = liberacao.options(joinedload(LiberacoesParcela.escola))
        liberacao = liberacao.filter(LiberacoesParcela.id == liberacao_id).first()

        if not liberacao:
            raise HTTPException(status_code=404, detail="Liberação não encontrada")

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

        return LiberacaoParcelaResponse(
            success=True,
            message="Liberação atualizada com sucesso",
            liberacao=ParcelaService.mapear_liberacao_parcela(liberacao)
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Erro ao atualizar liberação")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar liberação: {str(e)}")


@parcelas_router.delete("/liberacoes/{liberacao_id}", response_model=LiberacaoParcelaResponse, tags=["Parcelas"])
def remover_liberacao_parcela(
    liberacao_id: int,
    db: Session = Depends(get_db)
) -> LiberacaoParcelaResponse:
    try:
        liberacao = db.query(LiberacoesParcela)
        liberacao = liberacao.options(joinedload(LiberacoesParcela.escola))
        liberacao = liberacao.filter(LiberacoesParcela.id == liberacao_id).first()

        if not liberacao:
            raise HTTPException(status_code=404, detail="Liberação não encontrada")

        liberacao.liberada = False
        liberacao.numero_folha = None
        liberacao.data_liberacao = None

        db.commit()
        db.refresh(liberacao)

        return LiberacaoParcelaResponse(
            success=True,
            message="Liberação resetada com sucesso",
            liberacao=ParcelaService.mapear_liberacao_parcela(liberacao)
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Erro ao remover liberação")
        raise HTTPException(status_code=500, detail=f"Erro ao remover liberação: {str(e)}")




@parcelas_router.put("/escola/{escola_id}/folha", response_model=EscolaAtualizadaResponse, tags=["Parcelas"])
def atualizar_numeracao_folha(
    escola_id: int,
    request: AtualizarFolhaRequest,
    db: Session = Depends(get_db)
) -> EscolaAtualizadaResponse:
    try:
        escola = db.query(Escola).filter(Escola.id == escola_id).first()
        if not escola:
            raise HTTPException(status_code=404, detail="Escola não encontrada")
        
        rows_updated = db.query(Escola)\
            .filter(Escola.id == escola_id)\
            .update({"numeracao_folha": request.numeracao_folha}, synchronize_session=False)
        
        if rows_updated == 0:
            raise HTTPException(status_code=404, detail="Escola não encontrada para atualização")
        
        db.commit()
        
        db.expire_all()
        escola = db.query(Escola).filter(Escola.id == escola_id).first()
        
        logger.info(f"Numeração da folha atualizada para escola {escola_id}: {request.numeracao_folha}")
        
        return EscolaAtualizadaResponse(
            success=True,
            message=f"Numeração da folha atualizada para '{request.numeracao_folha or 'nenhum'}'",
            escola_id=escola.id,
            nome_uex=escola.nome_uex,
            estado_liberacao=escola_esta_liberada(escola),
            numeracao_folha=escola.numeracao_folha
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Erro ao atualizar numeração da folha da escola {escola_id}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar numeração da folha: {str(e)}")


@parcelas_router.put("/escola/{escola_id}", response_model=EscolaAtualizadaResponse, tags=["Parcelas"])
def atualizar_escola(
    escola_id: int,
    request: AtualizarEscolaRequest,
    db: Session = Depends(get_db)
) -> EscolaAtualizadaResponse:
    try:
        escola = db.query(Escola).filter(Escola.id == escola_id).first()
        if not escola:
            raise HTTPException(status_code=404, detail="Escola não encontrada")
        
        update_dict = {}
        atualizacoes = []
        
        # estado_liberacao não pode mais ser atualizado diretamente - é derivado das liberações
        if request.estado_liberacao is not None:
            logger.warning(f"Tentativa de atualizar estado_liberacao diretamente para escola {escola_id} - ignorado (campo derivado)")
        
        if request.numeracao_folha is not None:
            update_dict["numeracao_folha"] = request.numeracao_folha
            atualizacoes.append(f"numeracao_folha='{request.numeracao_folha}'")
        
        if not atualizacoes:
            raise HTTPException(
                status_code=400,
                detail="Nenhum campo fornecido para atualização. Informe 'numeracao_folha' (estado_liberacao é derivado das liberações)"
            )
        
        rows_updated = db.query(Escola)\
            .filter(Escola.id == escola_id)\
            .update(update_dict, synchronize_session=False)
        
        if rows_updated == 0:
            raise HTTPException(status_code=404, detail="Escola não encontrada para atualização")
        
        db.commit()
        
        db.expire_all()
        escola = db.query(Escola).filter(Escola.id == escola_id).first()
        
        logger.info(f"Escola {escola_id} atualizada: {', '.join(atualizacoes)}")
        
        return EscolaAtualizadaResponse(
            success=True,
            message=f"Escola atualizada: {', '.join(atualizacoes)}",
            escola_id=escola.id,
            nome_uex=escola.nome_uex,
            estado_liberacao=escola_esta_liberada(escola),
            numeracao_folha=escola.numeracao_folha
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Erro ao atualizar escola {escola_id}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar escola: {str(e)}")

