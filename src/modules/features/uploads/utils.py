from sqlalchemy.orm import Session
from datetime import datetime
from src.modules.features.uploads import Upload
from src.core.logging_config import logger


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

