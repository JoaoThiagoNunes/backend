from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from src.modules.shared.base import Base


class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    
    ano_letivo_id = Column(Integer, ForeignKey("anos_letivos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.now, nullable=False)
    total_escolas = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    ano_letivo = relationship("AnoLetivo", back_populates="uploads")
    escolas = relationship("Escola", back_populates="upload", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Upload(id={self.id}, ano={self.ano_letivo_id}, filename='{self.filename}', escolas={self.total_escolas})>"

