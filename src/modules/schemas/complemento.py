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
