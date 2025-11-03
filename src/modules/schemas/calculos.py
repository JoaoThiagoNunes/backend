from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class CalculoItem(BaseModel):
    profin_custeio: float
    profin_projeto: float
    profin_kit_escolar: float
    profin_uniforme: float
    profin_merenda: float
    profin_sala_recurso: float
    profin_permanente: float
    profin_climatizacao: float
    profin_preuni: float
    valor_total: float

class EscolaCalculo(BaseModel):
    id: int
    dre: Optional[str] = None
    nome_uex: str
    profin_custeio: float
    profin_projeto: float
    profin_kit_escolar: float
    profin_uniforme: float
    profin_merenda: float
    profin_sala_recurso: float
    profin_permanente: float
    profin_climatizacao: float
    profin_preuni: float
    valor_total: float

class ResponseCalculos(BaseModel):
    success: bool
    message: str
    total_escolas: int
    valor_total_geral: float
    escolas: List[EscolaCalculo]
    upload_id: int
    ano_letivo_id: Optional[int] = None 

    class Config:
        from_attributes = True  # Compatível com SQLAlchemy (antigo orm_mode)
