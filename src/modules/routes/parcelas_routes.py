from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from src.core.database import get_db
from src.core.logging_config import logger
from src.core.utils import (
    obter_ano_letivo,
    calcular_porcentagens_ensino,
    dividir_cota_em_parcelas_por_ensino
)
from src.modules.models import (
    CalculosProfin, Escola, TipoCota, TipoEnsino, ParcelasProfin, Upload
)
from src.modules.schemas.parcelas import (
    SepararParcelasRequest, SepararParcelasResponse,
    EscolaParcelas, ParcelaPorCota, ParcelasEscolaResponse, ParcelaDetalhe
)
from datetime import datetime


router = APIRouter()


@router.post("", response_model=SepararParcelasResponse, tags=["Parcelas"])
def separar_valores_em_parcelas(
    request: SepararParcelasRequest,
    db: Session = Depends(get_db)
) -> SepararParcelasResponse:
    """
    Divide os valores das cotas em 2 parcelas e subdivide cada parcela por tipo de ensino.
    
    Fluxo:
    1. Busca todos os cálculos do ano letivo
    2. Para cada cálculo, calcula % de alunos (fundamental vs médio)
    3. Divide cada cota em 2 parcelas
    4. Divide cada parcela por tipo de ensino baseado na % de alunos
    
    Args:
        request: Dados da requisição (ano_letivo_id, recalcular, calculation_version)
        db: Sessão do banco de dados
    
    Returns:
        SepararParcelasResponse com todas as parcelas criadas
    """
    try:
        # 1. Determinar ano letivo
        ano_letivo, ano_letivo_id = obter_ano_letivo(db, request.ano_letivo_id)
        
        # Versão do cálculo (para auditoria)
        calculation_version = request.calculation_version or f"v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("="*60)
        logger.info(f"SEPARANDO VALORES EM PARCELAS - ANO LETIVO: {ano_letivo.ano}")
        logger.info(f"Versão do cálculo: {calculation_version}")
        logger.info("="*60)
        
        # 2. Buscar todos os cálculos do ano letivo COM EAGER LOADING
        # Otimização: Carrega escolas junto para evitar N+1 queries
        calculos = db.query(CalculosProfin)\
            .join(Escola, CalculosProfin.escola_id == Escola.id)\
            .join(Upload, Escola.upload_id == Upload.id)\
            .options(joinedload(CalculosProfin.escola))\
            .filter(Upload.ano_letivo_id == ano_letivo_id)\
            .all()
        
        if not calculos:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum cálculo encontrado para o ano letivo {ano_letivo.ano}. Execute /calculos primeiro."
            )
        
        # Lista de cotas que devem ser processadas (apenas as especificadas)
        # merenda, gestão (custeio), preuni, climatização, sala de recurso, uniforme, permanente e kit escolar
        # Formato: (nome_exibicao, campo_banco, enum_tipo_cota)
        COTAS_PROCESSAR = [
            ("merenda", "profin_merenda", "merenda"),
            ("gestao", "profin_custeio", "custeio"),  # Exibe "gestao" mas usa TipoCota.CUSTEIO internamente
            ("preuni", "profin_preuni", "preuni"),
            ("climatizacao", "profin_climatizacao", "climatizacao"),
            ("sala_recurso", "profin_sala_recurso", "sala_recurso"),
            ("uniforme", "profin_uniforme", "uniforme"),
            ("permanente", "profin_permanente", "permanente"),
            ("kit_escolar", "profin_kit_escolar", "kit_escolar"),
        ]
        
        # 3. Verificar idempotência: se já existem parcelas e não é para recalcular
        if not request.recalcular:
            # Verificar apenas parcelas das cotas especificadas
            cotas_processar_enum = [TipoCota(c[2]) for c in COTAS_PROCESSAR]  # Usa o enum (terceiro elemento)
            calculos_com_parcelas = db.query(ParcelasProfin.calculo_id)\
                .join(CalculosProfin, ParcelasProfin.calculo_id == CalculosProfin.id)\
                .join(Escola, CalculosProfin.escola_id == Escola.id)\
                .join(Upload, Escola.upload_id == Upload.id)\
                .filter(
                    Upload.ano_letivo_id == ano_letivo_id,
                    ParcelasProfin.tipo_cota.in_(cotas_processar_enum)
                )\
                .distinct()\
                .all()
            
            if calculos_com_parcelas:
                calculos_ids_com_parcelas = {row[0] for row in calculos_com_parcelas}
                calculos_sem_parcelas = [c for c in calculos if c.id not in calculos_ids_com_parcelas]
                
                if not calculos_sem_parcelas:
                    logger.info("✅ Todas as escolas já têm parcelas criadas. Use recalcular=true para recalcular.")
                    # Retornar parcelas existentes (apenas das cotas especificadas)
                    cotas_processar_enum = [TipoCota(c[2]) for c in COTAS_PROCESSAR]  # Usa o enum (terceiro elemento)
                    parcelas_existentes = db.query(ParcelasProfin)\
                        .join(CalculosProfin, ParcelasProfin.calculo_id == CalculosProfin.id)\
                        .join(Escola, CalculosProfin.escola_id == Escola.id)\
                        .join(Upload, Escola.upload_id == Upload.id)\
                        .filter(
                            Upload.ano_letivo_id == ano_letivo_id,
                            ParcelasProfin.tipo_cota.in_(cotas_processar_enum)
                        )\
                        .all()
                    
                    # Agrupar por escola
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
                        
                        # Agrupar parcelas por cota (apenas as cotas especificadas)
                        cota_enum_value = parcela.tipo_cota.value  # Valor do enum (ex: "custeio")
                        
                        # Encontrar o nome de exibição correspondente (mapear enum -> nome_exibicao)
                        cota_exibicao = None
                        campo_cota = None
                        for nome_exib, campo, enum_val in COTAS_PROCESSAR:
                            if enum_val == cota_enum_value:
                                cota_exibicao = nome_exib
                                campo_cota = campo
                                break
                        
                        if not cota_exibicao:
                            continue  # Pular cotas que não devem ser processadas
                        
                        if cota_exibicao not in escolas_dict[escola_id]["parcelas_por_cota"]:
                            valor_cota = getattr(calculo, campo_cota, 0.0)
                            escolas_dict[escola_id]["parcelas_por_cota"][cota_exibicao] = {
                                "tipo_cota": cota_exibicao,  # Usa nome de exibição (ex: "gestao")
                                "valor_total_reais": valor_cota,
                                "parcela_1": {"fundamental": 0.0, "medio": 0.0},
                                "parcela_2": {"fundamental": 0.0, "medio": 0.0},
                                "porcentagens": {
                                    "fundamental": escolas_dict[escola_id]["pct_fundamental"],
                                    "medio": escolas_dict[escola_id]["pct_medio"]
                                }
                            }
                        
                        # Adicionar valor da parcela
                        parcela_key = f"parcela_{parcela.numero_parcela}"
                        ensino_key = parcela.tipo_ensino.value
                        valor_reais = parcela.valor_centavos / 100.0
                        escolas_dict[escola_id]["parcelas_por_cota"][cota_exibicao][parcela_key][ensino_key] = valor_reais
                    
                    # Construir resposta
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
                                ]
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
            # Deletar parcelas existentes se for recalcular (apenas das cotas especificadas)
            calculos_ids = [c.id for c in calculos]
            cotas_processar_enum = [TipoCota(c[2]) for c in COTAS_PROCESSAR]  # Usa o enum (terceiro elemento)
            if calculos_ids:
                db.query(ParcelasProfin)\
                    .filter(
                        ParcelasProfin.calculo_id.in_(calculos_ids),
                        ParcelasProfin.tipo_cota.in_(cotas_processar_enum)
                    )\
                    .delete(synchronize_session=False)
                logger.info(f"🗑️ Parcelas antigas deletadas para recalcular (apenas cotas especificadas)")
        
        # 4. Processar cada cálculo
        escolas_processadas = []
        total_parcelas_criadas = 0
        
        for calculo in calculos:
            # Escola já carregada via eager loading (sem query extra!)
            escola = calculo.escola
            if not escola:
                logger.warning(f"Escola não encontrada para cálculo {calculo.id}")
                continue
            
            # Calcular porcentagens de ensino
            pct_fundamental, pct_medio = calcular_porcentagens_ensino(escola)
            
            # Processar cada cota (apenas as especificadas)
            parcelas_por_cota = []
            
            for nome_exibicao, campo_cota, enum_valor in COTAS_PROCESSAR:
                # Obter valor da cota
                valor_cota = getattr(calculo, campo_cota, 0.0)
                
                if valor_cota <= 0:
                    continue
                
                # Dividir cota em parcelas por ensino
                divisao = dividir_cota_em_parcelas_por_ensino(
                    valor_cota,
                    pct_fundamental,
                    pct_medio
                )
                
                # Criar registros de parcelas (usa enum_valor para TipoCota, mas nome_exibicao para resposta)
                tipo_cota_enum = TipoCota(enum_valor)  # Usa valor do enum (ex: "custeio")
                
                # Parcela 1 - Fundamental
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
                
                # Parcela 1 - Médio
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
                
                # Parcela 2 - Fundamental
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
                
                # Parcela 2 - Médio
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
                
                # Adicionar ao resultado (usa nome_exibicao para exibição)
                parcelas_por_cota.append(
                    ParcelaPorCota(
                        tipo_cota=nome_exibicao,  # Usa nome de exibição (ex: "gestao")
                        valor_total_reais=valor_cota,
                        parcela_1={
                            "fundamental": divisao["parcela_1"]["fundamental"] / 100.0,
                            "medio": divisao["parcela_1"]["medio"] / 100.0
                        },
                        parcela_2={
                            "fundamental": divisao["parcela_2"]["fundamental"] / 100.0,
                            "medio": divisao["parcela_2"]["medio"] / 100.0
                        },
                        porcentagens={
                            "fundamental": pct_fundamental,
                            "medio": pct_medio
                        }
                    )
                )
            
            # Adicionar escola processada
            escolas_processadas.append(
                EscolaParcelas(
                    escola_id=escola.id,
                    nome_uex=escola.nome_uex,
                    dre=escola.dre,
                    porcentagem_fundamental=pct_fundamental,
                    porcentagem_medio=pct_medio,
                    parcelas_por_cota=parcelas_por_cota
                )
            )
        
        # Commit final
        db.commit()
        
        logger.info(f"✅ Parcelas criadas para {len(escolas_processadas)} escolas")
        logger.info(f"📊 Total de parcelas: {total_parcelas_criadas}")
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
        logger.exception("❌ Erro ao separar valores em parcelas")
        raise HTTPException(status_code=500, detail=f"Erro ao separar valores: {str(e)}")


