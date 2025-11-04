from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.database import Base
import enum


class StatusAnoLetivo(str, enum.Enum):
    ATIVO = "ATIVO"
    ARQUIVADO = "ARQUIVADO"


class AnoLetivo(Base):
    """
    Tabela que armazena os anos letivos.
    Apenas um ano pode estar ATIVO por vez.
    Anos ARQUIVADOS são mantidos por 5 anos para consulta.
    """
    __tablename__ = "anos_letivos"
    
    id = Column(Integer, primary_key=True, index=True)
    ano = Column(Integer, unique=True, nullable=False, index=True)
    status = Column(Enum(StatusAnoLetivo), default=StatusAnoLetivo.ATIVO, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    arquivado_em = Column(DateTime, nullable=True)
    
    # Relacionamento: Um ano letivo tem vários uploads
    uploads = relationship("Upload", back_populates="ano_letivo", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnoLetivo(id={self.id}, ano={self.ano}, status='{self.status.value}')>"


class Upload(Base):
    """
    Tabela que armazena informações sobre cada upload de arquivo Excel.
    Cada upload está vinculado a um ano letivo e pode ter várias escolas associadas.
    """
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Chave estrangeira para AnoLetivo
    ano_letivo_id = Column(Integer, ForeignKey("anos_letivos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.now, nullable=False)
    total_escolas = Column(Integer, default=0)
    
    # Flag para indicar se é o upload ativo (último upload do ano)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Relacionamentos
    ano_letivo = relationship("AnoLetivo", back_populates="uploads")
    escolas = relationship("Escola", back_populates="upload", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Upload(id={self.id}, ano={self.ano_letivo_id}, filename='{self.filename}', escolas={self.total_escolas})>"


class Escola(Base):
    """
    Tabela que armazena os dados de cada escola/UEX.
    Cada escola está associada a um upload e pode ter um cálculo.
    """
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
    escola_id = Column(Integer, ForeignKey("escolas.id", ondelete="CASCADE"), nullable=False, unique=True)
    
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
    parcelas = relationship("ParcelasProfin", back_populates="calculo", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CalculosProfin(escola_id={self.escola_id}, total=R$ {self.valor_total:,.2f})>"


class TipoCota(str, enum.Enum):
    """Tipos de cotas PROFIN"""
    CUSTEIO = "custeio"
    PROJETO = "projeto"
    KIT_ESCOLAR = "kit_escolar"
    UNIFORME = "uniforme"
    MERENDA = "merenda"
    SALA_RECURSO = "sala_recurso"
    PERMANENTE = "permanente"
    CLIMATIZACAO = "climatizacao"
    PREUNI = "preuni"


class TipoEnsino(str, enum.Enum):
    """Tipos de ensino"""
    FUNDAMENTAL = "fundamental"
    MEDIO = "medio"


class ParcelasProfin(Base):
    """
    Tabela que armazena as parcelas divididas por cota, número da parcela e tipo de ensino.
    Cada cota é dividida em 2 parcelas, e cada parcela é dividida por tipo de ensino (fundamental/médio).
    Valores armazenados em centavos (inteiros) para evitar problemas com floats.
    """
    __tablename__ = "parcelas_profin"
    __table_args__ = (
        UniqueConstraint('calculo_id', 'tipo_cota', 'numero_parcela', 'tipo_ensino', 
                       name='uq_parcela_calculo_cota_parcela_ensino'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Chave estrangeira para CalculosProfin
    calculo_id = Column(Integer, ForeignKey("calculos_profin.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Tipo de cota (custeio, projeto, kit_escolar, etc.)
    tipo_cota = Column(Enum(TipoCota), nullable=False, index=True)
    
    # Número da parcela (1 ou 2)
    numero_parcela = Column(Integer, nullable=False, index=True)
    
    # Tipo de ensino (fundamental ou medio)
    tipo_ensino = Column(Enum(TipoEnsino), nullable=False, index=True)
    
    # Valor em centavos (inteiro para evitar problemas com floats)
    valor_centavos = Column(Integer, nullable=False, default=0)
    
    # Porcentagem de alunos do tipo de ensino (0-100)
    porcentagem_alunos = Column(Float, nullable=False, default=0.0)
    
    # Data de criação
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Versão do cálculo (para auditoria)
    calculation_version = Column(String(50), nullable=True)
    
    # Relacionamento
    calculo = relationship("CalculosProfin", back_populates="parcelas")
    
    def __repr__(self):
        return f"<ParcelasProfin(calculo_id={self.calculo_id}, cota={self.tipo_cota.value}, parcela={self.numero_parcela}, ensino={self.tipo_ensino.value}, valor={self.valor_centavos/100:.2f})>"
    
    @property
    def valor_reais(self) -> float:
        """Retorna o valor em reais (centavos / 100)"""
        return self.valor_centavos / 100.0