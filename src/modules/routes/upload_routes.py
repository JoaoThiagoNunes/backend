from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.schemas.upload import *
from src.modules.models import  *
from datetime import datetime
from typing import Dict, Any, Optional
from io import BytesIO
import pandas as pd
from src.core.utils import limpar_uploads_antigos, obter_texto, obter_quantidade, validar_indigena_e_quilombola

router = APIRouter()


@router.post("/upload-excel", tags=["Uploads"])
async def upload_excel(
    file: UploadFile = File(...),
    ano_letivo_id: Optional[int] = Query(None, description="ID do ano letivo (usa ano ativo se não informado)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Faz upload de arquivo Excel/CSV e salva as escolas no banco de dados.
    Se ano_letivo_id não for informado, usa o ano ativo atual.
    """
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx, .xls ou .csv)")
    
    try:
        # 1. Determinar ano letivo
        if ano_letivo_id is None:
            ano_letivo = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
            if not ano_letivo:
                raise HTTPException(status_code=400, detail="Nenhum ano letivo ativo. Crie um ano primeiro.")
            ano_letivo_id = ano_letivo.id
        else:
            ano_letivo = db.query(AnoLetivo).filter(AnoLetivo.id == ano_letivo_id).first()
            if not ano_letivo:
                raise HTTPException(status_code=404, detail=f"Ano letivo ID {ano_letivo_id} não encontrado")
        
        print(f"\n{'='*60}")
        print(f"UPLOAD PARA ANO LETIVO: {ano_letivo.ano} (Status: {ano_letivo.status.value})")
        print(f"{'='*60}\n")
        
        # 2. Ler arquivo
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(contents))
        else:
            df = pd.read_excel(BytesIO(contents))
        
        print(f"Arquivo: {file.filename}")
        print(f"Total de linhas: {len(df)}")
        print(f"Colunas: {df.columns.tolist()}\n")
        
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
        db.commit()
        db.refresh(upload)
        
        print(f"Upload registrado com ID: {upload.id}\n")
        
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
                
                print(f"[{idx + 1}/{len(df)}] Processando: {nome_escola} (DRE: {dre_val or 'N/A'})")
                
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
                db.flush()
                
                escolas_salvas += 1
                print(f"✅ Salva! (ID: {escola_obj.id}, Total alunos: {escola_obj.total_alunos})")
                
            except Exception as e:
                error_msg = str(e)
                print(f"   ❌ ERRO: {error_msg}")
                escolas_com_erro.append({
                    "linha": idx + 1,
                    "nome": nome_escola if 'nome_escola' in locals() else 'Desconhecido',
                    "erro": error_msg
                })
                continue
        
        # 6. Commit final
        db.commit()
        
        # 7. Atualizar total de escolas no upload
        upload.total_escolas = escolas_salvas
        db.commit()
        
        # 8. Verificar no banco
        total_no_banco = db.query(Escola).filter(Escola.upload_id == upload.id).count()
        
        print(f"\n{'='*60}")
        print(f"✅ UPLOAD CONCLUÍDO")
        print(f"Ano letivo: {ano_letivo.ano}")
        print(f"Escolas salvas: {escolas_salvas}")
        print(f"Confirmadas no banco: {total_no_banco}")
        print(f"Erros: {len(escolas_com_erro)}")
        print(f"{'='*60}\n")
        
        # 9. Retornar resposta
        response = {
            "success": True,
            "upload_id": upload.id,
            "ano_letivo_id": ano_letivo_id,
            "ano_letivo": ano_letivo.ano,
            "filename": file.filename,
            "total_linhas": len(df),
            "escolas_salvas": escolas_salvas,
            "escolas_confirmadas_banco": total_no_banco,
            "escolas_com_erro": len(escolas_com_erro),
            "colunas": df.columns.tolist(),
        }
        
        if escolas_com_erro:
            response["erros"] = escolas_com_erro[:10]
            response["aviso"] = f"{len(escolas_com_erro)} escolas tiveram erro ao salvar"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"\n{'='*60}")
        print(f"❌ ERRO NO UPLOAD")
        print(f"Erro: {str(e)}")
        print(f"{'='*60}\n")
        
        import traceback
        traceback.print_exc()
        
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")


@router.get("/uploads", tags=["Uploads"])
def listar_uploads(
    ano_letivo_id: Optional[int] = Query(None, description="Filtrar por ano letivo"),
    db: Session = Depends(get_db)
):
    """Lista uploads, opcionalmente filtrados por ano letivo"""
    query = db.query(Upload)
    
    if ano_letivo_id:
        query = query.filter(Upload.ano_letivo_id == ano_letivo_id)
    
    uploads = query.order_by(Upload.upload_date.desc()).all()
    
    return {
        "success": True,
        "uploads": [
            {
                "id": up.id,
                "ano_letivo_id": up.ano_letivo_id,
                "ano_letivo": up.ano_letivo.ano,
                "filename": up.filename,
                "upload_date": up.upload_date,
                "total_escolas": up.total_escolas,
                "is_active": up.is_active
            }
            for up in uploads
        ]
    }

@router.get("/upload/{upload_id}", tags=["Uploads"])
def obter_upload(upload_id: int, db: Session = Depends(get_db)):
    """Retorna detalhes de um upload específico com suas escolas"""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado")
    
    escolas = db.query(Escola).filter(Escola.upload_id == upload_id).all()
    
    escolas_com_calculos = []
    for escola in escolas:
        calculo = db.query(CalculosProfin).filter(CalculosProfin.escola_id == escola.id).first()
        escolas_com_calculos.append({
            "escola": {
                "id": escola.id,
                "nome_uex": escola.nome_uex,
                "dre": escola.dre,
                "total_alunos": escola.total_alunos,
                "created_at": escola.created_at
            },
            "calculos": {
                "id": calculo.id,
                "profin_custeio": calculo.profin_custeio,
                "profin_projeto": calculo.profin_projeto,
                "profin_kit_escolar": calculo.profin_kit_escolar,
                "profin_uniforme": calculo.profin_uniforme,
                "profin_merenda": calculo.profin_merenda,
                "profin_sala_recurso": calculo.profin_sala_recurso,
                "profin_permanente": calculo.profin_permanente,
                "profin_climatizacao": calculo.profin_climatizacao,
                "profin_preuni": calculo.profin_preuni,
                "valor_total": calculo.valor_total,
                "calculated_at": calculo.calculated_at
            } if calculo else None
        })
    
    return {
        "success": True,
        "upload": {
            "id": upload.id,
            "ano_letivo_id": upload.ano_letivo_id,
            "ano_letivo": upload.ano_letivo.ano,
            "filename": upload.filename,
            "upload_date": upload.upload_date,
            "total_escolas": upload.total_escolas
        },
        "escolas": escolas_com_calculos
    }

