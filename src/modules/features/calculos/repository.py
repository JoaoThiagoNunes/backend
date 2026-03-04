from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.modules.shared.repositories import BaseRepository
from src.modules.features.calculos import CalculosProfin
from src.modules.features.escolas import Escola
from src.modules.features.uploads import Upload


class CalculoRepository(BaseRepository[CalculosProfin]):
    def __init__(self, db: Session):
        super().__init__(db, CalculosProfin)

    def delete_all(self) -> int:
        deleted = self.db.query(self.model).delete(synchronize_session=False)
        self.db.flush()
        return deleted
    
    def find_by_escola_id(self, escola_id: int) -> Optional[CalculosProfin]:
        return self.db.query(self.model).filter(
            CalculosProfin.escola_id == escola_id
        ).first()
    
    def find_by_ano_letivo(self, ano_letivo_id: int) -> List[CalculosProfin]:
        return (
            self.db.query(self.model)
            .join(Escola)
            .join(Upload)
            .options(joinedload(CalculosProfin.escola))
            .filter(Upload.ano_letivo_id == ano_letivo_id)
            .all()
        )
    
    def find_by_ano_letivo_with_parcelas(self, ano_letivo_id: int) -> List[CalculosProfin]:
        return (
            self.db.query(self.model)
            .join(Escola)
            .join(Upload)
            .options(
                joinedload(CalculosProfin.escola),
                joinedload(CalculosProfin.parcelas)
            )
            .filter(Upload.ano_letivo_id == ano_letivo_id)
            .all()
        )
    
    def find_by_escolas_ids(self, escola_ids: List[int]) -> List[CalculosProfin]:
        return self.db.query(self.model).filter(
            CalculosProfin.escola_id.in_(escola_ids)
        ).all()

