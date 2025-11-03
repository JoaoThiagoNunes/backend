"""
Schemas Pydantic para rotas de upload.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .escola import EscolaInfo


class CalculoInfo(BaseModel):
    """Informações de cálculo de uma escola"""
    id: Optional[int] = None
    profin_custeio: Optional[float] = None
    profin_projeto: Optional[float] = None
    profin_kit_escolar: Optional[float] = None
    profin_uniforme: Optional[float] = None
    profin_merenda: Optional[float] = None
    profin_sala_recurso: Optional[float] = None
    profin_permanente: Optional[float] = None
    profin_climatizacao: Optional[float] = None
    profin_preuni: Optional[float] = None
    valor_total: Optional[float] = None
    calculated_at: Optional[datetime] = None


class UploadListItem(BaseModel):
    """Item de upload na listagem"""
    id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    upload_date: datetime
    total_escolas: int
    is_active: bool


class UploadListResponse(BaseModel):
    """Resposta de listagem de uploads"""
    success: bool = True
    uploads: List[UploadListItem]


class EscolaComCalculo(BaseModel):
    """Escola com seus cálculos"""
    escola: EscolaInfo
    calculos: Optional[CalculoInfo] = None


class UploadDetailInfo(BaseModel):
    """Informações detalhadas de um upload"""
    id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    upload_date: datetime
    total_escolas: int


class UploadDetailResponse(BaseModel):
    """Resposta de detalhes de upload"""
    success: bool = True
    upload: UploadDetailInfo
    escolas: List[EscolaComCalculo]


class ErroUpload(BaseModel):
    """Informação de erro no upload"""
    linha: int
    nome: str
    erro: str


class UploadExcelResponse(BaseModel):
    """Resposta de upload de Excel"""
    success: bool = True
    upload_id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    total_linhas: int
    escolas_salvas: int
    escolas_confirmadas_banco: int
    escolas_com_erro: int
    colunas: List[str]
    erros: Optional[List[ErroUpload]] = None
    aviso: Optional[str] = None
