from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from src.modules.shared.repositories import BaseRepository
from .models import ComplementoUpload, ComplementoEscola, StatusComplemento, LiberacoesComplemento, ParcelasComplemento


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
    
    def find_by_upload_base_and_ano(self, upload_base_id: int, ano_letivo_id: int) -> Optional[ComplementoUpload]:
        """Busca complemento existente para um upload base e ano letivo específicos."""
        return self.db.query(ComplementoUpload).filter(
            ComplementoUpload.upload_base_id == upload_base_id,
            ComplementoUpload.ano_letivo_id == ano_letivo_id
        ).first()
    
    def delete_all_by_upload_base_and_ano(self, upload_base_id: int, ano_letivo_id: int) -> int:
        """Deleta todos os complementos para um upload base e ano letivo específicos."""
        complementos = self.db.query(ComplementoUpload).filter(
            ComplementoUpload.upload_base_id == upload_base_id,
            ComplementoUpload.ano_letivo_id == ano_letivo_id
        ).all()
        
        count = len(complementos)
        for complemento in complementos:
            self.db.delete(complemento)
        
        self.db.flush()
        return count
    
    def delete_all_by_ano_letivo(self, ano_letivo_id: int) -> int:
        """Deleta todos os complementos de um ano letivo específico."""
        complementos = self.db.query(ComplementoUpload).filter(
            ComplementoUpload.ano_letivo_id == ano_letivo_id
        ).all()
        
        count = len(complementos)
        for complemento in complementos:
            self.db.delete(complemento)
        
        self.db.flush()
        return count
    
    def find_mais_recente_by_ano_letivo(self, ano_letivo_id: int) -> Optional[ComplementoUpload]:
        """Busca o complemento upload mais recente de um ano letivo."""
        return self.db.query(ComplementoUpload).filter(
            ComplementoUpload.ano_letivo_id == ano_letivo_id
        ).order_by(ComplementoUpload.upload_date.desc()).first()


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
        result = self.db.query(ComplementoEscola).filter(
            ComplementoEscola.escola_id == escola_id
        ).order_by(ComplementoEscola.processed_at.desc()).all()
        return result
    
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


class LiberacaoComplementoRepository(BaseRepository[LiberacoesComplemento]):
    """
    Repositório para operações CRUD com LiberacoesComplemento.
    """
    
    def __init__(self, db: Session):
        super().__init__(db, LiberacoesComplemento)
    
    def find_by_escola(self, escola_id: int, complemento_upload_id: Optional[int] = None) -> Optional[LiberacoesComplemento]:
        """Busca liberação de complemento de uma escola específica."""
        query = self.db.query(self.model).filter(
            LiberacoesComplemento.escola_id == escola_id
        )
        if complemento_upload_id:
            query = query.filter(LiberacoesComplemento.complemento_upload_id == complemento_upload_id)
        return query.first()
    
    def find_by_folha(
        self,
        numero_folha: int,
        complemento_upload_id: Optional[int] = None
    ) -> List[LiberacoesComplemento]:
        """Busca todas as liberações de uma folha específica."""
        query = self.db.query(self.model).filter(
            LiberacoesComplemento.numero_folha == numero_folha
        )
        if complemento_upload_id:
            query = query.filter(LiberacoesComplemento.complemento_upload_id == complemento_upload_id)
        return query.options(joinedload(LiberacoesComplemento.escola)).all()
    
    def find_liberadas(
        self,
        numero_folha: Optional[int] = None,
        complemento_upload_id: Optional[int] = None
    ) -> List[LiberacoesComplemento]:
        """Busca todas as liberações liberadas, opcionalmente filtradas por folha e upload."""
        query = self.db.query(self.model).filter(
            LiberacoesComplemento.liberada == True
        )
        if numero_folha:
            query = query.filter(LiberacoesComplemento.numero_folha == numero_folha)
        if complemento_upload_id:
            query = query.filter(LiberacoesComplemento.complemento_upload_id == complemento_upload_id)
        return query.options(joinedload(LiberacoesComplemento.escola)).all()
    
    def find_by_escolas_ids(
        self,
        escola_ids: List[int],
        complemento_upload_id: Optional[int] = None
    ) -> List[LiberacoesComplemento]:
        """Busca liberações de múltiplas escolas."""
        query = self.db.query(self.model).filter(
            LiberacoesComplemento.escola_id.in_(escola_ids)
        )
        if complemento_upload_id:
            query = query.filter(LiberacoesComplemento.complemento_upload_id == complemento_upload_id)
        return query.options(joinedload(LiberacoesComplemento.escola)).all()
    
    def create_map_by_escola_id(
        self,
        escola_ids: List[int],
        complemento_upload_id: Optional[int] = None
    ) -> dict:
        """Cria um mapa de liberações por escola_id."""
        liberacoes = self.find_by_escolas_ids(escola_ids, complemento_upload_id)
        return {liberacao.escola_id: liberacao for liberacao in liberacoes}


class ParcelasComplementoRepository(BaseRepository[ParcelasComplemento]):
    """
    Repositório para operações CRUD com ParcelasComplemento.
    """
    
    def __init__(self, db: Session):
        super().__init__(db, ParcelasComplemento)
    
    def find_by_complemento_escola_id(self, complemento_escola_id: int) -> List[ParcelasComplemento]:
        """Busca todas as parcelas de um complemento_escola específico."""
        return self.db.query(ParcelasComplemento).filter(
            ParcelasComplemento.complemento_escola_id == complemento_escola_id
        ).all()
    
    def find_by_complemento_escola_ids(self, complemento_escola_ids: List[int]) -> List[ParcelasComplemento]:
        """Busca todas as parcelas de múltiplos complemento_escola."""
        return self.db.query(ParcelasComplemento).filter(
            ParcelasComplemento.complemento_escola_id.in_(complemento_escola_ids)
        ).all()
    
    def delete_by_complemento_escola_ids(self, complemento_escola_ids: List[int]) -> int:
        """Deleta todas as parcelas de múltiplos complemento_escola."""
        deleted = self.db.query(ParcelasComplemento).filter(
            ParcelasComplemento.complemento_escola_id.in_(complemento_escola_ids)
        ).delete(synchronize_session=False)
        self.db.flush()
        return deleted
