from typing import Any, Optional
import pandas as pd

def obter_quantidade(row: pd.Series, coluna: str) -> int:
    valor = row.get(coluna, 0)
    try:
        return int(valor) if pd.notna(valor) else 0
    except (ValueError, TypeError):
        return 0

def obter_quantidade_por_nome(row: pd.Series, nome_normalizado: str) -> int:
    nome_normalizado = nome_normalizado.strip().lower()
    for coluna in row.index:
        if isinstance(coluna, str) and coluna.strip().lower() == nome_normalizado:
            return obter_quantidade(row, coluna)
    return 0


def obter_texto(row: pd.Series, coluna: str, default: Optional[str] = "") -> str:
    valor: Any = row.get(coluna, default)
    try:
        return str(valor) if pd.notna(valor) else (default or "")
    except (ValueError, TypeError):
        return default or ""


def validar_indigena_e_quilombola(row: pd.Series, coluna: str) -> str:
    valor = row.get(coluna, "NÃO")
    try:
        return str(valor) if pd.notna(valor) else "NÃO"
    except (ValueError, TypeError):
        return "NÃO"


