from sqlalchemy.orm import Session
from datetime import datetime
from src.modules.features.uploads import Upload
from src.modules.features.uploads.repository import UploadRepository
from src.core.logging_config import logger


def obter_ou_criar_upload_ativo(db: Session, ano_letivo_id: int, filename: str) -> Upload:
    repo = UploadRepository(db)
    upload_existente = repo.find_active_by_ano_letivo(ano_letivo_id)
    
    if upload_existente:
        repo.update(
            upload_existente,
            filename=filename,
            upload_date=datetime.now(),
            total_escolas=0
        )
        logger.info(f"Atualizando upload existente ID {upload_existente.id} (substituindo dados)")
        return upload_existente
    else:
        # Criar novo upload
        novo_upload = repo.create(
            ano_letivo_id=ano_letivo_id,
            filename=filename,
            total_escolas=0,
            upload_date=datetime.now(),
            is_active=True
        )
        logger.info(f"Criando novo upload para ano letivo {ano_letivo_id}")
        return novo_upload

