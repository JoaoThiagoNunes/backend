from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, List, Dict, Any
from src.core.logging_config import logger
from src.modules.features.parcelas import ParcelasProfin, LiberacoesParcela
from src.modules.features.escolas import Escola
from src.modules.features.calculos import CalculosProfin
from src.modules.schemas.parcelas import LiberacaoParcelaInfo, EscolaPrevisaoInfo


class ParcelaService:
    @staticmethod
    def calcular_total_parcela(calculo: Optional[CalculosProfin], numero_parcela: int) -> float:
        if not calculo or not calculo.parcelas:
            return 0.0

        total_centavos = sum(
            parcela.valor_centavos
            for parcela in calculo.parcelas
            if parcela.numero_parcela == numero_parcela
        )

        return round(total_centavos / 100.0, 2)
    
    @staticmethod
    def mapear_liberacao_parcela(liberacao: LiberacoesParcela) -> LiberacaoParcelaInfo:
        escola = liberacao.escola

        return LiberacaoParcelaInfo(
            id=liberacao.id,
            escola_id=escola.id if escola else liberacao.escola_id,
            nome_uex=escola.nome_uex if escola else "",
            dre=escola.dre if escola else None,
            numero_parcela=liberacao.numero_parcela,
            liberada=liberacao.liberada,
            numero_folha=liberacao.numero_folha,
            data_liberacao=liberacao.data_liberacao,
            created_at=liberacao.created_at,
            updated_at=liberacao.updated_at
        )
    
    @staticmethod
    def build_previsao_info(
        escola: Escola,
        numero_parcela: int,
        liberacao: Optional[LiberacoesParcela]
    ) -> EscolaPrevisaoInfo:
        calculo = escola.calculos
        valor_total = ParcelaService.calcular_total_parcela(calculo, numero_parcela)

        liberada = False
        numero_folha = None
        if liberacao:
            liberada = liberacao.liberada
            numero_folha = liberacao.numero_folha

        return EscolaPrevisaoInfo(
            escola_id=escola.id,
            nome_uex=escola.nome_uex,
            dre=escola.dre,
            numero_parcela=numero_parcela,
            liberada=liberada,
            numero_folha=numero_folha,
            valor_total_reais=valor_total
        )

