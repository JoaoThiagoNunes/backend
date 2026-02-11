from sqlalchemy import Column, Integer, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from src.modules.shared.base import Base
import enum

class StatusAnoLetivo(str, enum.Enum):
    ATIVO = "ATIVO"
    ARQUIVADO = "ARQUIVADO"

class AnoLetivo(Base):
    __tablename__ = "anos_letivos"
    
    id = Column(Integer, primary_key=True, index=True)
    ano = Column(Integer, unique=True, nullable=False, index=True)
    status = Column(Enum(StatusAnoLetivo), default=StatusAnoLetivo.ATIVO, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    arquivado_em = Column(DateTime, nullable=True)
    
    # Relacionamento: Um ano letivo tem vários uploads
    uploads = relationship(
        "Upload", 
        back_populates="ano_letivo", 
        cascade="all, delete-orphan"
        )
    contexto_ativo = relationship(
        "ContextoAtivo", 
        back_populates="ano_letivo", 
        uselist=False
        )
   
    #complemento_uploads = relationship(
    #    "ComplementoUpload",
    #    back_populates="ano_letivo",
    #    cascade="all, delete-orphan"
    #)
    
    def __repr__(self):
        return f"<AnoLetivo(id={self.id}, ano={self.ano}, status='{self.status.value}')>"

