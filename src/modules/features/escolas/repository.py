from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from src.modules.shared.repositories import BaseRepository
from src.modules.features.escolas import Escola
from src.modules.features.uploads import Upload


class EscolaRepository(BaseRepository[Escola]):
    def __init__(self, db: Session):
        super().__init__(db, Escola)
    
    def find_by_upload_id(self, upload_id: int) -> List[Escola]:
        return self.db.query(self.model).filter(
            Escola.upload_id == upload_id
        ).all()
    
    def find_by_nome_e_dre(self, nome_uex: str, dre: Optional[str], upload_id: int) -> Optional[Escola]:
        query = self.db.query(self.model).filter(
            Escola.upload_id == upload_id,
            Escola.nome_uex == nome_uex
        )
        if dre:
            query = query.filter(Escola.dre == dre)
        else:
            query = query.filter(Escola.dre.is_(None))
        return query.first()
    
    def find_by_ids(self, escola_ids: List[int]) -> List[Escola]:
        return self.db.query(self.model).filter(
            Escola.id.in_(escola_ids)
        ).all()
    
    def find_by_ano_letivo(self, ano_letivo_id: int) -> List[Escola]:
        return self.db.query(self.model).join(Upload).filter(
            Upload.ano_letivo_id == ano_letivo_id
        ).all()
    
    def find_by_ano_letivo_with_relations(
        self, 
        ano_letivo_id: int,
        load_calculos: bool = False,
        load_liberacoes_parcelas: bool = False,
        load_liberacoes_projetos: bool = False
    ) -> List[Escola]:
        query = self.db.query(self.model).join(Upload).filter(
            Upload.ano_letivo_id == ano_letivo_id
        )
        
        options = []
        if load_calculos:
            options.append(joinedload(Escola.calculos))
        if load_liberacoes_parcelas:
            options.append(joinedload(Escola.liberacoes_parcelas))
        if load_liberacoes_projetos:
            options.append(joinedload(Escola.liberacoes_projetos))
        
        if options:
            query = query.options(*options)
        
        return query.all()
    
    def count_by_upload_id(self, upload_id: int) -> int:
        return self.db.query(self.model).filter(
            Escola.upload_id == upload_id
        ).count()
    
    def create_map_by_nome_dre(self, upload_id: int) -> dict:
        escolas = self.find_by_upload_id(upload_id)
        return {
            (e.nome_uex, e.dre): e 
            for e in escolas
        }

