from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class LiberacaoProjetoInfo(BaseModel):
    id: int
    escola_id: int
    nome_uex: str
    dre: Optional[str]
    liberada: bool
    numero_folha: Optional[int]
    data_liberacao: Optional[datetime]
    valor_projetos_aprovados: float
    created_at: datetime
    updated_at: datetime


class LiberarProjetosRequest(BaseModel):
    escola_ids: List[int]
    numero_folha: int


class LiberarProjetosResponse(BaseModel):
    success: bool
    message: str
    total_escolas_atualizadas: int
    numero_folha: int
    liberacoes: List[LiberacaoProjetoInfo]


class ListarLiberacoesProjetosResponse(BaseModel):
    success: bool
    total: int
    liberacoes: List[LiberacaoProjetoInfo]


class AtualizarLiberacaoProjetoRequest(BaseModel):
    liberada: Optional[bool] = None
    numero_folha: Optional[int] = None
    data_liberacao: Optional[datetime] = None


class LiberacaoProjetoResponse(BaseModel):
    success: bool
    message: str
    liberacao: LiberacaoProjetoInfo
