from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from src.modules.shared.base import Base
from src.modules.features.calculos import TipoCota, TipoEnsino


class ParcelasProfin(Base):
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
        return self.valor_centavos / 100.0


class LiberacoesParcela(Base):
    __tablename__ = "liberacoes_parcela"
    __table_args__ = (
        UniqueConstraint(
            'escola_id',
            'numero_parcela',
            name='uq_liberacao_escola_parcela'
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    escola_id = Column(Integer, ForeignKey("escolas.id", ondelete="CASCADE"), nullable=False, index=True)
    numero_parcela = Column(Integer, nullable=False, index=True)
    liberada = Column(Boolean, default=False, nullable=False, index=True)
    numero_folha = Column(Integer, nullable=True, index=True)
    data_liberacao = Column(DateTime, nullable=True)
    valor_projetos_aprovados = Column(Float, default=0.0, nullable=False)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    escola = relationship("Escola", back_populates="liberacoes_parcelas")

