from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AnoLetivoBase(BaseModel):
    """Schema base para ano letivo"""
    ano: int


class AnoLetivoCreate(AnoLetivoBase):
    """Schema para criação de ano letivo"""
    pass


class AnoLetivoRead(AnoLetivoBase):
    """Schema para leitura de ano letivo"""
    id: int
    status: Optional[str] = None
    arquivado_em: Optional[datetime] = None
    created_at: Optional[datetime] = None
    total_uploads: Optional[int] = None

    class Config:
        from_attributes = True  # Compatível com SQLAlchemy (antigo orm_mode)


class AnoLetivoListResponse(BaseModel):
    """Schema para resposta de listagem de anos letivos"""
    success: bool = True
    anos: list[AnoLetivoRead]


class AnoLetivoDetailResponse(BaseModel):
    """Schema para resposta de detalhes de ano letivo"""
    success: bool = True
    ano: AnoLetivoRead


class AnoLetivoCreateResponse(BaseModel):
    """Schema para resposta de criação de ano letivo"""
    success: bool = True
    message: str
    ano: AnoLetivoRead


class AnoLetivoArquivarResponse(BaseModel):
    """Schema para resposta de arquivamento de ano letivo"""
    success: bool = True
    message: str
    ano: AnoLetivoRead


class AnoLetivoDeleteResponse(BaseModel):
    """Schema para resposta de exclusão de ano letivo"""
    success: bool = True
    message: str
