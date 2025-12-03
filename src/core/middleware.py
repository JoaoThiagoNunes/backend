import time
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.core.logging_config import logger
from src.core.exceptions import (
    BaseAPIException,
    DomainException,
    domain_exception_to_http,
    handle_exception
)


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    start_time = time.time()
    
    # Log da requisição recebida
    logger.info(
        f"→ {request.method} {request.url.path} "
        f"[Client: {request.client.host if request.client else 'unknown'}]"
    )
    
    # Processar requisição
    response = await call_next(request)
    
    # Calcular tempo de processamento
    process_time = time.time() - start_time
    
    # Log da resposta
    logger.info(
        f"← {request.method} {request.url.path} "
        f"[Status: {response.status_code}] "
        f"[Time: {process_time:.3f}s]"
    )
    
    # Adicionar header com tempo de processamento
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    try:
        response = await call_next(request)
        return response
    
    except DomainException as e:
        logger.warning(
            f"Domain Exception: {e.error_code} - {e.message} "
            f"[Path: {request.url.path}]"
        )
        http_exception = domain_exception_to_http(e)
        return JSONResponse(
            status_code=http_exception.status_code,
            content={
                "success": False,
                "error": http_exception.detail,
                "error_code": e.error_code,
                "path": str(request.url.path)
            }
        )
    
    except BaseAPIException as e:
        # Exceções customizadas do projeto
        logger.warning(
            f"API Exception: {e.status_code} - {e.detail} "
            f"[Path: {request.url.path}]"
        )
        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "error": e.detail,
                "error_code": e.error_code,
                "path": str(request.url.path)
            }
        )
    
    except StarletteHTTPException as e:
        # HTTPException do FastAPI/Starlette
        logger.warning(
            f"HTTP Exception: {e.status_code} - {e.detail} "
            f"[Path: {request.url.path}]"
        )
        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "error": e.detail,
                "status_code": e.status_code,
                "path": str(request.url.path)
            }
        )
    
    except RequestValidationError as e:
        # Erros de validação do Pydantic
        logger.warning(
            f"Validation Error: {e.errors()} "
            f"[Path: {request.url.path}]"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Erro de validação",
                "error_code": "VALIDATION_ERROR",
                "details": e.errors(),
                "path": str(request.url.path)
            }
        )
    
    except Exception as e:
        # Erros não tratados
        logger.exception(
            f"Unhandled Exception: {str(e)} "
            f"[Path: {request.url.path}]"
        )
        http_exception = handle_exception(e)
        return JSONResponse(
            status_code=http_exception.status_code,
            content={
                "success": False,
                "error": http_exception.detail,
                "error_code": "INTERNAL_SERVER_ERROR",
                "path": str(request.url.path)
            }
        )

