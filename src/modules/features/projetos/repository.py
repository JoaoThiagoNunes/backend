from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.modules.shared.repositories import BaseRepository
from src.modules.features.projetos import LiberacoesProjeto
from src.modules.features.escolas import Escola
from src.modules.features.uploads import Upload


class ProjetoRepository(BaseRepository[LiberacoesProjeto]):    
    def __init__(self, db: Session):
        super().__init__(db, LiberacoesProjeto)
    
    def find_by_escola_id(self, escola_id: int) -> Optional[LiberacoesProjeto]:
        return self.db.query(self.model).filter(
            LiberacoesProjeto.escola_id == escola_id
        ).first()
    
    def find_by_escolas_ids(self, escola_ids: List[int]) -> List[LiberacoesProjeto]:
        return self.db.query(self.model).filter(
            LiberacoesProjeto.escola_id.in_(escola_ids)
        ).all()
    
    def find_by_ano_letivo(
        self,
        ano_letivo_id: int,
        numero_folha: Optional[int] = None,
        liberada: Optional[bool] = None
    ) -> List[LiberacoesProjeto]:
        query = (
            self.db.query(self.model)
            .join(Escola)
            .join(Upload, Escola.upload_id == Upload.id)
            .filter(Upload.ano_letivo_id == ano_letivo_id)
        )
        
        if numero_folha is not None:
            query = query.filter(LiberacoesProjeto.numero_folha == numero_folha)
        
        if liberada is not None:
            query = query.filter(LiberacoesProjeto.liberada == liberada)
        
        return query.options(joinedload(LiberacoesProjeto.escola)).all()
    
    def find_by_folha(
        self,
        numero_folha: int,
        liberada: bool = True
    ) -> List[LiberacoesProjeto]:
        query = self.db.query(self.model).filter(
            LiberacoesProjeto.numero_folha == numero_folha
        )
        if liberada:
            query = query.filter(LiberacoesProjeto.liberada == True)
        return query.options(joinedload(LiberacoesProjeto.escola)).order_by(
            Escola.nome_uex
        ).all()
    
    def find_all_with_filters(
        self,
        numero_folha: Optional[int] = None,
        liberada: Optional[bool] = None,
        escola_id: Optional[int] = None,
        ano_letivo_id: Optional[int] = None
    ) -> List[LiberacoesProjeto]:
        query = self.db.query(self.model)
        
        if ano_letivo_id is not None:
            query = query.join(Escola).join(Upload, Escola.upload_id == Upload.id)
            query = query.filter(Upload.ano_letivo_id == ano_letivo_id)
        else:
            query = query.join(Escola)
        
        if numero_folha is not None:
            query = query.filter(LiberacoesProjeto.numero_folha == numero_folha)
        
        if liberada is not None:
            query = query.filter(LiberacoesProjeto.liberada == liberada)
        
        if escola_id is not None:
            query = query.filter(LiberacoesProjeto.escola_id == escola_id)
        
        return query.options(joinedload(LiberacoesProjeto.escola)).order_by(
            LiberacoesProjeto.numero_folha.nulls_last(),
            Escola.nome_uex
        ).all()
    
    def create_map_by_escola_id(self, escola_ids: List[int]) -> dict:
        liberacoes = self.find_by_escolas_ids(escola_ids)
        return {liberacao.escola_id: liberacao for liberacao in liberacoes}

