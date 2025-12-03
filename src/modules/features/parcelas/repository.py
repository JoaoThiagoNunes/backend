from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.modules.shared.repositories import BaseRepository
from src.modules.features.parcelas import ParcelasProfin, LiberacoesParcela
from src.modules.features.calculos import TipoCota


class ParcelaRepository(BaseRepository[ParcelasProfin]):    
    def __init__(self, db: Session):
        super().__init__(db, ParcelasProfin)
    
    def find_by_calculo_id(self, calculo_id: int) -> List[ParcelasProfin]:
        return self.db.query(self.model).filter(
            ParcelasProfin.calculo_id == calculo_id
        ).order_by(
            ParcelasProfin.tipo_cota,
            ParcelasProfin.numero_parcela,
            ParcelasProfin.tipo_ensino
        ).all()
    
    def find_by_calculo_and_cotas(
        self, 
        calculo_id: int, 
        cotas: List[TipoCota]
    ) -> List[ParcelasProfin]:
        return self.db.query(self.model).filter(
            ParcelasProfin.calculo_id == calculo_id,
            ParcelasProfin.tipo_cota.in_(cotas)
        ).order_by(
            ParcelasProfin.tipo_cota,
            ParcelasProfin.numero_parcela,
            ParcelasProfin.tipo_ensino
        ).all()
    
    def delete_by_calculo_id(self, calculo_id: int) -> int:
        deleted = self.db.query(self.model).filter(
            ParcelasProfin.calculo_id == calculo_id
        ).delete(synchronize_session=False)
        self.db.flush()
        return deleted


class LiberacaoParcelaRepository(BaseRepository[LiberacoesParcela]):    
    def __init__(self, db: Session):
        super().__init__(db, LiberacoesParcela)
    
    def find_by_escola_id(self, escola_id: int) -> List[LiberacoesParcela]:
        return self.db.query(self.model).filter(
            LiberacoesParcela.escola_id == escola_id
        ).order_by(LiberacoesParcela.numero_parcela).all()
    
    def find_by_escola_and_parcela(
        self, 
        escola_id: int, 
        numero_parcela: int
    ) -> Optional[LiberacoesParcela]:
        return self.db.query(self.model).filter(
            LiberacoesParcela.escola_id == escola_id,
            LiberacoesParcela.numero_parcela == numero_parcela
        ).first()
    
    def find_by_escolas_ids_and_parcela(
        self,
        escola_ids: List[int],
        numero_parcela: int
    ) -> List[LiberacoesParcela]:
        return self.db.query(self.model).filter(
            LiberacoesParcela.escola_id.in_(escola_ids),
            LiberacoesParcela.numero_parcela == numero_parcela
        ).all()
    
    def find_by_folha(
        self,
        numero_folha: int,
        numero_parcela: Optional[int] = None
    ) -> List[LiberacoesParcela]:
        query = self.db.query(self.model).filter(
            LiberacoesParcela.numero_folha == numero_folha
        )
        if numero_parcela:
            query = query.filter(LiberacoesParcela.numero_parcela == numero_parcela)
        return query.options(joinedload(LiberacoesParcela.escola)).all()
    
    def find_liberadas(
        self,
        numero_parcela: Optional[int] = None,
        numero_folha: Optional[int] = None
    ) -> List[LiberacoesParcela]:
        query = self.db.query(self.model).filter(
            LiberacoesParcela.liberada == True
        )
        if numero_parcela:
            query = query.filter(LiberacoesParcela.numero_parcela == numero_parcela)
        if numero_folha:
            query = query.filter(LiberacoesParcela.numero_folha == numero_folha)
        return query.options(joinedload(LiberacoesParcela.escola)).all()
    
    def create_map_by_escola_parcela(
        self,
        escola_ids: List[int],
        numero_parcela: int
    ) -> dict:
        liberacoes = self.find_by_escolas_ids_and_parcela(escola_ids, numero_parcela)
        return {liberacao.escola_id: liberacao for liberacao in liberacoes}

