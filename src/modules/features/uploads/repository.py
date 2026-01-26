from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from src.modules.shared.repositories import BaseRepository
from src.modules.features.uploads import Upload, ContextoAtivo


class ContextoAtivoRepository(BaseRepository[ContextoAtivo]):
    def __init__(self, db: Session):
        super().__init__(db, ContextoAtivo)
    
    def find_by_ano_letivo(self, ano_letivo_id: int) -> Optional[ContextoAtivo]:
        return self.db.query(self.model).filter(
            ContextoAtivo.ano_letivo_id == ano_letivo_id
        ).first()
    
    def find_upload_ativo(self, ano_letivo_id: int) -> Optional[Upload]:
        contexto = self.find_by_ano_letivo(ano_letivo_id)
        if contexto:
            return contexto.upload
        return None
    
    def ativar_upload(self, ano_letivo_id: int, upload_id: int) -> ContextoAtivo:
        """Ativa um upload para um ano letivo, desativando o anterior se existir"""
        contexto_existente = self.find_by_ano_letivo(ano_letivo_id)
        
        if contexto_existente:
            # Atualizar contexto existente
            self.update(
                contexto_existente,
                upload_id=upload_id,
                ativado_em=datetime.now()
            )
            return contexto_existente
        else:
            # Criar novo contexto
            return self.create(
                ano_letivo_id=ano_letivo_id,
                upload_id=upload_id
            )


class UploadRepository(BaseRepository[Upload]):
    def __init__(self, db: Session):
        super().__init__(db, Upload)
    
    def find_by_ano_letivo(self, ano_letivo_id: int) -> Optional[Upload]:
        return self.db.query(self.model).filter(
            Upload.ano_letivo_id == ano_letivo_id
        ).first()
    
    def find_latest(self, ano_letivo_id: Optional[int] = None) -> Optional[Upload]:
        query = self.db.query(self.model)
        if ano_letivo_id:
            query = query.filter(Upload.ano_letivo_id == ano_letivo_id)
        return query.order_by(Upload.upload_date.desc()).first()
    
    def find_all_by_ano_letivo(self, ano_letivo_id: int) -> List[Upload]:
        return self.db.query(self.model).filter(
            Upload.ano_letivo_id == ano_letivo_id
        ).order_by(Upload.upload_date.desc()).all()

