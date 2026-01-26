from sqlalchemy.orm import Session
from datetime import datetime
from src.modules.features.uploads import Upload
from src.modules.features.uploads.repository import UploadRepository, ContextoAtivoRepository
from src.core.logging_config import logger


def obter_ou_criar_upload_ativo(db: Session, ano_letivo_id: int, filename: str) -> Upload:
    """Cria um novo upload e atualiza o contexto ativo para apontar para ele"""
    upload_repo = UploadRepository(db)
    contexto_repo = ContextoAtivoRepository(db)
    
    # Sempre criar novo upload (não atualizar existente para preservar histórico)
    novo_upload = upload_repo.create(
        ano_letivo_id=ano_letivo_id,
        filename=filename,
        total_escolas=0,
        upload_date=datetime.now()
    )
    
    # Ativar o novo upload no contexto
    contexto_repo.ativar_upload(ano_letivo_id, novo_upload.id)
    
    logger.info(f"Criando novo upload ID {novo_upload.id} para ano letivo {ano_letivo_id} e ativando no contexto")
    return novo_upload

