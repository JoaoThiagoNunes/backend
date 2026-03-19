from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum as SQLEnum, Boolean, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from src.modules.shared.base import Base
from src.modules.features.calculos import TipoCota, TipoEnsino
import enum


class StatusComplemento(str, enum.Enum):
    AUMENTO = "AUMENTO"
    SEM_MUDANCA = "SEM_MUDANCA"
    DIMINUICAO = "DIMINUICAO"
    ERRO = "ERRO"


class ComplementoUpload(Base):
    __tablename__ = "complemento_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    ano_letivo_id = Column(Integer, ForeignKey("anos_letivos.id", ondelete="CASCADE"), nullable=False, index=True)
    upload_base_id = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    upload_complemento_id = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.now, nullable=False)
    
    # Estatísticas do processamento
    total_escolas_processadas = Column(Integer, default=0)
    escolas_com_aumento = Column(Integer, default=0)
    escolas_sem_mudanca = Column(Integer, default=0)
    escolas_com_diminuicao = Column(Integer, default=0)
    escolas_com_erro = Column(Integer, default=0)
    
    # Relacionamentos
    ano_letivo = relationship("AnoLetivo", back_populates="complemento_uploads")
    upload_base = relationship("Upload", foreign_keys=[upload_base_id])
    upload_complemento = relationship("Upload", foreign_keys=[upload_complemento_id])
    complementos_escola = relationship(
        "ComplementoEscola",
        back_populates="complemento_upload",
        cascade="all, delete-orphan",
    )
    # Não usar delete-orphan/cascade destrutivo em liberações para preservar histórico
    liberacoes_complemento = relationship(
        "LiberacoesComplemento",
        back_populates="complemento_upload",
    )
    
    def __repr__(self):
        return f"<ComplementoUpload(id={self.id}, ano={self.ano_letivo_id}, filename='{self.filename}')>"


