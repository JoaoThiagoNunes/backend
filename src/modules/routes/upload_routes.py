from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.logging_config import logger
from src.modules.schemas.upload import (
    UploadListResponse, UploadDetailResponse, UploadExcelResponse,
    UploadListItem, UploadDetailInfo, EscolaComCalculo, CalculoInfo, ErroUpload
)
from src.modules.schemas.escola import EscolaInfo
from src.modules.models import  *
from datetime import datetime
from typing import Optional
from io import BytesIO
import pandas as pd
from src.core.utils import limpar_uploads_antigos, obter_texto, obter_quantidade, validar_indigena_e_quilombola, obter_ano_letivo

router = APIRouter()


@router.get("", response_model=UploadListResponse, tags=["Uploads"])
def listar_uploads(
    ano_letivo_id: Optional[int] = Query(None, description="Filtrar por ano letivo"),
    db: Session = Depends(get_db)
) -> UploadListResponse:
    """Lista uploads, opcionalmente filtrados por ano letivo"""
    query = db.query(Upload)
    
    if ano_letivo_id:
        query = query.filter(Upload.ano_letivo_id == ano_letivo_id)
    
    uploads = query.order_by(Upload.upload_date.desc()).all()
    
    return UploadListResponse(
        success=True,
        uploads=[
            UploadListItem(
                id=up.id,
                ano_letivo_id=up.ano_letivo_id,
                ano_letivo=up.ano_letivo.ano,
                filename=up.filename,
                upload_date=up.upload_date,
                total_escolas=up.total_escolas,
                is_active=up.is_active
            )
            for up in uploads
        ]
    )

@router.get("/{upload_id}", response_model=UploadDetailResponse, tags=["Uploads"])
def obter_upload(upload_id: int, db: Session = Depends(get_db)) -> UploadDetailResponse:
    """Retorna detalhes de um upload específico com suas escolas"""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado")
    
    escolas = db.query(Escola).filter(Escola.upload_id == upload_id).all()
    
    escolas_com_calculos = []
    for escola in escolas:
        calculo = db.query(CalculosProfin).filter(CalculosProfin.escola_id == escola.id).first()
        escolas_com_calculos.append(
            EscolaComCalculo(
                escola=EscolaInfo(
                    id=escola.id,
                    nome_uex=escola.nome_uex,
                    dre=escola.dre,
                    total_alunos=escola.total_alunos,
                    fundamental_inicial=escola.fundamental_inicial,
                    fundamental_final=escola.fundamental_final,
                    fundamental_integral=escola.fundamental_integral,
                    profissionalizante=escola.profissionalizante,
                    alternancia=escola.alternancia,
                    ensino_medio_integral=escola.ensino_medio_integral,
                    ensino_medio_regular=escola.ensino_medio_regular,
                    especial_fund_regular=escola.especial_fund_regular,
                    especial_fund_integral=escola.especial_fund_integral,
                    especial_medio_parcial=escola.especial_medio_parcial,
                    especial_medio_integral=escola.especial_medio_integral,
                    sala_recurso=escola.sala_recurso,
                    climatizacao=escola.climatizacao,
                    preuni=escola.preuni,
                    indigena_quilombola=escola.indigena_quilombola,
                    created_at=escola.created_at
                ),
                calculos=CalculoInfo(
                    id=calculo.id,
                    profin_custeio=calculo.profin_custeio,
                    profin_projeto=calculo.profin_projeto,
                    profin_kit_escolar=calculo.profin_kit_escolar,
                    profin_uniforme=calculo.profin_uniforme,
                    profin_merenda=calculo.profin_merenda,
                    profin_sala_recurso=calculo.profin_sala_recurso,
                    profin_permanente=calculo.profin_permanente,
                    profin_climatizacao=calculo.profin_climatizacao,
                    profin_preuni=calculo.profin_preuni,
                    valor_total=calculo.valor_total,
                    calculated_at=calculo.calculated_at
                ) if calculo else None
            )
        )
    
    return UploadDetailResponse(
        success=True,
        upload=UploadDetailInfo(
            id=upload.id,
            ano_letivo_id=upload.ano_letivo_id,
            ano_letivo=upload.ano_letivo.ano,
            filename=upload.filename,
            upload_date=upload.upload_date,
            total_escolas=upload.total_escolas
        ),
        escolas=escolas_com_calculos
    )



