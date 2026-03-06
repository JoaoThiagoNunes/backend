from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class UploadComplementoRequest(BaseModel):
    ano_letivo_id: Optional[int] = None
    upload_base_id: Optional[int] = None


class ComplementoEscolaInfo(BaseModel):
    escola_id: int
    nome_uex: str
    dre: Optional[str]
    status: str  # 'AUMENTO', 'SEM_MUDANCA', 'DIMINUICAO'
    
    # Quantidades antes/depois
    total_alunos_antes: int
    total_alunos_depois: int
    total_alunos_diferenca: int
    
    # Valores calculados (se houver aumento)
    valor_complemento_total: Optional[float] = None
    
    # Valores individuais das cotas
    valor_complemento_gestao: Optional[float] = None
    valor_complemento_kit_escolar: Optional[float] = None
    valor_complemento_uniforme: Optional[float] = None
    valor_complemento_merenda: Optional[float] = None
    valor_complemento_sala_recurso: Optional[float] = None
    
    # Detalhes por modalidade (opcional)
    detalhes_modalidades: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class UploadComplementoResponse(BaseModel):
    success: bool
    complemento_upload_id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    upload_date: datetime
    
    # Estatísticas
    total_escolas_processadas: int
    escolas_com_aumento: int
    escolas_sem_mudanca: int
    escolas_com_diminuicao: int
    escolas_com_erro: int
    
    # Valor total de complemento calculado
    valor_complemento_total: float
    
    # Lista de escolas (opcional)
    escolas: Optional[List[ComplementoEscolaInfo]] = None
    erros: Optional[List[Dict[str, Any]]] = None


class ComplementoUploadDetailResponse(BaseModel):
    complemento_upload_id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    upload_date: datetime
    upload_base_id: int
    upload_complemento_id: int
    
    # Estatísticas
    total_escolas_processadas: int
    escolas_com_aumento: int
    escolas_sem_mudanca: int
    escolas_com_diminuicao: int
    escolas_com_erro: int
    
    # Valor total
    valor_complemento_total: float
    
    # Lista de escolas
    escolas: List[ComplementoEscolaInfo]
    
    class Config:
        from_attributes = True


class ComplementoEscolaHistoricoResponse(BaseModel):
    escola_id: int
    nome_uex: str
    dre: Optional[str]
    complementos: List[Dict[str, Any]]


class LiberarComplementoRequest(BaseModel):
    escola_ids: List[int]
    numero_folha: int
    complemento_upload_id: Optional[int] = None
    ano_letivo_id: Optional[int] = None


class LiberacaoComplementoInfo(BaseModel):
    id: int
    escola_id: int
    nome_uex: str
    dre: Optional[str]
    complemento_upload_id: Optional[int]
    liberada: bool
    numero_folha: Optional[int]
    data_liberacao: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LiberarComplementoResponse(BaseModel):
    success: bool
    message: str
    total_escolas_atualizadas: int
    numero_folha: int
    liberacoes: List[LiberacaoComplementoInfo]


class ListarLiberacoesComplementoRequest(BaseModel):
    complemento_upload_id: Optional[int] = None
    numero_folha: Optional[int] = None
    liberada: Optional[bool] = None
    escola_id: Optional[int] = None


class ListarLiberacoesComplementoResponse(BaseModel):
    success: bool
    total: int
    liberacoes: List[LiberacaoComplementoInfo]


class AtualizarLiberacaoComplementoRequest(BaseModel):
    liberada: Optional[bool] = None
    numero_folha: Optional[int] = None
    data_liberacao: Optional[datetime] = None


class LiberacaoComplementoResponse(BaseModel):
    success: bool
    message: str
    liberacao: LiberacaoComplementoInfo


class ComplementoEscolaPrevisaoInfo(BaseModel):
    escola_id: int
    nome_uex: str
    dre: Optional[str]
    liberada: bool
    numero_folha: Optional[int] = None
    valor_complemento_total: float
    status: str  # 'AUMENTO', 'SEM_MUDANCA', 'DIMINUICAO'


class ComplementoFolhaInfo(BaseModel):
    numero_folha: Optional[int]
    total_escolas: int
    valor_total_reais: float
    escolas: List[ComplementoEscolaPrevisaoInfo]


class ComplementoResumoResponse(BaseModel):
    success: bool
    total_folhas: int
    total_escolas: int
    valor_total_reais: float
    folhas: List[ComplementoFolhaInfo]
