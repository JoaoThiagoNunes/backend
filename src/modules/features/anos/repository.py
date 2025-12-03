from typing import List, Optional
from sqlalchemy.orm import Session
from src.modules.shared.repositories import BaseRepository
from src.modules.features.anos import AnoLetivo, StatusAnoLetivo


class AnoLetivoRepository(BaseRepository[AnoLetivo]):
    def __init__(self, db: Session):
        super().__init__(db, AnoLetivo)
    
    def find_by_ano(self, ano: int) -> Optional[AnoLetivo]:
        return self.db.query(self.model).filter(AnoLetivo.ano == ano).first()
    
    def find_active(self) -> Optional[AnoLetivo]:
        return self.db.query(self.model).filter(
            AnoLetivo.status == StatusAnoLetivo.ATIVO
        ).first()
    
    def find_all_ordered(self) -> List[AnoLetivo]:
        return self.db.query(self.model).order_by(AnoLetivo.ano.desc()).all()
    
    def find_archived(self) -> List[AnoLetivo]:
        return self.db.query(self.model).filter(
            AnoLetivo.status == StatusAnoLetivo.ARQUIVADO
        ).order_by(AnoLetivo.ano.desc()).all()

