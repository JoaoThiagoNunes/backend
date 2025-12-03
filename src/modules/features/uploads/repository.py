from typing import List, Optional
from sqlalchemy.orm import Session
from src.modules.shared.repositories import BaseRepository
from src.modules.features.uploads import Upload


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
    
    def find_active_by_ano_letivo(self, ano_letivo_id: int) -> Optional[Upload]:
        return self.db.query(self.model).filter(
            Upload.ano_letivo_id == ano_letivo_id,
            Upload.is_active == True
        ).first()
    
    def find_all_by_ano_letivo(self, ano_letivo_id: int) -> List[Upload]:
        return self.db.query(self.model).filter(
            Upload.ano_letivo_id == ano_letivo_id
        ).order_by(Upload.upload_date.desc()).all()

