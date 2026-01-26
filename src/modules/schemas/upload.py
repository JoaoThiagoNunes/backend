from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class UploadListItem(BaseModel):
    success: bool = True
    id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    upload_date: datetime
    total_escolas: int

class EscolaPlanilhaInfo(BaseModel):
    dados_planilha: Dict[str, Any]

class UploadDetailInfo(BaseModel):
    id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    upload_date: datetime
    total_escolas: int

class UploadDetailResponse(BaseModel):
    success: bool = True
    upload: UploadDetailInfo
    escolas: List[EscolaPlanilhaInfo]

class ErroUpload(BaseModel):
    linha: int
    nome: str
    erro: str

class UploadExcelResponse(BaseModel):
    success: bool = True
    upload_id: int
    ano_letivo_id: int
    ano_letivo: int
    filename: str
    total_linhas: int
    escolas_salvas: int
    escolas_confirmadas_banco: int
    escolas_com_erro: int
    colunas: List[str]
    erros: Optional[List[ErroUpload]] = None
    aviso: Optional[str] = None
