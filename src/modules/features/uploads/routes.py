from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.logging_config import logger
from src.core.exceptions import DomainException
from src.modules.schemas.upload import (
    UploadListItem,
    UploadDetailResponse,
    UploadExcelResponse,
    ErroUpload,
)
from src.modules.features.uploads import UploadService
from typing import Optional

upload_router = APIRouter()


@upload_router.get("", response_model=UploadListItem, tags=["Uploads"])
def obter_upload_unico(
    ano_letivo_id: Optional[int] = Query(None, description="Filtrar por ano letivo"),
    db: Session = Depends(get_db)
) -> UploadListItem:
    return UploadService.obter_upload_unico(db, ano_letivo_id)

@upload_router.get("/detalhes", response_model=UploadDetailResponse, tags=["Uploads"])
def obter_upload_detalhado(
    ano_letivo_id: Optional[int] = Query(
        None, description="Ano letivo que deseja consultar (padrão: ano ativo)"
    ),
    db: Session = Depends(get_db)
) -> UploadDetailResponse:
    resultado = UploadService.obter_upload_detalhado(db, ano_letivo_id)
    
    return UploadDetailResponse(
        success=True,
        upload=resultado["upload"],
        escolas=resultado["escolas"]
    )



@upload_router.post("/excel", response_model=UploadExcelResponse, tags=["Uploads"])
async def upload_excel(
    file: UploadFile = File(...),
    ano_letivo_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> UploadExcelResponse:
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx, .xls ou .csv)")
    
    try:
        contents = await file.read()
        resultado = UploadService.processar_planilha_excel(db, contents, file.filename, ano_letivo_id)
        
        erros = None
        aviso = None
        if resultado["escolas_com_erro"] > 0:
            erros = [ErroUpload(**erro) for erro in resultado["escolas_com_erro_lista"][:10]]
            aviso = f"{resultado['escolas_com_erro']} escolas tiveram erro ao salvar"
        
        return UploadExcelResponse(
            success=True,
            upload_id=resultado["upload_id"],
            ano_letivo_id=resultado["ano_letivo_id"],
            ano_letivo=resultado["ano_letivo"],
            filename=resultado["filename"],
            total_linhas=resultado["total_linhas"],
            escolas_salvas=resultado["escolas_salvas"],
            escolas_confirmadas_banco=resultado["escolas_confirmadas_banco"],
            escolas_com_erro=resultado["escolas_com_erro"],
            colunas=resultado["colunas"],
            erros=erros,
            aviso=aviso
        )
        
    except (HTTPException, DomainException):
        raise
    except Exception as e:
        logger.exception("ERRO NO UPLOAD")
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

