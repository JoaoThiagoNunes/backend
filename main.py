from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import BytesIO
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from database import engine, get_db
from models import Base, Upload, Escola, CalculosProfin, AnoLetivo, StatusAnoLetivo

# Criar todas as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# SCHEDULER PARA TAREFAS AUTOMÁTICAS
# ==========================================
scheduler = BackgroundScheduler()

def arquivar_anos_automaticamente():
    """
    Executa diariamente à meia-noite.
    Arquiva anos letivos que chegaram ao último dia do ano (31/12).
    """
    db = next(get_db())
    try:
        hoje = datetime.now()
        
        # Se for 31 de dezembro, arquiva o ano atual
        if hoje.month == 12 and hoje.day == 31:
            ano_atual = hoje.year
            ano_letivo = db.query(AnoLetivo).filter(
                AnoLetivo.ano == ano_atual,
                AnoLetivo.status == StatusAnoLetivo.ATIVO
            ).first()
            
            if ano_letivo:
                ano_letivo.status = StatusAnoLetivo.ARQUIVADO
                ano_letivo.arquivado_em = datetime.now()
                db.commit()
                print(f"✅ Ano letivo {ano_atual} arquivado automaticamente em {hoje}")
    except Exception as e:
        print(f"❌ Erro ao arquivar anos: {str(e)}")
        db.rollback()
    finally:
        db.close()

def limpar_anos_antigos():
    """
    Executa diariamente.
    Remove anos letivos arquivados há mais de 5 anos.
    """
    db = next(get_db())
    try:
        limite_data = datetime.now() - timedelta(days=5*365)  # 5 anos atrás
        
        anos_para_deletar = db.query(AnoLetivo).filter(
            AnoLetivo.status == StatusAnoLetivo.ARQUIVADO,
            AnoLetivo.arquivado_em <= limite_data
        ).all()
        
        count = 0
        for ano in anos_para_deletar:
            print(f"🗑️ Deletando ano letivo {ano.ano} (arquivado em {ano.arquivado_em})")
            db.delete(ano)  # Cascade deleta uploads, escolas, cálculos
            count += 1
        
        if count > 0:
            db.commit()
            print(f"✅ {count} ano(s) letivo(s) antigo(s) removido(s)")
    except Exception as e:
        print(f"❌ Erro ao limpar anos antigos: {str(e)}")
        db.rollback()
    finally:
        db.close()

# Agendar tarefas (executa todo dia à meia-noite)
scheduler.add_job(arquivar_anos_automaticamente, 'cron', hour=0, minute=0)
scheduler.add_job(limpar_anos_antigos, 'cron', hour=0, minute=30)
scheduler.start()

# ==========================================
# STARTUP: CRIAR ANO LETIVO INICIAL
# ==========================================
@app.on_event("startup")
def criar_ano_inicial():
    """
    Cria o ano letivo 2026 se não existir nenhum ano no banco.
    """
    db = next(get_db())
    try:
        total_anos = db.query(AnoLetivo).count()
        if total_anos == 0:
            ano_inicial = AnoLetivo(
                ano=2026,
                status=StatusAnoLetivo.ATIVO,
                created_at=datetime.now()
            )
            db.add(ano_inicial)
            db.commit()
            print("✅ Ano letivo 2026 criado automaticamente")
    except Exception as e:
        print(f"❌ Erro ao criar ano inicial: {str(e)}")
        db.rollback()
    finally:
        db.close()

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================
def limpar_uploads_antigos(db: Session, ano_letivo_id: int):
    """
    Remove uploads anteriores DO MESMO ANO LETIVO.
    Mantém isolamento entre anos.
    """
    uploads = db.query(Upload).filter(Upload.ano_letivo_id == ano_letivo_id).all()
    count = 0
    for up in uploads:
        db.delete(up)  # Cascade deleta escolas e cálculos
        count += 1
    db.commit()
    if count > 0:
        print(f"🗑️ {count} upload(s) anterior(es) do ano letivo removido(s)")

def obter_quantidade(row: pd.Series, coluna: str) -> int:
    valor = row.get(coluna, 0)
    try:
        return int(valor) if pd.notna(valor) else 0
    except (ValueError, TypeError):
        return 0

