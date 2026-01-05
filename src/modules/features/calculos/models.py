from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.modules.shared.base import Base
import enum


class TipoCota(str, enum.Enum):
    GESTAO = "gestao"
    PROJETO = "projeto"
    KIT_ESCOLAR = "kit_escolar"
    UNIFORME = "uniforme"
    MERENDA = "merenda"
    SALA_RECURSO = "sala_recurso"
    PERMANENTE = "permanente"
    # CLIMATIZACAO = "climatizacao" # Desativado temporariamente
    PREUNI = "preuni"


class TipoEnsino(str, enum.Enum):
    FUNDAMENTAL = "fundamental"
    MEDIO = "medio"


class CalculosProfin(Base):
    __tablename__ = "calculos_profin"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Chave estrangeira para Escola (único - uma escola tem apenas um cálculo)
    escola_id = Column(Integer, ForeignKey("escolas.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Valores calculados para cada cota PROFIN
    profin_gestao = Column(Float, default=0.0)
    profin_projeto = Column(Float, default=0.0)
    profin_kit_escolar = Column(Float, default=0.0)
    profin_uniforme = Column(Float, default=0.0)
    profin_merenda = Column(Float, default=0.0)
    profin_sala_recurso = Column(Float, default=0.0)
    profin_permanente = Column(Float, default=0.0)
    # profin_climatizacao = Column(Float, default=0.0) # Desativado temporariamente
    profin_preuni = Column(Float, default=0.0)
    
    # Valor total (soma de todas as cotas)
    valor_total = Column(Float, default=0.0, index=True)
    
    # Data de cálculo
    calculated_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relacionamento
    escola = relationship("Escola", back_populates="calculos")
    parcelas = relationship("ParcelasProfin", back_populates="calculo", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CalculosProfin(escola_id={self.escola_id}, total=R$ {self.valor_total:,.2f})>"

