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
from src.modules.features.anos.repository import AnoLetivoRepository
from src.modules.schemas.ano import AnoLetivoRead, AnoLetivoCreate


class AnoLetivoService:
    @staticmethod
    def listar_anos_letivos(db: Session) -> List[AnoLetivoRead]:
        repo = AnoLetivoRepository(db)
        anos = repo.find_all_ordered()
        
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
        repo = AnoLetivoRepository(db)
        
        # Verificar se ano já existe
        ano_existente = repo.find_by_ano(data.ano)
        if ano_existente:
            raise AnoLetivoJaExisteException(data.ano)
        
        # Arquivar ano ativo atual (se houver)
        ano_ativo_atual = repo.find_active()
        
        with transaction(db):
            if ano_ativo_atual:
                # Apenas arquivar o ano anterior (mantém uploads, escolas e cálculos para histórico)
                repo.update(
                    ano_ativo_atual,
                    status=StatusAnoLetivo.ARQUIVADO,
                    arquivado_em=datetime.now()
                )
                logger.info(f"Ano letivo {ano_ativo_atual.ano} arquivado (dados históricos preservados)")
            
            # Criar novo ano
            novo_ano = repo.create(
                ano=data.ano,
                status=StatusAnoLetivo.ATIVO,
                created_at=datetime.now()
            )
        
        return novo_ano
    
    @staticmethod
    def arquivar_ano_letivo(db: Session, ano_id: int) -> AnoLetivo:
        repo = AnoLetivoRepository(db)
        
        ano = repo.find_by_id(ano_id)
        if not ano:
            raise AnoLetivoNaoEncontradoException(ano_id)
        
        if ano.status == StatusAnoLetivo.ARQUIVADO:
            raise AnoLetivoJaArquivadoException(ano.ano)
        
        with transaction(db):
            repo.update(
                ano,
                status=StatusAnoLetivo.ARQUIVADO,
                arquivado_em=datetime.now()
            )
        
        return ano
    
    @staticmethod
    def deletar_ano_letivo(db: Session, ano_id: int) -> int:
        repo = AnoLetivoRepository(db)
        
        ano = repo.find_by_id(ano_id)
        if not ano:
            raise AnoLetivoNaoEncontradoException(ano_id)
        
        ano_numero = ano.ano
        
        with transaction(db):
            repo.delete(ano)  # Cascade deleta tudo relacionado
        
        return ano_numero

