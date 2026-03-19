from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EscolaInfo(BaseModel):
    id: int
    nome_uex: str
    dre: Optional[str] = None
    cnpj: Optional[str] = None
    total_alunos: Optional[int] = None
    fundamental_inicial: Optional[int] = None
    fundamental_final: Optional[int] = None
    fundamental_integral: Optional[int] = None
    profissionalizante: Optional[int] = None
    profissionalizante_integrado: Optional[int] = None
    alternancia: Optional[int] = None
    ensino_medio_integral: Optional[int] = None
    ensino_medio_regular: Optional[int] = None
    especial_fund_regular: Optional[int] = None
    especial_fund_integral: Optional[int] = None
    especial_medio_parcial: Optional[int] = None
    especial_medio_integral: Optional[int] = None
    fic_senac: Optional[int] = None
    especial_profissionalizante_parcial: Optional[int] = None
    especial_profissionalizante_integrado: Optional[int] = None
    sala_recurso: Optional[int] = None
    climatizacao: Optional[int] = None
    preuni: Optional[int] = None
    quantidade_projetos_aprovados: Optional[int] = None
    repasse_por_area: Optional[int] = None
    indigena_quilombola: Optional[str] = None
    created_at: Optional[datetime] = None
    codigo_ept: Optional[str] = None
    codigo_inep: Optional[str] = None
    saldo_reprogramado_gestao: Optional[float] = None
    saldo_reprogramado_merenda: Optional[float] = None

class EscolaCreate(BaseModel):
    nome_uex: str
    dre: Optional[str] = None
    codigo_ept: Optional[str] = None
    codigo_inep: Optional[str] = None

class EscolaRead(BaseModel):
    id: int
    nome_uex: str
    dre: Optional[str] = None
    total_alunos: Optional[int] = None
    fic_senac: Optional[int] = None
    especial_profissionalizante_parcial: Optional[int] = None
    especial_profissionalizante_integrado: Optional[int] = None
    codigo_ept: Optional[str] = None
    codigo_inep: Optional[str] = None
    
    class Config:
        from_attributes = True
