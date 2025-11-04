from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class RootResponse(BaseModel):
    """Resposta do endpoint raiz"""
    message: str
    versao: str


class LimparDadosResponse(BaseModel):
    """Resposta de limpeza de dados"""
    success: bool = True
    message: str


class AnoStatusInfo(BaseModel):
    """Informações resumidas de um ano letivo"""
    id: int
    ano: int
    status: str
    uploads: int
    escolas: int
    created_at: Optional[datetime] = None
    arquivado_em: Optional[datetime] = None


class AnoAtivoInfo(BaseModel):
    """Informações do ano letivo ativo"""
    id: int
    ano: int
    status: str


class ResumoDados(BaseModel):
    """Resumo de dados do banco"""
    total_anos_letivos: int
    total_uploads: int
    total_escolas: int
    total_calculos: int


class StatusDadosResponse(BaseModel):
    """Resposta de status dos dados"""
    success: bool = True
    resumo: ResumoDados
    ano_ativo: Optional[AnoAtivoInfo] = None
    anos: List[AnoStatusInfo]


class HealthCheckResponse(BaseModel):
    """Resposta de health check"""
    status: str
    versao: str
    features: List[str]

