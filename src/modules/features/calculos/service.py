from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
from src.core.logging_config import logger
from src.core.database import transaction
from src.core.exceptions import (CalculoNaoEncontradoException, EscolaNaoEncontradaException)
from src.modules.features.calculos.repository import CalculoRepository
from src.modules.features.escolas.repository import EscolaRepository
from src.modules.schemas.calculos import EscolaCalculo
from src.modules.features.anos import obter_ano_letivo
from .utils import calcular_todas_cotas


class CalculoService:
    @staticmethod
    def listar_calculos(db: Session, ano_letivo_id: Optional[int] = None) -> Dict[str, Any]:
        ano_letivo, ano_id = obter_ano_letivo(db, ano_letivo_id)

        calculo_repo = CalculoRepository(db)
        calculos = calculo_repo.find_by_ano_letivo(ano_id)

        if not calculos:
            raise CalculoNaoEncontradoException(ano_letivo.ano)

        escolas_calculadas: List[EscolaCalculo] = []
        valor_total_geral = 0.0
        upload_id = None

        for calculo in calculos:
            escola = calculo.escola
            if not escola:
                continue

            upload_id = upload_id or escola.upload_id
            valor_total = calculo.valor_total or 0.0
            valor_total_geral += valor_total

            escolas_calculadas.append(
                EscolaCalculo(
                    id=escola.id,
                    dre=escola.dre,
                    nome_uex=escola.nome_uex,
                    profin_gestao=calculo.profin_gestao or 0.0,
                    profin_projeto=calculo.profin_projeto or 0.0,
                    profin_kit_escolar=calculo.profin_kit_escolar or 0.0,
                    profin_uniforme=calculo.profin_uniforme or 0.0,
                    profin_merenda=calculo.profin_merenda or 0.0,
                    profin_sala_recurso=calculo.profin_sala_recurso or 0.0,
                    profin_permanente=calculo.profin_permanente or 0.0,
                    # profin_climatizacao=calculo.profin_climatizacao or 0.0, # Desativado temporariamente
                    profin_preuni=calculo.profin_preuni or 0.0,
                    valor_total=valor_total,
                )
            )

        if not escolas_calculadas:
            raise CalculoNaoEncontradoException(ano_letivo.ano)

        return {
            "ano_letivo": ano_letivo,
            "ano_letivo_id": ano_id,
            "escolas_calculadas": escolas_calculadas,
            "valor_total_geral": round(valor_total_geral, 2),
            "upload_id": upload_id or 0,
        }
    
    @staticmethod
    def calcular_valores_para_ano(db: Session, ano_letivo_id: Optional[int] = None) -> Dict[str, Any]:
        ano_letivo, ano_letivo_id = obter_ano_letivo(db, ano_letivo_id)
        
        logger.info("="*60)
        logger.info(f"CALCULANDO VALORES - ANO LETIVO: {ano_letivo.ano}")
        logger.info("="*60)
        
        escola_repo = EscolaRepository(db)
        escolas = escola_repo.find_by_ano_letivo(ano_letivo_id)
        
        if not escolas:
            raise EscolaNaoEncontradaException(ano_letivo=ano_letivo.ano)
        
        calculo_repo = CalculoRepository(db)
        escolas_calculadas = []
        valor_total_geral = 0.0
        upload_id = escolas[0].upload_id if escolas else None
        
        with transaction(db):
            for escola_obj in escolas:
                row_data = {
                    "TOTAL": escola_obj.total_alunos,
                    "FUNDAMENTAL INICIAL": escola_obj.fundamental_inicial,
                    "FUNDAMENTAL FINAL": escola_obj.fundamental_final,
                    "FUNDAMENTAL INTEGRAL": escola_obj.fundamental_integral,
                    "PROFISSIONALIZANTE": escola_obj.profissionalizante,
                    "ALTERNÂNCIA": escola_obj.alternancia,
                    "ENSINO MÉDIO INTEGRAL": escola_obj.ensino_medio_integral,
                    "ENSINO MÉDIO REGULAR": escola_obj.ensino_medio_regular,
                    "ESPECIAL FUNDAMENTAL REGULAR": escola_obj.especial_fund_regular,
                    "ESPECIAL FUNDAMENTAL INTEGRAL": escola_obj.especial_fund_integral,
                    "ESPECIAL MÉDIO PARCIAL": escola_obj.especial_medio_parcial,
                    "ESPECIAL MÉDIO INTEGRAL": escola_obj.especial_medio_integral,
                    "SALA DE RECURSO": escola_obj.sala_recurso,
                    # "CLIMATIZAÇÃO": escola_obj.climatizacao, # Desativado temporariamente
                    "PREUNI": escola_obj.preuni,
                    "PROJETOS": escola_obj.quantidade_projetos_aprovados,
                    "INDIGENA & QUILOMBOLA": escola_obj.indigena_quilombola,
                    "REPASSE POR AREA": escola_obj.repasse_por_area,
                    "EPT": escola_obj.codigo_ept,
                    "INEP": escola_obj.codigo_inep,
                }
                
                row_series = pd.Series(row_data)
                cotas = calcular_todas_cotas(row_series)
                
                calculo_obj = calculo_repo.find_by_escola_id(escola_obj.id)
                
                if calculo_obj:
                    # Atualizar cálculo existente
                    calculo_repo.update(
                        calculo_obj,
                        profin_gestao=cotas["profin_gestao"],
                        profin_projeto=cotas["profin_projeto"],
                        profin_kit_escolar=cotas["profin_kit_escolar"],
                        profin_uniforme=cotas["profin_uniforme"],
                        profin_merenda=cotas["profin_merenda"],
                        profin_sala_recurso=cotas["profin_sala_recurso"],
                        profin_permanente=cotas["profin_permanente"],
                        # profin_climatizacao=cotas["profin_climatizacao"], # Desativado temporariamente
                        profin_preuni=cotas["profin_preuni"],
                        valor_total=cotas["valor_total"],
                        calculated_at=datetime.now()
                    )
                else:
                    # Criar novo cálculo
                    calculo_obj = calculo_repo.create(
                        escola_id=escola_obj.id,
                        profin_gestao=cotas["profin_gestao"],
                        profin_projeto=cotas["profin_projeto"],
                        profin_kit_escolar=cotas["profin_kit_escolar"],
                        profin_uniforme=cotas["profin_uniforme"],
                        profin_merenda=cotas["profin_merenda"],
                        profin_sala_recurso=cotas["profin_sala_recurso"],
                        profin_permanente=cotas["profin_permanente"],
                        # profin_climatizacao=cotas["profin_climatizacao"], # Desativado temporariamente
                        profin_preuni=cotas["profin_preuni"],
                        valor_total=cotas["valor_total"],
                        calculated_at=datetime.now()
                    )
                
                escola_data = {
                    "id": escola_obj.id,
                    "nome_uex": escola_obj.nome_uex,
                    "dre": escola_obj.dre,
                    **cotas
                }
                
                escolas_calculadas.append(escola_data)
                valor_total_geral += cotas["valor_total"]
        
        logger.info(f"Cálculos concluídos para {len(escolas_calculadas)} escolas")
        logger.info(f"Valor total: R$ {valor_total_geral:,.2f}")
        logger.info("="*60)
        
        return {
            "ano_letivo": ano_letivo,
            "ano_letivo_id": ano_letivo_id,
            "escolas_calculadas": escolas_calculadas,
            "valor_total_geral": round(valor_total_geral, 2),
            "upload_id": upload_id,
        }

