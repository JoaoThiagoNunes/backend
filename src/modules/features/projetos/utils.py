import pandas as pd
from src.modules.shared.utils import obter_quantidade


def obter_quantidade_projetos_aprovados(row: pd.Series) -> int:
    return obter_quantidade(row, "QUANTIDADE DE PROJETOS APROVADOS")