@router.get("/escola/{escola_id}", response_model=ParcelasEscolaResponse, tags=["Parcelas"])
def obter_parcelas_escola(
    escola_id: int,
    db: Session = Depends(get_db)
) -> ParcelasEscolaResponse:
    """
    Retorna todas as parcelas de uma escola específica (apenas das cotas especificadas).
    """
    escola = db.query(Escola).filter(Escola.id == escola_id).first()
    if not escola:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    
    calculo = db.query(CalculosProfin).filter(CalculosProfin.escola_id == escola_id).first()
    if not calculo:
        raise HTTPException(status_code=404, detail="Nenhum cálculo encontrado para esta escola")
    
    # Filtrar apenas as cotas especificadas
    # Formato: (nome_exibicao, campo_banco, enum_tipo_cota)
    COTAS_PROCESSAR = [
        ("merenda", "profin_merenda", "merenda"),
        ("gestao", "profin_custeio", "custeio"),  # Exibe "gestao" mas usa TipoCota.CUSTEIO internamente
        ("preuni", "profin_preuni", "preuni"),
        ("climatizacao", "profin_climatizacao", "climatizacao"),
        ("sala_recurso", "profin_sala_recurso", "sala_recurso"),
        ("uniforme", "profin_uniforme", "uniforme"),
        ("permanente", "profin_permanente", "permanente"),
        ("kit_escolar", "profin_kit_escolar", "kit_escolar"),
    ]
    cotas_processar_enum = [TipoCota(c[2]) for c in COTAS_PROCESSAR]  # Usa o enum (terceiro elemento)
    
    parcelas = db.query(ParcelasProfin)\
        .filter(
            ParcelasProfin.calculo_id == calculo.id,
            ParcelasProfin.tipo_cota.in_(cotas_processar_enum)
        )\
        .order_by(ParcelasProfin.tipo_cota, ParcelasProfin.numero_parcela, ParcelasProfin.tipo_ensino)\
        .all()
    
    if not parcelas:
        raise HTTPException(status_code=404, detail="Nenhuma parcela encontrada para esta escola. Execute /parcelas primeiro.")
    
    # Calcular porcentagens
    pct_fundamental, pct_medio = calcular_porcentagens_ensino(escola)
    
    # Mapear tipo_cota.value (enum) para nome de exibição
    def mapear_cota_exibicao(enum_value: str) -> str:
        for nome_exib, _, enum_val in COTAS_PROCESSAR:
            if enum_val == enum_value:
                return nome_exib
        return enum_value  # Retorna o valor original se não encontrar
    
    parcelas_detalhes = [
        ParcelaDetalhe(
            id=p.id,
            tipo_cota=mapear_cota_exibicao(p.tipo_cota.value),  # Mapeia "custeio" -> "gestao"
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
        parcelas=parcelas_detalhes
    )
