from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from src.core.logging_config import logger
from src.core.database import transaction
from src.core.exceptions import (
    AnoLetivoJaExisteException,
    AnoLetivoNaoEncontradoException,
    AnoLetivoJaArquivadoException
)
from src.modules.features.anos import AnoLetivo, StatusAnoLetivo
from src.modules.schemas.ano import AnoLetivoRead, AnoLetivoCreate


class AnoLetivoService:
    @staticmethod
    def listar_anos_letivos(db: Session) -> List[AnoLetivoRead]:
        anos = db.query(AnoLetivo).order_by(AnoLetivo.ano.desc()).all()
        
        return [
            AnoLetivoRead(
                id=ano.id,
                ano=ano.ano,
                status=ano.status.value,
                created_at=ano.created_at,
                arquivado_em=ano.arquivado_em,
                total_uploads=len(ano.uploads)
            )
            for ano in anos
        ]
    
    @staticmethod
    def criar_ano_letivo(db: Session, data: AnoLetivoCreate) -> AnoLetivo:
        # Verificar se ano já existe
        ano_existente = db.query(AnoLetivo).filter(AnoLetivo.ano == data.ano).first()
        if ano_existente:
            raise AnoLetivoJaExisteException(data.ano)
        
        # Arquivar ano ativo atual (se houver) - MANTÉM os dados históricos
        ano_ativo_atual = db.query(AnoLetivo).filter(
            AnoLetivo.status == StatusAnoLetivo.ATIVO
        ).first()
        
        with transaction(db):
            if ano_ativo_atual:
                # Apenas arquivar o ano anterior (mantém uploads, escolas e cálculos para histórico)
                ano_ativo_atual.status = StatusAnoLetivo.ARQUIVADO
                ano_ativo_atual.arquivado_em = datetime.now()
                logger.info(f"Ano letivo {ano_ativo_atual.ano} arquivado (dados históricos preservados)")
            
            # Criar novo ano
            novo_ano = AnoLetivo(
                ano=data.ano,
                status=StatusAnoLetivo.ATIVO,
                created_at=datetime.now()
            )
            db.add(novo_ano)
            db.flush()
            db.refresh(novo_ano)
        
        return novo_ano
    
    @staticmethod
    def arquivar_ano_letivo(db: Session, ano_id: int) -> AnoLetivo:
        ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_id).first()
        if not ano:
            raise AnoLetivoNaoEncontradoException(ano_id)
        
        if ano.status == StatusAnoLetivo.ARQUIVADO:
            raise AnoLetivoJaArquivadoException(ano.ano)
        
        with transaction(db):
            ano.status = StatusAnoLetivo.ARQUIVADO
            ano.arquivado_em = datetime.now()
        
        return ano
    
    @staticmethod
    def deletar_ano_letivo(db: Session, ano_id: int) -> int:
        ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_id).first()
        if not ano:
            raise AnoLetivoNaoEncontradoException(ano_id)
        
        ano_numero = ano.ano
        
        with transaction(db):
            db.delete(ano)  # Cascade deleta tudo relacionado
        
        return ano_numero