def obter_texto(row: pd.Series, coluna: str, default: str = "") -> str:
    valor = row.get(coluna, default)
    try:
        return str(valor) if pd.notna(valor) else default
    except (ValueError, TypeError):
        return default

def validar_indigena_e_quilombola(row: pd.Series, coluna: str) -> str:
    valor = row.get(coluna, "NÃO")
    try:
        return str(valor) if pd.notna(valor) else "NÃO"
    except (ValueError, TypeError):
        return "NÃO"

# ==========================================
# CÁLCULOS DAS COTAS (sem mudanças)
# ==========================================
def calcular_profin_custeio(row: pd.Series) -> float:
    valor_fixo = 2000.00
    
    fund_inicial = obter_quantidade(row, "FUNDAMENTAL INICIAL")
    fund_final = obter_quantidade(row, "FUNDAMENTAL FINAL")
    fund_integral = obter_quantidade(row, "FUNDAMENTAL INTEGRAL")
    profissionalizante = obter_quantidade(row, "PROFISSIONALIZANTE")
    alternancia = obter_quantidade(row, "ALTERNÂNCIA")
    medio_integral = obter_quantidade(row, "ENSINO MÉDIO INTEGRAL")
    medio_regular = obter_quantidade(row, "ENSINO MÉDIO REGULAR")
    esp_fund_regular = obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR")
    esp_fund_integral = obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL")
    esp_medio_parcial = obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL")
    esp_medio_integral = obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL")

    valor_variavel = (
        (fund_inicial * 1.0) +
        (fund_final * 1.10) +
        (fund_integral * 1.4) +
        (profissionalizante * 1.3) +
        ((alternancia * 1.4)*4.0) +
        (medio_integral * 1.4) +
        (medio_regular * 1.25) +
        ((esp_fund_regular * 1.0)*2.0) +
        ((esp_fund_integral * 1.4)*2.0) +
        ((esp_medio_parcial * 1.25)*2.0) +
        ((esp_medio_integral * 1.4)*2.0) 
    ) * 90.0

    valor_total = valor_fixo + valor_variavel
    return round(valor_total, 2)

def calcular_profin_projeto(row: pd.Series) -> float:
    fund_integral = obter_quantidade(row, "FUNDAMENTAL INTEGRAL")
    medio_integral = obter_quantidade(row, "ENSINO MÉDIO INTEGRAL")
    esp_fund_integral = obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL")
    esp_medio_integral = obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL")
    quantidade_aluno = obter_quantidade(row, "TOTAL")

    if (quantidade_aluno <= 500):
        if (fund_integral or medio_integral or esp_fund_integral or esp_medio_integral > 0):
            return round((5000 * 2), 2)
        return round(5000, 2)
    elif (quantidade_aluno > 500 and quantidade_aluno <= 1000):
        if (fund_integral or medio_integral or esp_fund_integral or esp_medio_integral > 0):
            return round((10000 * 2), 2)
        return round(10000, 2)
    else:
        if (fund_integral or medio_integral or esp_fund_integral or esp_medio_integral > 0):
            return round((15000 * 2), 2)
        return round(15000, 2)

def calcular_profin_kit_escolar(row: pd.Series) -> float:
    quantidade_aluno = obter_quantidade(row, "TOTAL")
    return round(quantidade_aluno * 150, 2)

def calcular_profin_uniforme(row: pd.Series) -> float:
    quantidade_aluno = obter_quantidade(row, "TOTAL")
    return round(quantidade_aluno * 60, 2)

