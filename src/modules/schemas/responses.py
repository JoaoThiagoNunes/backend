from pydantic import BaseModel
from typing import Optional, Any, Dict, List


class SuccessResponse(BaseModel):
    """Resposta padrão de sucesso"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Resposta padrão de erro"""
    success: bool = False
    detail: str
    error_code: Optional[str] = None