class ComplementoEscola(Base):
    __tablename__ = "complemento_escolas"
    
    id = Column(Integer, primary_key=True, index=True)
    complemento_upload_id = Column(Integer, ForeignKey("complemento_uploads.id", ondelete="CASCADE"), 
                                   nullable=False, index=True)
    escola_id = Column(Integer, ForeignKey("escolas.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Quantidades ANTES (snapshot do upload base)
    total_alunos_antes = Column(Integer, default=0)
    fundamental_inicial_antes = Column(Integer, default=0)
    fundamental_final_antes = Column(Integer, default=0)
    fundamental_integral_antes = Column(Integer, default=0)
    profissionalizante_antes = Column(Integer, default=0)
    profissionalizante_integrado_antes = Column(Integer, default=0)
    alternancia_antes = Column(Integer, default=0)
    ensino_medio_integral_antes = Column(Integer, default=0)
    ensino_medio_regular_antes = Column(Integer, default=0)
    especial_fund_regular_antes = Column(Integer, default=0)
    especial_fund_integral_antes = Column(Integer, default=0)
    especial_medio_parcial_antes = Column(Integer, default=0)
    especial_medio_integral_antes = Column(Integer, default=0)
    sala_recurso_antes = Column(Integer, default=0)
    preuni_antes = Column(Integer, default=0)
    
    # Quantidades DEPOIS (do upload complemento)
    total_alunos_depois = Column(Integer, default=0)
    fundamental_inicial_depois = Column(Integer, default=0)
    fundamental_final_depois = Column(Integer, default=0)
    fundamental_integral_depois = Column(Integer, default=0)
    profissionalizante_depois = Column(Integer, default=0)
    profissionalizante_integrado_depois = Column(Integer, default=0)
    alternancia_depois = Column(Integer, default=0)
    ensino_medio_integral_depois = Column(Integer, default=0)
    ensino_medio_regular_depois = Column(Integer, default=0)
    especial_fund_regular_depois = Column(Integer, default=0)
    especial_fund_integral_depois = Column(Integer, default=0)
    especial_medio_parcial_depois = Column(Integer, default=0)
    especial_medio_integral_depois = Column(Integer, default=0)
    sala_recurso_depois = Column(Integer, default=0)
    preuni_depois = Column(Integer, default=0)
    
    # Diferenças calculadas (apenas valores positivos para cálculo)
    total_alunos_diferenca = Column(Integer, default=0)
    fundamental_inicial_diferenca = Column(Integer, default=0)
    fundamental_final_diferenca = Column(Integer, default=0)
    fundamental_integral_diferenca = Column(Integer, default=0)
    profissionalizante_diferenca = Column(Integer, default=0)
    profissionalizante_integrado_diferenca = Column(Integer, default=0)
    alternancia_diferenca = Column(Integer, default=0)
    ensino_medio_integral_diferenca = Column(Integer, default=0)
    ensino_medio_regular_diferenca = Column(Integer, default=0)
    especial_fund_regular_diferenca = Column(Integer, default=0)
    especial_fund_integral_diferenca = Column(Integer, default=0)
    especial_medio_parcial_diferenca = Column(Integer, default=0)
    especial_medio_integral_diferenca = Column(Integer, default=0)
    sala_recurso_diferenca = Column(Integer, default=0)
    preuni_diferenca = Column(Integer, default=0)
    
    # Status do processamento
    status = Column(SQLEnum(StatusComplemento), nullable=False, default=StatusComplemento.SEM_MUDANCA)
    
    # Valores calculados do complemento (apenas se houve aumento)
    valor_complemento_gestao = Column(Float, default=0.0)
    valor_complemento_projeto = Column(Float, default=0.0)
    valor_complemento_kit_escolar = Column(Float, default=0.0)
    valor_complemento_uniforme = Column(Float, default=0.0)
    valor_complemento_merenda = Column(Float, default=0.0)
    valor_complemento_sala_recurso = Column(Float, default=0.0)
    valor_complemento_preuni = Column(Float, default=0.0)
    valor_complemento_total = Column(Float, default=0.0, index=True)
    
    # Data de processamento
    processed_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relacionamentos
    complemento_upload = relationship("ComplementoUpload", back_populates="complementos_escola")
    escola = relationship("Escola", back_populates="complementos")
    
    def __repr__(self):
        return f"<ComplementoEscola(escola_id={self.escola_id}, status={self.status.value}, valor={self.valor_complemento_total})>"
    
    # Relacionamento com parcelas
    parcelas = relationship(
        "ParcelasComplemento",
        back_populates="complemento_escola",
        cascade="all, delete-orphan"
    )


class ParcelasComplemento(Base):
    __tablename__ = "parcelas_complemento"
    __table_args__ = (
        UniqueConstraint(
            'complemento_escola_id',
            'tipo_cota',
            'numero_parcela',
            'tipo_ensino',
            name='uq_parcela_complemento_escola_cota_parcela_ensino'
        ),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Chave estrangeira para ComplementoEscola
    complemento_escola_id = Column(Integer, ForeignKey("complemento_escolas.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Tipo de cota (gestao, merenda, kit_escolar, uniforme, sala_recurso)
    tipo_cota = Column(Enum(TipoCota), nullable=False, index=True)
    
    # Número da parcela (1 ou 2, se aplicável)
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
    complemento_escola = relationship("ComplementoEscola", back_populates="parcelas")
    
    def __repr__(self):
        return f"<ParcelasComplemento(complemento_escola_id={self.complemento_escola_id}, cota={self.tipo_cota.value}, parcela={self.numero_parcela}, ensino={self.tipo_ensino.value}, valor={self.valor_centavos/100:.2f})>"
    
    @property
    def valor_reais(self) -> float:
        return self.valor_centavos / 100.0


class LiberacoesComplemento(Base):
    __tablename__ = "liberacoes_complemento"
    __table_args__ = (
        UniqueConstraint(
            'escola_id',
            'complemento_upload_id',
            name='uq_liberacao_complemento_escola_upload'
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    escola_id = Column(Integer, ForeignKey("escolas.id", ondelete="RESTRICT"), nullable=False, index=True)
    complemento_upload_id = Column(Integer, ForeignKey("complemento_uploads.id", ondelete="CASCADE"), nullable=True, index=True)
    liberada = Column(Boolean, default=False, nullable=False, index=True)
    numero_folha = Column(Integer, nullable=True, index=True)
    data_liberacao = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    escola = relationship("Escola", back_populates="liberacoes_complementos")
    complemento_upload = relationship("ComplementoUpload", back_populates="liberacoes_complemento")

    def __repr__(self):
        return f"<LiberacoesComplemento(escola_id={self.escola_id}, folha={self.numero_folha}, liberada={self.liberada})>"