def calcular_profin_merenda(row: pd.Series) -> float:
    valor_per_capita = 35.0

    fund_inicial = obter_quantidade(row, "FUNDAMENTAL INICIAL")
    fund_final = obter_quantidade(row, "FUNDAMENTAL FINAL")
    profissionalizante = obter_quantidade(row, "PROFISSIONALIZANTE")
    medio_regular = obter_quantidade(row, "ENSINO MÉDIO REGULAR")

    fund_integral = obter_quantidade(row, "FUNDAMENTAL INTEGRAL")
    medio_integral = obter_quantidade(row, "ENSINO MÉDIO INTEGRAL")
    esp_fund_integral = obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL")
    esp_medio_integral = obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL")
    esp_fund_regular = obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR")
    esp_medio_parcial = obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL")

    alternancia = obter_quantidade(row, "ALTERNÂNCIA")

    valor_total = (
        ((fund_inicial + fund_final + profissionalizante + medio_regular) * valor_per_capita) + 
        ((fund_integral + medio_integral + esp_fund_integral + esp_medio_integral + esp_fund_regular + esp_medio_parcial) * 2 * valor_per_capita) +
        (alternancia * (valor_per_capita * 4))
    )

    if (validar_indigena_e_quilombola(row, "INDIGENA & QUILOMBOLA") != "NÃO"):
        return round(valor_total * 2, 2)

    return round(valor_total, 2)

def calcular_profin_sala_recurso(row: pd.Series) -> float:
    if (obter_quantidade(row, "SALA DE RECURSO") != 0):
        valor_fixo = 2000
        quantidade_aluno = obter_quantidade(row, "SALA DE RECURSO")
        return round(quantidade_aluno * 180 + valor_fixo, 2)
    return 0.00

def calcular_profin_climatizacao(row: pd.Series) -> float:
    qtd_aparelhos = obter_quantidade(row, "CLIMATIZAÇÃO")
    return round(qtd_aparelhos * 300, 2)

def calcular_profin_preuni(row: pd.Series) -> float:
    qtd_alunos_preuni = obter_quantidade(row, "PREUNI")
    return round(qtd_alunos_preuni * 90, 2)

def calcular_profin_permanente(row: pd.Series) -> float:
    quantidade_aluno = obter_quantidade(row, "TOTAL")
    return round(quantidade_aluno * 110, 2)

def calcular_todas_cotas(row: pd.Series) -> Dict[str, Any]:
    profin_custeio = calcular_profin_custeio(row)
    profin_projeto = calcular_profin_projeto(row)
    profin_kit_escolar = calcular_profin_kit_escolar(row)
    profin_uniforme = calcular_profin_uniforme(row)
    profin_merenda = calcular_profin_merenda(row)
    profin_sala_recurso = calcular_profin_sala_recurso(row)
    profin_permanente = calcular_profin_permanente(row)
    profin_climatizacao = calcular_profin_climatizacao(row)
    profin_preuni = calcular_profin_preuni(row)
    
    cotas = {
        "profin_custeio": profin_custeio,
        "profin_projeto": profin_projeto,
        "profin_kit_escolar": profin_kit_escolar,
        "profin_uniforme": profin_uniforme,
        "profin_merenda": profin_merenda,
        "profin_sala_recurso": profin_sala_recurso,
        "profin_permanente": profin_permanente,
        "profin_climatizacao": profin_climatizacao,
        "profin_preuni": profin_preuni,
    }
    
    cotas["valor_total"] = round(sum([
        v for k, v in cotas.items() 
        if k not in ["tem_alternancia", "valor_total"] and isinstance(v, (int, float))
    ]), 2)
    
    return cotas

# ==========================================
# MODELOS PYDANTIC
# ==========================================
class AnoLetivoCreate(BaseModel):
    ano: int

class ResponseCalculos(BaseModel):
    success: bool
    message: str
    total_escolas: int
    valor_total_geral: float
    escolas: List[Dict[str, Any]]
    upload_id: int
    ano_letivo_id: int

# ==========================================
# ROTAS - ANOS LETIVOS
# ==========================================
@app.get("/anos-letivos")
def listar_anos_letivos(db: Session = Depends(get_db)):
    """Lista todos os anos letivos (ativos e arquivados)"""
    anos = db.query(AnoLetivo).order_by(AnoLetivo.ano.desc()).all()
    return {
        "success": True,
        "anos": [
            {
                "id": ano.id,
                "ano": ano.ano,
                "status": ano.status.value,
                "created_at": ano.created_at,
                "arquivado_em": ano.arquivado_em,
                "total_uploads": len(ano.uploads)
            }
            for ano in anos
        ]
    }

