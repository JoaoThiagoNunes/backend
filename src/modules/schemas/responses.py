from pydantic import BaseModel
from typing import Optional, Any

class SuccessResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    detail: str
    error_code: Optional[str] = None



