import pandas as pd
from src.modules.features.projetos.constants import COLUNAS_PROJETOS_APROVADOS
from src.modules.shared.utils import obter_quantidade_por_nome


def obter_quantidade_projetos_aprovados(row: pd.Series) -> int:
    for coluna in COLUNAS_PROJETOS_APROVADOS:
        quantidade = obter_quantidade_por_nome(row, coluna)
        if quantidade:
            return quantidade
    return 0

