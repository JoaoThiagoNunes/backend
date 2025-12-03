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

#Exceções de domínio
class DomainException(Exception):
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class AnoLetivoJaExisteException(DomainException):
    def __init__(self, ano: int):
        super().__init__(
            message=f"Ano letivo {ano} já existe",
            error_code="ANO_LETIVO_JA_EXISTE"
        )

class AnoLetivoNaoEncontradoException(DomainException):
    def __init__(self, ano_id: Optional[int] = None):
        if ano_id:
            message = f"Ano letivo ID {ano_id} não encontrado"
        else:
            message = "Ano letivo não encontrado"
        super().__init__(
            message=message,
            error_code="ANO_LETIVO_NAO_ENCONTRADO"
        )

class AnoLetivoJaArquivadoException(DomainException):
    def __init__(self, ano: Optional[int] = None):
        if ano:
            message = f"Ano letivo {ano} já está arquivado"
        else:
            message = "Ano letivo já está arquivado"
        super().__init__(
            message=message,
            error_code="ANO_LETIVO_JA_ARQUIVADO"
        )

class UploadNaoEncontradoException(DomainException):
    def __init__(self, upload_id: Optional[int] = None, ano_letivo_id: Optional[int] = None):
        if upload_id:
            message = f"Upload ID {upload_id} não encontrado"
        elif ano_letivo_id:
            message = f"Nenhum upload encontrado para o ano letivo {ano_letivo_id}"
        else:
            message = "Nenhum upload encontrado"
        super().__init__(
            message=message,
            error_code="UPLOAD_NAO_ENCONTRADO"
        )

class UploadInvalidoException(DomainException):
    def __init__(self, motivo: str):
        super().__init__(
            message=f"Upload inválido: {motivo}",
            error_code="UPLOAD_INVALIDO"
        )

class CalculoNaoEncontradoException(DomainException):
    def __init__(self, ano_letivo: Optional[int] = None):
        if ano_letivo:
            message = f"Nenhum cálculo encontrado para o ano letivo {ano_letivo}"
        else:
            message = "Nenhum cálculo encontrado"
        super().__init__(
            message=message,
            error_code="CALCULO_NAO_ENCONTRADO"
        )

class CalculoInvalidoException(DomainException):
    def __init__(self, motivo: str):
        super().__init__(
            message=f"Cálculo inválido: {motivo}",
            error_code="CALCULO_INVALIDO"
        )

class EscolaNaoEncontradaException(DomainException):
    def __init__(self, escola_id: Optional[int] = None, ano_letivo: Optional[int] = None):
        if escola_id:
            message = f"Escola ID {escola_id} não encontrada"
        elif ano_letivo:
            message = f"Nenhuma escola encontrada para o ano letivo {ano_letivo}"
        else:
            message = "Escola não encontrada"
        super().__init__(
            message=message,
            error_code="ESCOLA_NAO_ENCONTRADA"
        )


# HELPERS PARA CONVERSÃO
def domain_exception_to_http(domain_exception: DomainException) -> HTTPException:
    if isinstance(domain_exception, (
        AnoLetivoNaoEncontradoException,
        UploadNaoEncontradoException,
        CalculoNaoEncontradoException,
        EscolaNaoEncontradaException
    )):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(domain_exception, (
        AnoLetivoJaExisteException,
        AnoLetivoJaArquivadoException,
        UploadInvalidoException,
        CalculoInvalidoException
    )):
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    
    return HTTPException(
        status_code=status_code,
        detail=domain_exception.message
    )


def handle_exception(e: Exception, default_message: str = "Erro interno do servidor") -> HTTPException:
    if isinstance(e, HTTPException):
        return e
    
    if isinstance(e, DomainException):
        return domain_exception_to_http(e)
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=default_message
    )

