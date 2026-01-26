from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from src.modules.shared.base import Base


class ContextoAtivo(Base):
    __tablename__ = "contexto_ativo"
    __table_args__ = (
        UniqueConstraint('ano_letivo_id', name='uq_contexto_ano_letivo'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    ano_letivo_id = Column(Integer, ForeignKey("anos_letivos.id", ondelete="CASCADE"), 
                          nullable=False, unique=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), 
                      nullable=False, index=True)
    ativado_em = Column(DateTime, default=datetime.now, nullable=False)
    
    ano_letivo = relationship("AnoLetivo", back_populates="contexto_ativo")
    upload = relationship("Upload", back_populates="contexto_ativo")
    
    def __repr__(self):
        return f"<ContextoAtivo(id={self.id}, ano_letivo_id={self.ano_letivo_id}, upload_id={self.upload_id})>"


class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    
    ano_letivo_id = Column(Integer, ForeignKey("anos_letivos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.now, nullable=False)
    total_escolas = Column(Integer, default=0)
    
    ano_letivo = relationship("AnoLetivo", back_populates="uploads")
    escolas = relationship("Escola", back_populates="upload", cascade="all, delete-orphan")
    contexto_ativo = relationship("ContextoAtivo", back_populates="upload", uselist=False)
    
    def __repr__(self):
        return f"<Upload(id={self.id}, ano={self.ano_letivo_id}, filename='{self.filename}', escolas={self.total_escolas})>"

