from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from src.modules.models import TipoCota, TipoEnsino


class ParcelaInfo(BaseModel):
    """Informações de uma parcela específica"""
    tipo_cota: str
    numero_parcela: int
    tipo_ensino: str
    valor_reais: float
    valor_centavos: int
    porcentagem_alunos: float


class ParcelaPorCota(BaseModel):
    """Parcelas de uma cota específica"""
    tipo_cota: str
    valor_total_reais: float
    parcela_1: Dict[str, float]  # {"fundamental": valor, "medio": valor}
    parcela_2: Dict[str, float]
    porcentagens: Dict[str, float]  # {"fundamental": %, "medio": %}


class EscolaParcelas(BaseModel):
    """Parcelas de uma escola"""
    escola_id: int
    nome_uex: str
    dre: Optional[str] = None
    porcentagem_fundamental: float
    porcentagem_medio: float
    parcelas_por_cota: List[ParcelaPorCota]


class SepararParcelasRequest(BaseModel):
    """Request para separar valores em parcelas"""
    ano_letivo_id: Optional[int] = None
    recalcular: bool = False  # Se True, recalcula mesmo que já existam parcelas
    calculation_version: Optional[str] = None  # Versão do cálculo para auditoria


class SepararParcelasResponse(BaseModel):
    """Response da separação de parcelas"""
    success: bool
    message: str
    total_escolas: int
    escolas_processadas: int
    total_parcelas_criadas: int
    ano_letivo_id: int
    escolas: List[EscolaParcelas]
    calculation_version: Optional[str] = None


class ParcelaDetalhe(BaseModel):
    """Detalhe de uma parcela individual"""
    id: int
    tipo_cota: str
    numero_parcela: int
    tipo_ensino: str
    valor_reais: float
    valor_centavos: int
    porcentagem_alunos: float
    created_at: datetime

    class Config:
        from_attributes = True


class ParcelasEscolaResponse(BaseModel):
    """Response com parcelas de uma escola específica"""
    success: bool
    escola_id: int
    nome_uex: str
    dre: Optional[str] = None
    porcentagem_fundamental: float
    porcentagem_medio: float
    parcelas: List[ParcelaDetalhe]
