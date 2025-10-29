from pydantic import BaseModel
from typing import Optional

class AnoLetivoBase(BaseModel):
    ano: int

class AnoLetivoCreate(AnoLetivoBase):
    pass

class AnoLetivoRead(AnoLetivoBase):
    id: int
    status: Optional[str] = None
    arquivado_em: Optional[str] = None  # ISO datetime ou use datetime e orm_mode

    class Config:
        orm_mode = True