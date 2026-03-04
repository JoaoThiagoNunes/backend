from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from src.modules.shared.base import Base


class LiberacoesProjeto(Base):
    __tablename__ = "liberacoes_projeto"
    __table_args__ = (
        UniqueConstraint(
            'escola_id',
            name='uq_liberacao_projeto_escola'
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    escola_id = Column(Integer, ForeignKey("escolas.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    liberada = Column(Boolean, default=False, nullable=False, index=True)
    numero_folha = Column(Integer, nullable=True, index=True)
    data_liberacao = Column(DateTime, nullable=True)
    
    # Valor calculado baseado nos projetos aprovados cadastrados no Excel
    # Cada projeto aprovado = R$ 5.000,00 (limitado ao valor de direito)
    valor_projetos_aprovados = Column(Float, default=0.0, nullable=False)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    escola = relationship("Escola", back_populates="liberacoes_projetos")