@app.get("/anos-letivos/ativo")
def obter_ano_ativo(db: Session = Depends(get_db)):
    """Retorna o ano letivo ativo atual"""
    ano = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
    if not ano:
        raise HTTPException(status_code=404, detail="Nenhum ano letivo ativo encontrado")
    
    return {
        "success": True,
        "ano": {
            "id": ano.id,
            "ano": ano.ano,
            "status": ano.status.value,
            "created_at": ano.created_at,
            "total_uploads": len(ano.uploads)
        }
    }

@app.post("/anos-letivos")
def criar_ano_letivo(data: AnoLetivoCreate, db: Session = Depends(get_db)):
    """
    Cria um novo ano letivo.
    Apenas um ano pode estar ATIVO por vez.
    """
    # Verificar se ano já existe
    ano_existente = db.query(AnoLetivo).filter(AnoLetivo.ano == data.ano).first()
    if ano_existente:
        raise HTTPException(status_code=400, detail=f"Ano letivo {data.ano} já existe")
    
    # Arquivar ano ativo atual (se houver)
    ano_ativo_atual = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
    if ano_ativo_atual:
        ano_ativo_atual.status = StatusAnoLetivo.ARQUIVADO
        ano_ativo_atual.arquivado_em = datetime.now()
    
    # Criar novo ano
    novo_ano = AnoLetivo(
        ano=data.ano,
        status=StatusAnoLetivo.ATIVO,
        created_at=datetime.now()
    )
    db.add(novo_ano)
    db.commit()
    db.refresh(novo_ano)
    
    return {
        "success": True,
        "message": f"Ano letivo {data.ano} criado com sucesso",
        "ano": {
            "id": novo_ano.id,
            "ano": novo_ano.ano,
            "status": novo_ano.status.value,
            "created_at": novo_ano.created_at
        }
    }

@app.put("/anos-letivos/{ano_id}/arquivar")
def arquivar_ano_letivo(ano_id: int, db: Session = Depends(get_db)):
    """Arquiva um ano letivo manualmente (requer admin)"""
    ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_id).first()
    if not ano:
        raise HTTPException(status_code=404, detail="Ano letivo não encontrado")
    
    if ano.status == StatusAnoLetivo.ARQUIVADO:
        raise HTTPException(status_code=400, detail="Ano letivo já está arquivado")
    
    ano.status = StatusAnoLetivo.ARQUIVADO
    ano.arquivado_em = datetime.now()
    db.commit()
    
    return {
        "success": True,
        "message": f"Ano letivo {ano.ano} arquivado com sucesso",
        "ano": {
            "id": ano.id,
            "ano": ano.ano,
            "status": ano.status.value,
            "arquivado_em": ano.arquivado_em
        }
    }

@app.delete("/anos-letivos/{ano_id}")
def deletar_ano_letivo(ano_id: int, db: Session = Depends(get_db)):
    """
    Deleta um ano letivo (apenas admin).
    Nota: Anos são deletados automaticamente após 5 anos de arquivamento.
    """
    ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_id).first()
    if not ano:
        raise HTTPException(status_code=404, detail="Ano letivo não encontrado")
    
    ano_numero = ano.ano
    db.delete(ano)  # Cascade deleta tudo relacionado
    db.commit()
    
    return {
        "success": True,
        "message": f"Ano letivo {ano_numero} e todos os dados relacionados foram deletados"
    }

# ==========================================
# ROTAS - UPLOAD E CÁLCULOS
# ==========================================
@app.get("/")
def read_root():
    return {"message": "API funcionando!", "versao": "2.0 - Com Anos Letivos"}

@app.post("/upload-excel")
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


@app.get("/uploads")
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

@app.get("/upload/{upload_id}")
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


