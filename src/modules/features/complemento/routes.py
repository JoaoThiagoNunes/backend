from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
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
    ComplementoEscolaInfo,
    LiberarComplementoRequest,
    LiberarComplementoResponse,
    ListarLiberacoesComplementoRequest,
    ListarLiberacoesComplementoResponse,
    AtualizarLiberacaoComplementoRequest,
    LiberacaoComplementoResponse,
    ComplementoResumoResponse
)
from .repository import LiberacaoComplementoRepository


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




@complemento_router.get("/repasse", response_model=ComplementoResumoResponse, tags=["Complemento"])
def obter_complementos_agrupados(
    ano_letivo_id: Optional[int] = Query(None, description="ID do ano letivo (padrão: ano ativo)"),
    complemento_upload_id: Optional[int] = Query(None, description="Filtrar por complemento_upload_id"),
    db: Session = Depends(get_db)
) -> ComplementoResumoResponse:
    """Obtém resumo de complementos agrupados por folhas."""
    try:
        resultado = ComplementoService.obter_complementos_agrupados(
            db,
            ano_letivo_id,
            complemento_upload_id
        )
        
        return ComplementoResumoResponse(**resultado)
    except Exception as e:
        logger.exception("ERRO AO OBTER COMPLEMENTOS AGRUPADOS")
        raise HTTPException(status_code=500, detail=f"Erro ao obter complementos agrupados: {str(e)}")


@complemento_router.get("/liberacoes", response_model=ListarLiberacoesComplementoResponse, tags=["Complemento"])
def listar_liberacoes_complemento(
    complemento_upload_id: Optional[int] = Query(None, description="Filtrar por complemento_upload_id (padrão: mais recente)"),
    numero_folha: Optional[int] = Query(None, description="Filtrar por número da folha"),
    liberada: Optional[bool] = Query(None, description="Filtrar por status de liberação"),
    escola_id: Optional[int] = Query(None, description="Filtrar por escola_id"),
    ano_letivo_id: Optional[int] = Query(None, description="ID do ano letivo (usado para buscar complemento_upload mais recente)"),
    db: Session = Depends(get_db)
) -> ListarLiberacoesComplementoResponse:
    """Lista liberações de complemento com filtros opcionais."""
    # Se não informado complemento_upload_id, buscar o mais recente
    if complemento_upload_id is None:
        from src.modules.features.anos import obter_ano_letivo
        _, ano_id = obter_ano_letivo(db, ano_letivo_id)
        complemento_repo = ComplementoUploadRepository(db)
        complemento_upload_recente = complemento_repo.find_mais_recente_by_ano_letivo(ano_id)
        if complemento_upload_recente:
            complemento_upload_id = complemento_upload_recente.id
    
    liberacao_repo = LiberacaoComplementoRepository(db)
    
    query = liberacao_repo.db.query(liberacao_repo.model)
    
    if complemento_upload_id:
        query = query.filter(liberacao_repo.model.complemento_upload_id == complemento_upload_id)
    if numero_folha:
        query = query.filter(liberacao_repo.model.numero_folha == numero_folha)
    if liberada is not None:
        query = query.filter(liberacao_repo.model.liberada == liberada)
    if escola_id:
        query = query.filter(liberacao_repo.model.escola_id == escola_id)
    
    liberacoes = query.options(joinedload(liberacao_repo.model.escola)).all()
    
    liberacoes_info = [
        ComplementoService.mapear_liberacao_complemento(lib) for lib in liberacoes
    ]
    
    return ListarLiberacoesComplementoResponse(
        success=True,
        total=len(liberacoes_info),
        liberacoes=liberacoes_info
    )


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
            valor_complemento_total=ce.valor_complemento_total,
            valor_complemento_gestao=ce.valor_complemento_gestao,
            valor_complemento_kit_escolar=ce.valor_complemento_kit_escolar,
            valor_complemento_uniforme=ce.valor_complemento_uniforme,
            valor_complemento_merenda=ce.valor_complemento_merenda,
            valor_complemento_sala_recurso=ce.valor_complemento_sala_recurso
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
            'valor_complemento_total': c.valor_complemento_total,
            'valor_complemento_gestao': c.valor_complemento_gestao,
            'valor_complemento_kit_escolar': c.valor_complemento_kit_escolar,
            'valor_complemento_uniforme': c.valor_complemento_uniforme,
            'valor_complemento_merenda': c.valor_complemento_merenda,
            'valor_complemento_sala_recurso': c.valor_complemento_sala_recurso
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


@complemento_router.post("/liberar", response_model=LiberarComplementoResponse, tags=["Complemento"])
def liberar_escolas_complemento(
    request: LiberarComplementoRequest,
    db: Session = Depends(get_db)
) -> LiberarComplementoResponse:
    """Libera escolas para uma folha de complemento."""
    try:
        liberacoes = ComplementoService.liberar_escolas_complemento(
            db,
            request.escola_ids,
            request.numero_folha,
            request.complemento_upload_id,
            request.ano_letivo_id
        )
        
        liberacoes_info = [
            ComplementoService.mapear_liberacao_complemento(lib) for lib in liberacoes
        ]
        
        return LiberarComplementoResponse(
            success=True,
            message=f"{len(liberacoes)} escola(s) liberada(s) para folha {request.numero_folha}",
            total_escolas_atualizadas=len(liberacoes),
            numero_folha=request.numero_folha,
            liberacoes=liberacoes_info
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("ERRO AO LIBERAR ESCOLAS PARA COMPLEMENTO")
        raise HTTPException(status_code=500, detail=f"Erro ao liberar escolas: {str(e)}")


@complemento_router.put("/liberacoes/{liberacao_id}", response_model=LiberacaoComplementoResponse, tags=["Complemento"])
def atualizar_liberacao_complemento(
    liberacao_id: int,
    request: AtualizarLiberacaoComplementoRequest,
    db: Session = Depends(get_db)
) -> LiberacaoComplementoResponse:
    """Atualiza uma liberação de complemento."""
    liberacao_repo = LiberacaoComplementoRepository(db)
    liberacao = liberacao_repo.find_by_id(liberacao_id)
    
    if not liberacao:
        raise HTTPException(status_code=404, detail="Liberação não encontrada")
    
    try:
        update_data = {}
        if request.liberada is not None:
            update_data['liberada'] = request.liberada
        if request.numero_folha is not None:
            update_data['numero_folha'] = request.numero_folha
        if request.data_liberacao is not None:
            update_data['data_liberacao'] = request.data_liberacao
        
        if update_data:
            liberacao_repo.update(liberacao, **update_data)
        
        liberacao_info = ComplementoService.mapear_liberacao_complemento(liberacao)
        
        return LiberacaoComplementoResponse(
            success=True,
            message="Liberação atualizada com sucesso",
            liberacao=liberacao_info
        )
    except Exception as e:
        logger.exception("ERRO AO ATUALIZAR LIBERAÇÃO DE COMPLEMENTO")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar liberação: {str(e)}")


