from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Upload(Base):
    """
    Tabela que armazena informações sobre cada upload de arquivo Excel.
    Cada upload pode ter várias escolas associadas.
    """
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.now, nullable=False)
    total_escolas = Column(Integer, default=0)
    
    # Flag para indicar se é o upload ativo
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Relacionamento: Um upload tem várias escolas
    # cascade garante que ao deletar o objeto Upload via ORM os filhos sejam removidos
    escolas = relationship("Escola", back_populates="upload", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Upload(id={self.id}, filename='{self.filename}', escolas={self.total_escolas}, active={self.is_active})>"


class Escola(Base):
    """
    Tabela que armazena os dados de cada escola/UEX.
    Cada escola está associada a um upload e pode ter um cálculo.
    """
    __tablename__ = "escolas"
    __table_args__ = (
        UniqueConstraint('nome_uex', 'dre', name='uq_escola_nome_dre'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Chave estrangeira para Upload
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    
    # Dados básicos da escola
    nome_uex = Column(String(255), nullable=False, index=True)
    dre = Column(String(100), nullable=True)
    
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
    
    # Identificadores especiais
    indigena_quilombola = Column(String(10), default="NÃO")
    
    # Data de criação
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relacionamentos
    upload = relationship("Upload", back_populates="escolas")
    calculos = relationship("CalculosProfin", back_populates="escola", 
                          cascade="all, delete-orphan", uselist=False)
    
    def __repr__(self):
        return f"<Escola(id={self.id}, nome='{self.nome_uex}', alunos={self.total_alunos})>"


class CalculosProfin(Base):
    """
    Tabela que armazena os cálculos de todas as cotas PROFIN para cada escola.
    Cada escola tem apenas um registro de cálculo.
    """
    __tablename__ = "calculos_profin"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Chave estrangeira para Escola (único - uma escola tem apenas um cálculo)
    escola_id = Column(Integer, ForeignKey("escolas.id"), nullable=False, unique=True)
    
    # Valores calculados para cada cota PROFIN
    profin_custeio = Column(Float, default=0.0)
    profin_projeto = Column(Float, default=0.0)
    profin_kit_escolar = Column(Float, default=0.0)
    profin_uniforme = Column(Float, default=0.0)
    profin_merenda = Column(Float, default=0.0)
    profin_sala_recurso = Column(Float, default=0.0)
    profin_permanente = Column(Float, default=0.0)
    profin_climatizacao = Column(Float, default=0.0)
    profin_preuni = Column(Float, default=0.0)
    
    # Valor total (soma de todas as cotas)
    valor_total = Column(Float, default=0.0, index=True)
    
    # Data de cálculo
    calculated_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relacionamento
    escola = relationship("Escola", back_populates="calculos")
    
    def __repr__(self):
        return f"<CalculosProfin(escola_id={self.escola_id}, total=R$ {self.valor_total:,.2f})>"


class ConfiguracaoSistema(Base):
    """
    Tabela para configurações globais do sistema
    """
    __tablename__ = "configuracao_sistema"
    
    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String(100), unique=True, nullable=False)
    valor = Column(String(500), nullable=True)
    descricao = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Config(chave='{self.chave}', valor='{self.valor}')>"
