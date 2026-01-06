from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class ParcelaInfo(BaseModel):
    tipo_cota: str
    numero_parcela: int
    tipo_ensino: str
    valor_reais: float
    valor_centavos: int
    porcentagem_alunos: float

class ParcelaPorCota(BaseModel):
    tipo_cota: str
    valor_total_reais: float
    saldo_reprogramado: float
    parcela_1: Dict[str, float]  # {"fundamental": valor, "medio": valor}
    parcela_2: Optional[Dict[str, float]] = None  # Opcional - apenas para cotas com 2 parcelas
    porcentagens: Dict[str, float]  # {"fundamental": %, "medio": %}

class EscolaParcelas(BaseModel):
    escola_id: int
    nome_uex: str
    dre: Optional[str] = None
    porcentagem_fundamental: float
    porcentagem_medio: float
    parcelas_por_cota: List[ParcelaPorCota]
    estado_liberacao: Optional[bool] = False
    numeracao_folha: Optional[str] = None

class SepararParcelasRequest(BaseModel):
    ano_letivo_id: Optional[int] = None
    recalcular: bool = False  # Se True, recalcula mesmo que já existam parcelas
    calculation_version: Optional[str] = None  # Versão do cálculo para auditoria

class SepararParcelasResponse(BaseModel):
    success: bool
    message: str
    total_escolas: int
    escolas_processadas: int
    total_parcelas_criadas: int
    ano_letivo_id: int
    escolas: List[EscolaParcelas]
    calculation_version: Optional[str] = None

class ParcelaDetalhe(BaseModel):
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
    success: bool
    escola_id: int
    nome_uex: str
    dre: Optional[str] = None
    porcentagem_fundamental: float
    porcentagem_medio: float
    parcelas: List[ParcelaDetalhe]
    estado_liberacao: Optional[bool] = False
    numeracao_folha: Optional[str] = None

class AtualizarLiberacaoRequest(BaseModel):
    estado_liberacao: bool

class AtualizarFolhaRequest(BaseModel):
    numeracao_folha: Optional[str] = None

class AtualizarEscolaRequest(BaseModel):
    estado_liberacao: Optional[bool] = None
    numeracao_folha: Optional[str] = None

class EscolaAtualizadaResponse(BaseModel):
    success: bool
    message: str
    escola_id: int
    nome_uex: str
    estado_liberacao: bool
    numeracao_folha: Optional[str] = None

class LiberarParcelasRequest(BaseModel):
    escola_ids: List[int]
    numero_parcela: int
    numero_folha: int

class LiberacaoParcelaInfo(BaseModel):
    id: int
    escola_id: int
    nome_uex: str
    dre: Optional[str]
    numero_parcela: int
    liberada: bool
    numero_folha: Optional[int]
    data_liberacao: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class LiberarParcelasResponse(BaseModel):
    success: bool
    message: str
    total_escolas_atualizadas: int
    numero_parcela: int
    numero_folha: int
    liberacoes: List[LiberacaoParcelaInfo]

class ListarLiberacoesRequest(BaseModel):
    ano_letivo_id: Optional[int] = None
    numero_parcela: Optional[int] = None
    numero_folha: Optional[int] = None
    liberada: Optional[bool] = None
    escola_id: Optional[int] = None

class ListarLiberacoesResponse(BaseModel):
    success: bool
    total: int
    liberacoes: List[LiberacaoParcelaInfo]

class AtualizarLiberacaoParcelaRequest(BaseModel):
    liberada: Optional[bool] = None
    numero_folha: Optional[int] = None
    data_liberacao: Optional[datetime] = None

class LiberacaoParcelaResponse(BaseModel):
    success: bool
    message: str
    liberacao: LiberacaoParcelaInfo

class EscolaPrevisaoInfo(BaseModel):
    escola_id: int
    nome_uex: str
    dre: Optional[str]
    numero_parcela: int
    liberada: bool
    numero_folha: Optional[int] = None
    valor_total_reais: float
    quantidade_projetos_aprovados: Optional[int] = None
    quantidade_projetos_a_pagar: Optional[int] = None

class PrevisaoLiberacaoResponse(BaseModel):
    success: bool
    numero_parcela: int
    total_escolas: int
    escolas: List[EscolaPrevisaoInfo]

class RepasseFolhaInfo(BaseModel):
    numero_parcela: int
    numero_folha: Optional[int]
    total_escolas: int
    valor_total_reais: float
    escolas: List[EscolaPrevisaoInfo]

class RepasseResumoResponse(BaseModel):
    success: bool
    total_parcelas: int
    total_folhas: int
    total_escolas: int
    valor_total_reais: float
    folhas: List[RepasseFolhaInfo]
