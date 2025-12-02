from typing import Optional
from src.modules.features.escolas import Escola
from src.modules.features.calculos import CalculosProfin
from src.modules.features.projetos.constants import VALOR_PROJETO_UNITARIO


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

