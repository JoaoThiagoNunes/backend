from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from src.core.database import get_db
from src.core.logging_config import logger
from src.core.exceptions import DomainException
from .service import ComplementoService
from .repository import ComplementoUploadRepository, ComplementoEscolaRepository
from src.modules.schemas.complemento import (
    UploadComplementoResponse,
    ComplementoUploadDetailResponse,
    ComplementoEscolaHistoricoResponse,
    ComplementoEscolaInfo
)


complemento_router = APIRouter()


@complemento_router.post("/upload", response_model=UploadComplementoResponse, tags=["Complemento"])
async def upload_complemento(
    file: UploadFile = File(...),
    ano_letivo_id: Optional[int] = Query(None, description="ID do ano letivo (padrão: ano ativo)"),
    upload_base_id: Optional[int] = Query(None, description="ID do upload base (padrão: upload ativo)"),
    db: Session = Depends(get_db)
) -> UploadComplementoResponse:
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx, .xls ou .csv)")
    
    try:
        contents = await file.read()
        resultado = ComplementoService.processar_planilha_complemento(
            db, contents, file.filename, ano_letivo_id, upload_base_id
        )
        
        # Buscar complemento_upload para obter upload_date
        complemento_repo = ComplementoUploadRepository(db)
        complemento_upload = complemento_repo.find_by_id(resultado["complemento_upload_id"])
        
        return UploadComplementoResponse(
            success=True,
            complemento_upload_id=resultado["complemento_upload_id"],
            ano_letivo_id=resultado["ano_letivo_id"],
            ano_letivo=resultado["ano_letivo"],
            filename=resultado["filename"],
            upload_date=complemento_upload.upload_date,
            total_escolas_processadas=resultado["total_escolas_processadas"],
            escolas_com_aumento=resultado["escolas_com_aumento"],
            escolas_sem_mudanca=resultado["escolas_sem_mudanca"],
            escolas_com_diminuicao=resultado["escolas_com_diminuicao"],
            escolas_com_erro=resultado["escolas_com_erro"],
            valor_complemento_total=resultado["valor_complemento_total"],
            escolas=None,  # Opcional, pode ser implementado depois
            erros=None
        )
        
    except HTTPException:
        raise
    except DomainException:
        raise
    except Exception as e:
        logger.exception("ERRO NO UPLOAD DE COMPLEMENTO")
        raise HTTPException(status_code=500, detail=f"Erro ao processar complemento: {str(e)}")


@complemento_router.get("/{complemento_upload_id}", response_model=ComplementoUploadDetailResponse, tags=["Complemento"])
def obter_complemento_detalhado(
    complemento_upload_id: int,
    db: Session = Depends(get_db)
) -> ComplementoUploadDetailResponse:
    complemento_repo = ComplementoUploadRepository(db)
    complemento_upload = complemento_repo.find_by_id(complemento_upload_id)
    
    if not complemento_upload:
        raise HTTPException(status_code=404, detail="Complemento não encontrado")
    
    complemento_escola_repo = ComplementoEscolaRepository(db)
    complementos_escola = complemento_escola_repo.find_by_complemento_upload(complemento_upload_id)
    
    # Calcular valor total
    valor_total = sum(c.valor_complemento_total or 0.0 for c in complementos_escola)
    
    # Mapear para schema
    escolas_info = []
    for ce in complementos_escola:
        escolas_info.append(ComplementoEscolaInfo(
            escola_id=ce.escola_id,
            nome_uex=ce.escola.nome_uex,
            dre=ce.escola.dre,
            status=ce.status.value,
            total_alunos_antes=ce.total_alunos_antes,
            total_alunos_depois=ce.total_alunos_depois,
            total_alunos_diferenca=ce.total_alunos_diferenca,
            valor_complemento_total=ce.valor_complemento_total
        ))
    
    return ComplementoUploadDetailResponse(
        complemento_upload_id=complemento_upload.id,
        ano_letivo_id=complemento_upload.ano_letivo_id,
        ano_letivo=complemento_upload.ano_letivo.ano,
        filename=complemento_upload.filename,
        upload_date=complemento_upload.upload_date,
        upload_base_id=complemento_upload.upload_base_id,
        upload_complemento_id=complemento_upload.upload_complemento_id,
        total_escolas_processadas=complemento_upload.total_escolas_processadas,
        escolas_com_aumento=complemento_upload.escolas_com_aumento,
        escolas_sem_mudanca=complemento_upload.escolas_sem_mudanca,
        escolas_com_diminuicao=complemento_upload.escolas_com_diminuicao,
        escolas_com_erro=complemento_upload.escolas_com_erro,
        valor_complemento_total=valor_total,
        escolas=escolas_info
    )


@complemento_router.get("/escola/{escola_id}", response_model=ComplementoEscolaHistoricoResponse, tags=["Complemento"])
def obter_complementos_escola(
    escola_id: int,
    db: Session = Depends(get_db)
) -> ComplementoEscolaHistoricoResponse:
    from src.modules.features.escolas.repository import EscolaRepository
    
    escola_repo = EscolaRepository(db)
    escola = escola_repo.find_by_id(escola_id)
    
    if not escola:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    
    complemento_escola_repo = ComplementoEscolaRepository(db)
    complementos = complemento_escola_repo.find_by_escola(escola_id)
    
    complementos_info = []
    for c in complementos:
        complementos_info.append({
            'complemento_upload_id': c.complemento_upload_id,
            'data': c.processed_at,
            'status': c.status.value,
            'total_alunos_diferenca': c.total_alunos_diferenca,
            'valor_complemento_total': c.valor_complemento_total
        })
    
    return ComplementoEscolaHistoricoResponse(
        escola_id=escola.id,
        nome_uex=escola.nome_uex,
        dre=escola.dre,
        complementos=complementos_info
    )


@complemento_router.get("/", tags=["Complemento"])
def listar_complementos(
    ano_letivo_id: Optional[int] = Query(None, description="Filtrar por ano letivo"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    db: Session = Depends(get_db)
):

    complemento_repo = ComplementoUploadRepository(db)
    
    if ano_letivo_id:
        complementos = complemento_repo.find_by_ano_letivo(ano_letivo_id)
    else:
        complementos = complemento_repo.find_all()
    
    # Paginação simples
    total = len(complementos)
    start = (page - 1) * page_size
    end = start + page_size
    complementos_paginados = complementos[start:end]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "complemento_upload_id": c.id,
                "ano_letivo_id": c.ano_letivo_id,
                "ano_letivo": c.ano_letivo.ano,
                "filename": c.filename,
                "upload_date": c.upload_date,
                "total_escolas_processadas": c.total_escolas_processadas,
                "escolas_com_aumento": c.escolas_com_aumento,
                "valor_complemento_total": sum(ce.valor_complemento_total or 0.0 for ce in c.complementos_escola)
            }
            for c in complementos_paginados
        ]
    }
