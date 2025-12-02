import pandas as pd
from sqlalchemy.orm import Session
from src.modules.features.anos import AnoLetivo, StatusAnoLetivo
from fastapi import HTTPException
from typing import Optional, Tuple, Union


def obter_ano_letivo(
    db: Session,
    ano_letivo_id: Optional[int] = None,
    raise_if_not_found: bool = True
) -> Union[Tuple[AnoLetivo, int], Tuple[None, None]]:

    if ano_letivo_id is None:
        # Buscar ano letivo ativo
        ano_letivo = db.query(AnoLetivo).filter(
            AnoLetivo.status == StatusAnoLetivo.ATIVO
        ).first()
        
        if not ano_letivo:
            if raise_if_not_found:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhum ano letivo ativo encontrado. Crie um ano primeiro."
                )
            return None, None
        
        ano_letivo_id = ano_letivo.id
    else:
        # Buscar ano letivo por ID
        ano_letivo = db.query(AnoLetivo).filter(
            AnoLetivo.id == ano_letivo_id
        ).first()
        
        if not ano_letivo:
            if raise_if_not_found:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ano letivo ID {ano_letivo_id} não encontrado"
                )
            return None, None
    
    return ano_letivo, ano_letivo_id

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


def obter_texto(row: pd.Series, coluna: str, default: str = "") -> str:
    valor = row.get(coluna, default)
    try:
        return str(valor) if pd.notna(valor) else default
    except (ValueError, TypeError):
        return default

def validar_indigena_e_quilombola(row: pd.Series, coluna: str) -> str:
    valor = row.get(coluna, "NÃO")
    try:
        return str(valor) if pd.notna(valor) else "NÃO"
    except (ValueError, TypeError):
        return "NÃO"
