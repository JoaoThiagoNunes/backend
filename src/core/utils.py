"""
Utilitários genéricos compartilhados entre módulos.
Funções específicas de domínio devem estar em seus respectivos módulos.
"""
import pandas as pd
from sqlalchemy.orm import Session
from src.modules.features.uploads import Upload
from src.modules.features.anos import AnoLetivo, StatusAnoLetivo
from src.core.logging_config import logger
from fastapi import HTTPException
from typing import Optional, Tuple, Union
from datetime import datetime

# ==================
# BUSCAS E LIMPEZA
# ==================
VALOR_PROJETO_UNITARIO = 5000.0
COLUNAS_PROJETOS_APROVADOS = [
    "quantidade de projetos aprovados",
    "quantidade de projetos",
    "qtd de projetos",
    "qtd projetos",
    "projetos aprovados",
    "projetos",
]


def obter_ou_criar_upload_ativo(db: Session, ano_letivo_id: int, filename: str) -> Upload:
    upload_existente = db.query(Upload).filter(
        Upload.ano_letivo_id == ano_letivo_id,
        Upload.is_active == True
    ).first()
    
    if upload_existente:
        upload_existente.filename = filename
        upload_existente.upload_date = datetime.now()
        upload_existente.total_escolas = 0 
        logger.info(f"📝 Atualizando upload existente ID {upload_existente.id} (substituindo dados)")
        return upload_existente
    else:
        # Criar novo upload
        novo_upload = Upload(
            ano_letivo_id=ano_letivo_id,
            filename=filename,
            total_escolas=0,
            upload_date=datetime.now(),
            is_active=True
        )
        db.add(novo_upload)
        logger.info(f"✨ Criando novo upload para ano letivo {ano_letivo_id}")
        return novo_upload

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


def obter_quantidade_projetos_aprovados(row: pd.Series) -> int:
    for coluna in COLUNAS_PROJETOS_APROVADOS:
        quantidade = obter_quantidade_por_nome(row, coluna)
        if quantidade:
            return quantidade
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