@app.post("/calcular-valores", response_model=ResponseCalculos)
async def calcular_valores(
    ano_letivo_id: Optional[int] = Query(None, description="ID do ano letivo (usa ano ativo se não informado)"),
    db: Session = Depends(get_db)
):
    """
    Calcula os valores das escolas de um ano letivo específico.
    Se ano_letivo_id não for informado, usa o ano ativo.
    """
    try:
        # 1. Determinar ano letivo
        if ano_letivo_id is None:
            ano_letivo = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
            if not ano_letivo:
                raise HTTPException(status_code=400, detail="Nenhum ano letivo ativo encontrado")
            ano_letivo_id = ano_letivo.id
        else:
            ano_letivo = db.query(AnoLetivo).filter(AnoLetivo.id == ano_letivo_id).first()
            if not ano_letivo:
                raise HTTPException(status_code=404, detail=f"Ano letivo ID {ano_letivo_id} não encontrado")
        
        print(f"\n{'='*60}")
        print(f"CALCULANDO VALORES - ANO LETIVO: {ano_letivo.ano}")
        print(f"{'='*60}\n")
        
        # 2. Buscar escolas do ano letivo
        escolas = db.query(Escola).join(Upload).filter(
            Upload.ano_letivo_id == ano_letivo_id
        ).all()
        
        if not escolas:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhuma escola encontrada para o ano letivo {ano_letivo.ano}"
            )
        
        escolas_calculadas = []
        valor_total_geral = 0.0
        upload_id = escolas[0].upload_id if escolas else None
        
        # 3. Calcular para cada escola
        for escola_obj in escolas:
            # Criar objeto row-like para cálculos
            row_data = {
                "TOTAL": escola_obj.total_alunos,
                "FUNDAMENTAL INICIAL": escola_obj.fundamental_inicial,
                "FUNDAMENTAL FINAL": escola_obj.fundamental_final,
                "FUNDAMENTAL INTEGRAL": escola_obj.fundamental_integral,
                "PROFISSIONALIZANTE": escola_obj.profissionalizante,
                "ALTERNÂNCIA": escola_obj.alternancia,
                "ENSINO MÉDIO INTEGRAL": escola_obj.ensino_medio_integral,
                "ENSINO MÉDIO REGULAR": escola_obj.ensino_medio_regular,
                "ESPECIAL FUNDAMENTAL REGULAR": escola_obj.especial_fund_regular,
                "ESPECIAL FUNDAMENTAL INTEGRAL": escola_obj.especial_fund_integral,
                "ESPECIAL MÉDIO PARCIAL": escola_obj.especial_medio_parcial,
                "ESPECIAL MÉDIO INTEGRAL": escola_obj.especial_medio_integral,
                "SALA DE RECURSO": escola_obj.sala_recurso,
                "CLIMATIZAÇÃO": escola_obj.climatizacao,
                "PREUNI": escola_obj.preuni,
                "INDIGENA & QUILOMBOLA": escola_obj.indigena_quilombola
            }
            
            row_series = pd.Series(row_data)
            
            # Calcular todas as cotas
            cotas = calcular_todas_cotas(row_series)
            
            # Upsert na tabela CalculosProfin
            calculo_obj = db.query(CalculosProfin).filter(
                CalculosProfin.escola_id == escola_obj.id
            ).first()
            
            if calculo_obj:
                # Atualizar cálculo existente
                calculo_obj.profin_custeio = cotas["profin_custeio"]
                calculo_obj.profin_projeto = cotas["profin_projeto"]
                calculo_obj.profin_kit_escolar = cotas["profin_kit_escolar"]
                calculo_obj.profin_uniforme = cotas["profin_uniforme"]
                calculo_obj.profin_merenda = cotas["profin_merenda"]
                calculo_obj.profin_sala_recurso = cotas["profin_sala_recurso"]
                calculo_obj.profin_permanente = cotas["profin_permanente"]
                calculo_obj.profin_climatizacao = cotas["profin_climatizacao"]
                calculo_obj.profin_preuni = cotas["profin_preuni"]
                calculo_obj.valor_total = cotas["valor_total"]
                calculo_obj.calculated_at = datetime.now()
            else:
                # Criar novo cálculo
                calculo_obj = CalculosProfin(
                    escola_id=escola_obj.id,
                    profin_custeio=cotas["profin_custeio"],
                    profin_projeto=cotas["profin_projeto"],
                    profin_kit_escolar=cotas["profin_kit_escolar"],
                    profin_uniforme=cotas["profin_uniforme"],
                    profin_merenda=cotas["profin_merenda"],
                    profin_sala_recurso=cotas["profin_sala_recurso"],
                    profin_permanente=cotas["profin_permanente"],
                    profin_climatizacao=cotas["profin_climatizacao"],
                    profin_preuni=cotas["profin_preuni"],
                    valor_total=cotas["valor_total"],
                    calculated_at=datetime.now()
                )
                db.add(calculo_obj)
            
            escola_data = {
                "id": escola_obj.id,
                "nome_uex": escola_obj.nome_uex,
                "dre": escola_obj.dre,
                **cotas
            }
            
            escolas_calculadas.append(escola_data)
            valor_total_geral += cotas["valor_total"]
        
        db.commit()
        
        print(f"✅ Cálculos concluídos para {len(escolas_calculadas)} escolas")
        print(f"💰 Valor total: R$ {valor_total_geral:,.2f}")
        print(f"{'='*60}\n")
        
        return ResponseCalculos(
            success=True,
            message=f"Cálculos realizados para {len(escolas_calculadas)} escolas do ano {ano_letivo.ano}",
            total_escolas=len(escolas_calculadas),
            valor_total_geral=round(valor_total_geral, 2),
            escolas=escolas_calculadas,
            upload_id=upload_id,
            ano_letivo_id=ano_letivo_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao calcular: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valores: {str(e)}")

@app.delete("/limpar-dados")
def limpar_todos_dados(
    ano_letivo_id: Optional[int] = Query(None, description="Limpar apenas um ano específico"),
    db: Session = Depends(get_db)
):
    """
    CUIDADO: Apaga dados do banco.
    Se ano_letivo_id fornecido: apaga apenas aquele ano.
    Se não fornecido: apaga TUDO.
    """
    try:
        if ano_letivo_id:
            # Limpar apenas um ano específico
            ano = db.query(AnoLetivo).filter(AnoLetivo.id == ano_letivo_id).first()
            if not ano:
                raise HTTPException(status_code=404, detail="Ano letivo não encontrado")
            
            ano_numero = ano.ano
            db.delete(ano)  # Cascade deleta tudo relacionado
            db.commit()
            
            return {
                "success": True,
                "message": f"✅ Ano letivo {ano_numero} e todos os dados relacionados foram removidos"
            }
        else:
            # Limpar TUDO
            anos = db.query(AnoLetivo).all()
            count = len(anos)
            for ano in anos:
                db.delete(ano)
            db.commit()
            
            return {
                "success": True,
                "message": f"✅ {count} ano(s) letivo(s) e TODOS os dados foram removidos"
            }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar dados: {str(e)}")

@app.get("/status-dados")
def status_dados(db: Session = Depends(get_db)):
    """Retorna estatísticas gerais do banco de dados"""
    total_anos = db.query(AnoLetivo).count()
    total_uploads = db.query(Upload).count()
    total_escolas = db.query(Escola).count()
    total_calculos = db.query(CalculosProfin).count()
    
    ano_ativo = db.query(AnoLetivo).filter(AnoLetivo.status == StatusAnoLetivo.ATIVO).first()
    
    anos_lista = []
    for ano in db.query(AnoLetivo).order_by(AnoLetivo.ano.desc()).all():
        uploads_count = len(ano.uploads)
        escolas_count = sum([len(up.escolas) for up in ano.uploads])
        
        anos_lista.append({
            "id": ano.id,
            "ano": ano.ano,
            "status": ano.status.value,
            "uploads": uploads_count,
            "escolas": escolas_count,
            "created_at": ano.created_at,
            "arquivado_em": ano.arquivado_em
        })
    
    return {
        "success": True,
        "resumo": {
            "total_anos_letivos": total_anos,
            "total_uploads": total_uploads,
            "total_escolas": total_escolas,
            "total_calculos": total_calculos
        },
        "ano_ativo": {
            "id": ano_ativo.id,
            "ano": ano_ativo.ano,
            "status": ano_ativo.status.value
        } if ano_ativo else None,
        "anos": anos_lista
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "versao": "2.0",
        "features": ["anos_letivos", "arquivamento_automatico", "isolamento_por_ano"]
    }
        