@router.post("/excel", response_model=UploadExcelResponse, tags=["Uploads"])
async def upload_excel(
    file: UploadFile = File(...),
    ano_letivo_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> UploadExcelResponse:
   
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx, .xls ou .csv)")
    
    try:
        # 1. Determinar ano letivo (usando função centralizada)
        ano_letivo, ano_letivo_id = obter_ano_letivo(db, ano_letivo_id)
        
        logger.info("="*60)
        logger.info(f"UPLOAD PARA ANO LETIVO: {ano_letivo.ano} (Status: {ano_letivo.status.value})")
        logger.info("="*60)
        
        # 2. Ler arquivo
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(contents))
        else:
            df = pd.read_excel(BytesIO(contents))
        
        logger.info(f"Arquivo: {file.filename}")
        logger.info(f"Total de linhas: {len(df)}")
        logger.debug(f"Colunas: {df.columns.tolist()}")
        
        # 3. Limpar uploads anteriores DO MESMO ANO
        limpar_uploads_antigos(db, ano_letivo_id)
        
        # 4. Criar registro de upload
        upload = Upload(
            ano_letivo_id=ano_letivo_id,
            filename=file.filename,
            total_escolas=0,
            upload_date=datetime.now(),
            is_active=True
        )
        db.add(upload)
        db.flush()  # Usar flush para obter ID sem commit ainda
        db.refresh(upload)
        
        logger.info(f"Upload registrado com ID: {upload.id}")
        
        # 5. Salvar cada escola no banco
        escolas_salvas = 0
        escolas_com_erro = []
        
        for idx, row in df.iterrows():
            try:
                # Obter nome da escola
                nome_escola = (
                    row.get('NOME DA UEX') or 
                    row.get('nome') or 
                    row.get('Escola') or 
                    f"Escola {idx + 1}"
                )
                nome_escola = str(nome_escola).strip()
                
                # Obter DRE
                dre_val = obter_texto(row, "DRE", None)
                
                if (idx + 1) % 50 == 0 or idx == 0:  # Log apenas a cada 50 linhas
                    logger.debug(f"[{idx + 1}/{len(df)}] Processando: {nome_escola} (DRE: {dre_val or 'N/A'})")
                
                # Criar objeto Escola
                escola_obj = Escola(
                    upload_id=upload.id,
                    nome_uex=nome_escola,
                    dre=dre_val,
                    total_alunos=obter_quantidade(row, "TOTAL"),
                    fundamental_inicial=obter_quantidade(row, "FUNDAMENTAL INICIAL"),
                    fundamental_final=obter_quantidade(row, "FUNDAMENTAL FINAL"),
                    fundamental_integral=obter_quantidade(row, "FUNDAMENTAL INTEGRAL"),
                    profissionalizante=obter_quantidade(row, "PROFISSIONALIZANTE"),
                    alternancia=obter_quantidade(row, "ALTERNÂNCIA"),
                    ensino_medio_integral=obter_quantidade(row, "ENSINO MÉDIO INTEGRAL"),
                    ensino_medio_regular=obter_quantidade(row, "ENSINO MÉDIO REGULAR"),
                    especial_fund_regular=obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR"),
                    especial_fund_integral=obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL"),
                    especial_medio_parcial=obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL"),
                    especial_medio_integral=obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL"),
                    sala_recurso=obter_quantidade(row, "SALA DE RECURSO"),
                    climatizacao=obter_quantidade(row, "CLIMATIZAÇÃO"),
                    preuni=obter_quantidade(row, "PREUNI"),
                    indigena_quilombola=validar_indigena_e_quilombola(row, "INDIGENA & QUILOMBOLA")
                )
                
                db.add(escola_obj)
                db.flush()  # Flush para obter ID, commit será feito depois em batch
                
                escolas_salvas += 1
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Erro ao processar linha {idx + 1} ({nome_escola}): {error_msg}")
                escolas_com_erro.append({
                    "linha": idx + 1,
                    "nome": nome_escola if 'nome_escola' in locals() else 'Desconhecido',
                    "erro": error_msg
                })
                continue
        
        # 6. Commit final (transação padronizada: único commit após todas as operações)
        upload.total_escolas = escolas_salvas
        db.commit()
        
        # 7. Verificar no banco
        total_no_banco = db.query(Escola).filter(Escola.upload_id == upload.id).count()
        
        logger.info("="*60)
        logger.info(f"✅ UPLOAD CONCLUÍDO")
        logger.info(f"Ano letivo: {ano_letivo.ano}")
        logger.info(f"Escolas salvas: {escolas_salvas}")
        logger.info(f"Confirmadas no banco: {total_no_banco}")
        logger.warning(f"Erros: {len(escolas_com_erro)}" if escolas_com_erro else "Sem erros")
        logger.info("="*60)
        
        # 9. Retornar resposta
        erros = None
        aviso = None
        if escolas_com_erro:
            erros = [ErroUpload(**erro) for erro in escolas_com_erro[:10]]
            aviso = f"{len(escolas_com_erro)} escolas tiveram erro ao salvar"
        
        return UploadExcelResponse(
            success=True,
            upload_id=upload.id,
            ano_letivo_id=ano_letivo_id,
            ano_letivo=ano_letivo.ano,
            filename=file.filename,
            total_linhas=len(df),
            escolas_salvas=escolas_salvas,
            escolas_confirmadas_banco=total_no_banco,
            escolas_com_erro=len(escolas_com_erro),
            colunas=df.columns.tolist(),
            erros=erros,
            aviso=aviso
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("❌ ERRO NO UPLOAD")
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

