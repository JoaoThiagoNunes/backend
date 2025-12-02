from fastapi import HTTPException, status
from typing import Optional


class BaseAPIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


class NotFoundException(BaseAPIException):
    def __init__(self, detail: str = "Recurso não encontrado", error_code: str = "NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code
        )


class BadRequestException(BaseAPIException):
    def __init__(self, detail: str = "Requisição inválida", error_code: str = "BAD_REQUEST"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code
        )


class ValidationException(BaseAPIException):
    def __init__(self, detail: str = "Erro de validação", error_code: str = "VALIDATION_ERROR"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code
        )


def handle_exception(e: Exception, default_message: str = "Erro interno do servidor") -> HTTPException:
    if isinstance(e, HTTPException):
        return e
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=default_message
    )

