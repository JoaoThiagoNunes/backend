from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from src.modules.shared.base import Base


class Escola(Base):
    __tablename__ = "escolas"
    __table_args__ = (
        UniqueConstraint('upload_id', 'nome_uex', 'dre', name='uq_escola_upload_nome_dre'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Chave estrangeira para Upload
    upload_id = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    
    # Dados básicos da escola
    nome_uex = Column(String(255), nullable=False, index=True)
    dre = Column(String(100), nullable=True)
    cnpj = Column(String(20), nullable=True, index=True)
    
    # Quantidades de alunos por modalidade
    total_alunos = Column(Integer, default=0)
    fundamental_inicial = Column(Integer, default=0)
    fundamental_final = Column(Integer, default=0)
    fundamental_integral = Column(Integer, default=0)
    profissionalizante = Column(Integer, default=0)
    alternancia = Column(Integer, default=0)
    ensino_medio_integral = Column(Integer, default=0)
    ensino_medio_regular = Column(Integer, default=0)
    especial_fund_regular = Column(Integer, default=0)
    especial_fund_integral = Column(Integer, default=0)
    especial_medio_parcial = Column(Integer, default=0)
    especial_medio_integral = Column(Integer, default=0)
    
    # Recursos especiais
    sala_recurso = Column(Integer, default=0)
    climatizacao = Column(Integer, default=0)
    preuni = Column(Integer, default=0)
    indigena_quilombola = Column(String(10), default="NÃO")
    quantidade_projetos_aprovados = Column(Integer, default=0)
    repasse_por_area = Column(Integer, default=0)
    
    # Estado de liberação e numeração da folha
    estado_liberacao = Column(Boolean, default=False, nullable=False, index=True)
    numeracao_folha = Column(String(50), nullable=True, index=True)
    
    # Data de criação
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relacionamentos
    upload = relationship("Upload", back_populates="escolas")
    calculos = relationship("CalculosProfin", back_populates="escola", 
                          cascade="all, delete-orphan", uselist=False)
    liberacoes_parcelas = relationship(
        "LiberacoesParcela",
        back_populates="escola",
        cascade="all, delete-orphan"
    )
    liberacoes_projetos = relationship(
        "LiberacoesProjeto",
        back_populates="escola",
        cascade="all, delete-orphan",
        uselist=False
    )
    
    def __repr__(self):
        return f"<Escola(id={self.id}, nome='{self.nome_uex}', alunos={self.total_alunos})>"

