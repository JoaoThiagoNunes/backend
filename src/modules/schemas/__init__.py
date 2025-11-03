from .ano import (
    AnoLetivoCreate, AnoLetivoRead, AnoLetivoListResponse,
    AnoLetivoDetailResponse, AnoLetivoCreateResponse,
    AnoLetivoArquivarResponse, AnoLetivoDeleteResponse
)
from .upload import (
    UploadListResponse, UploadDetailResponse, UploadExcelResponse,
    UploadListItem, UploadDetailInfo, EscolaComCalculo, ErroUpload
)
from .escola import EscolaCreate, EscolaRead, EscolaInfo
from .calculos import ResponseCalculos, EscolaCalculo, CalculoItem
from .auth import LoginRequest, LoginResponse
from .admin import (
    RootResponse, LimparDadosResponse, StatusDadosResponse,
    HealthCheckResponse
)

__all__ = [
    # Anos
    "AnoLetivoCreate", "AnoLetivoRead", "AnoLetivoListResponse",
    "AnoLetivoDetailResponse", "AnoLetivoCreateResponse",
    "AnoLetivoArquivarResponse", "AnoLetivoDeleteResponse",
    # Uploads
    "UploadListResponse", "UploadDetailResponse", "UploadExcelResponse",
    "UploadListItem", "UploadDetailInfo", "EscolaComCalculo", "ErroUpload",
    # Escolas
    "EscolaCreate", "EscolaRead", "EscolaInfo",
    # Cálculos
    "ResponseCalculos", "EscolaCalculo", "CalculoItem",
    # Auth
    "LoginRequest", "LoginResponse",
    # Admin
    "RootResponse", "LimparDadosResponse", "StatusDadosResponse",
    "HealthCheckResponse",
]
