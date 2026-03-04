from sqlalchemy.orm import Session
from typing import Optional, List
from src.modules.shared.repositories import BaseRepository
from .models import ComplementoUpload, ComplementoEscola, StatusComplemento


class ComplementoUploadRepository(BaseRepository[ComplementoUpload]):
    """
    Repositório para operações CRUD com ComplementoUpload.
    
    Herda de BaseRepository que já fornece métodos básicos:
    - create, find_by_id, find_all, update, delete
    """
    
    def __init__(self, db: Session):
        super().__init__(db, ComplementoUpload)
    
    def find_by_ano_letivo(self, ano_letivo_id: int) -> List[ComplementoUpload]:
        """Busca todos os complementos de um ano letivo."""
        return self.db.query(ComplementoUpload).filter(
            ComplementoUpload.ano_letivo_id == ano_letivo_id
        ).order_by(ComplementoUpload.upload_date.desc()).all()
    
    def find_by_upload_base(self, upload_base_id: int) -> List[ComplementoUpload]:
        """Busca todos os complementos baseados em um upload específico."""
        return self.db.query(ComplementoUpload).filter(
            ComplementoUpload.upload_base_id == upload_base_id
        ).all()


class ComplementoEscolaRepository(BaseRepository[ComplementoEscola]):
    """
    Repositório para operações CRUD com ComplementoEscola.
    """
    
    def __init__(self, db: Session):
        super().__init__(db, ComplementoEscola)
    
    def find_by_complemento_upload(self, complemento_upload_id: int) -> List[ComplementoEscola]:
        """Busca todos os complementos de escolas de um upload de complemento."""
        return self.db.query(ComplementoEscola).filter(
            ComplementoEscola.complemento_upload_id == complemento_upload_id
        ).all()
    
    def find_by_escola(self, escola_id: int) -> List[ComplementoEscola]:
        """Busca histórico de complementos de uma escola específica."""
        return self.db.query(ComplementoEscola).filter(
            ComplementoEscola.escola_id == escola_id
        ).order_by(ComplementoEscola.processed_at.desc()).all()
    
    def find_by_status(self, complemento_upload_id: int, status: StatusComplemento) -> List[ComplementoEscola]:
        """Busca escolas com um status específico em um complemento."""
        return self.db.query(ComplementoEscola).filter(
            ComplementoEscola.complemento_upload_id == complemento_upload_id,
            ComplementoEscola.status == status
        ).all()
    
    def delete_by_escola_id(self, escola_id: int) -> int:
        """Deleta todos os complementos de uma escola específica."""
        deleted = self.db.query(ComplementoEscola).filter(
            ComplementoEscola.escola_id == escola_id
        ).delete(synchronize_session=False)
        self.db.flush()
        return deleted
