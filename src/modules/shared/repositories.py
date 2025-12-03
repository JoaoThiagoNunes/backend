from typing import Generic, TypeVar, List, Optional, Type
from sqlalchemy.orm import Session

from src.modules.shared.base import Base

# Tipo genérico para modelos
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model
    
    def find_by_id(self, id: int) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[ModelType]:
        query = self.db.query(self.model)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance
    
    def update(self, instance: ModelType, **kwargs) -> ModelType:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self.db.flush()
        self.db.refresh(instance)
        return instance
    
    def delete(self, instance: ModelType) -> None:
        self.db.delete(instance)
        self.db.flush()
    
    def count(self) -> int:
        return self.db.query(self.model).count()
    
    def exists(self, id: int) -> bool:
        return self.db.query(self.model).filter(self.model.id == id).first() is not None

