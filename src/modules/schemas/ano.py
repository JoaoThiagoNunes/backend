from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnoLetivoCreate(BaseModel):
    ano: int

class AnoLetivoRead(BaseModel):
    id: int
    ano: int
    status: Optional[str] = None
    arquivado_em: Optional[datetime] = None
    created_at: Optional[datetime] = None
    total_uploads: Optional[int] = None

    class Config:
        from_attributes = True 

class AnoLetivoListResponse(BaseModel):
    success: bool = True
    anos: list[AnoLetivoRead]


class AnoLetivoCreateResponse(BaseModel):
    success: bool = True
    message: str
    ano: AnoLetivoRead


class AnoLetivoArquivarResponse(BaseModel):
    success: bool = True
    message: str
    ano: AnoLetivoRead


class AnoLetivoDeleteResponse(BaseModel):
    success: bool = True
    message: str
