from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import BytesIO
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database import engine, get_db
from models import Base, Upload, Escola, CalculosProfin, ConfiguracaoSistema

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
# CONFIGURAÇÕES
# ==========================================
MODO_GERENCIAMENTO = "substituir"  # "substituir" | "historico" | "limite"
LIMITE_UPLOADS = 5

# ==========================================
# ARMAZENAMENTO EM MEMÓRIA
# ==========================================
dados_armazenados = {
    "df": None,
    "filename": None,
    "timestamp": None,
    "upload_id": None
}

# ==========================================
# FUNÇÕES AUXILIARES (mantidas)
# ==========================================
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
# FUNÇÕES DE GERENCIAMENTO DE DADOS (corrigidas)
# ==========================================
def limpar_uploads_antigos(db: Session, modo: str = MODO_GERENCIAMENTO):
    """Gerencia uploads antigos conforme o modo configurado.
       Importante: usar db.delete(obj) para ativar cascade ORM e evitar FK violations.
    """
    if modo == "substituir":
        uploads = db.query(Upload).all()
        count = 0
        for up in uploads:
            db.delete(up)  # ativa cascade: deleta escolas e calculos via ORM
            count += 1
        db.commit()
        print(f"🗑️ Modo SUBSTITUIR: {count} uploads antigos removidos")
        
    elif modo == "historico":
        # Desativa todos os uploads (marca is_active = False)
        db.query(Upload).update({"is_active": False})
        db.commit()
        print("📚 Modo HISTÓRICO: uploads anteriores desativados")
        
    elif modo == "limite":
        # Mantém apenas os últimos N uploads
        uploads_antigos = (
            db.query(Upload)
            .order_by(Upload.upload_date.desc())
            .offset(LIMITE_UPLOADS)
            .all()
        )
        count = 0
        for upload in uploads_antigos:
            db.delete(upload)  # delete via ORM -> cascade
            count += 1
        db.commit()
        print(f"📊 Modo LIMITE: removidos {count} uploads antigos, mantidos últimos {LIMITE_UPLOADS}")

def obter_upload_ativo(db: Session) -> Optional[Upload]:
    """Retorna o upload ativo (ou mais recente se modo histórico)"""
    if MODO_GERENCIAMENTO == "historico":
        return db.query(Upload).filter(Upload.is_active == True).first()
    else:
        return db.query(Upload).order_by(Upload.upload_date.desc()).first()

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

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
# FUNÇÕES DE GERENCIAMENTO DE DADOS
# ==========================================

def limpar_uploads_antigos(db: Session, modo: str = MODO_GERENCIAMENTO):
    """Gerencia uploads antigos conforme o modo configurado"""
    
    if modo == "substituir":
        # Apaga TODOS os uploads antigos
        count = db.query(Upload).delete()
        db.commit()
        print(f"🗑️ Modo SUBSTITUIR: {count} uploads antigos removidos")
        
    elif modo == "historico":
        # Desativa todos os uploads (marca is_active = False)
        db.query(Upload).update({"is_active": False})
        db.commit()
        print("📚 Modo HISTÓRICO: uploads anteriores desativados")
        
    elif modo == "limite":
        # Mantém apenas os últimos N uploads
        uploads_antigos = (
            db.query(Upload)
            .order_by(Upload.upload_date.desc())
            .offset(LIMITE_UPLOADS)
            .all()
        )
        for upload in uploads_antigos:
            db.delete(upload)
        db.commit()
        print(f"📊 Modo LIMITE: mantidos últimos {LIMITE_UPLOADS} uploads")

def obter_upload_ativo(db: Session) -> Optional[Upload]:
    """Retorna o upload ativo (ou mais recente se modo histórico)"""
    if MODO_GERENCIAMENTO == "historico":
        return db.query(Upload).filter(Upload.is_active == True).first()
    else:
        return db.query(Upload).order_by(Upload.upload_date.desc()).first()

# ==========================================
# CÁLCULOS DAS COTAS
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
# MODELOS DE DADOS (ResponseCalculos mantido)
class ResponseCalculos(BaseModel):
    success: bool
    message: str
    total_escolas: int
    valor_total_geral: float
    escolas: List[Dict[str, Any]]
    upload_id: int

# ==========================================
# ROTAS
# ==========================================
@app.get("/")
def read_root():
    return {
        "message": "API PROFIN funcionando!",
        "modo_gerenciamento": MODO_GERENCIAMENTO,
        "limite_uploads": LIMITE_UPLOADS if MODO_GERENCIAMENTO == "limite" else None
    }

@app.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    limpar_antigos: bool = Query(True, description="Limpar uploads antigos conforme modo configurado")
) -> Dict[str, Any]:
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls ou .csv)")
    
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # LIMPAR DADOS ANTIGOS (conforme modo configurado)
        if limpar_antigos:
            limpar_uploads_antigos(db, MODO_GERENCIAMENTO)
        
        # Criar registro de upload
        upload = Upload(
            filename=file.filename,
            total_escolas=len(df),
            upload_date=datetime.now(),
            is_active=True
        )
        db.add(upload)
        db.commit()
        db.refresh(upload)
        
        # Armazenar em memória
        dados_armazenados["df"] = df
        dados_armazenados["filename"] = file.filename
        dados_armazenados["timestamp"] = datetime.now()
        dados_armazenados["upload_id"] = upload.id
        
        # Converter para dicionário (retorno)
        data = df.to_dict(orient='records')
        
        info = {
            "upload_id": upload.id,
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data": data,
            "modo_gerenciamento": MODO_GERENCIAMENTO
        }
        
        return {
            "success": True,
            "message": f"Arquivo processado! Modo: {MODO_GERENCIAMENTO}",
            "info": info
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/calcular-valores", response_model=ResponseCalculos)
async def calcular_valores(db: Session = Depends(get_db)):
    """Calcula os valores e salva no banco de dados — agora com upsert por nome_uex + dre"""
    if dados_armazenados["df"] is None:
        raise HTTPException(
            status_code=400, 
            detail="Nenhum arquivo foi enviado ainda. Faça upload primeiro usando /upload-excel"
        )
    
    try:
        df = dados_armazenados["df"]
        upload_id = dados_armazenados["upload_id"]
        
        escolas_calculadas = []
        valor_total_geral = 0.0
        
        for idx, row in df.iterrows():
            nome_escola = (
                row.get('NOME DA UEX') or 
                row.get('nome') or 
                row.get('Escola') or 
                f"Escola {idx + 1}"
            )
            nome_escola = str(nome_escola).strip()
            dre_val = obter_texto(row, "DRE", None)
            
            # Busca por escola existente (unique: nome_uex + dre)
            query = db.query(Escola).filter(Escola.nome_uex == nome_escola)
            if dre_val:
                query = query.filter(Escola.dre == dre_val)
            else:
                # procurar null dre também
                query = query.filter(Escola.dre.is_(None))
            
            escola_obj = query.first()
            
            if escola_obj:
                # Atualiza a escola existente
                escola_obj.upload_id = upload_id
                escola_obj.total_alunos = obter_quantidade(row, "TOTAL")
                escola_obj.fundamental_inicial = obter_quantidade(row, "FUNDAMENTAL INICIAL")
                escola_obj.fundamental_final = obter_quantidade(row, "FUNDAMENTAL FINAL")
                escola_obj.fundamental_integral = obter_quantidade(row, "FUNDAMENTAL INTEGRAL")
                escola_obj.profissionalizante = obter_quantidade(row, "PROFISSIONALIZANTE")
                escola_obj.alternancia = obter_quantidade(row, "ALTERNÂNCIA")
                escola_obj.ensino_medio_integral = obter_quantidade(row, "ENSINO MÉDIO INTEGRAL")
                escola_obj.ensino_medio_regular = obter_quantidade(row, "ENSINO MÉDIO REGULAR")
                escola_obj.especial_fund_regular = obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR")
                escola_obj.especial_fund_integral = obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL")
                escola_obj.especial_medio_parcial = obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL")
                escola_obj.especial_medio_integral = obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL")
                escola_obj.sala_recurso = obter_quantidade(row, "SALA DE RECURSO")
                escola_obj.climatizacao = obter_quantidade(row, "CLIMATIZAÇÃO")
                escola_obj.preuni = obter_quantidade(row, "PREUNI")
                escola_obj.indigena_quilombola = validar_indigena_e_quilombola(row, "INDIGENA & QUILOMBOLA")
                
                db.add(escola_obj)
                db.flush()
            else:
                # Cria nova escola
                escola_obj = Escola(
                    upload_id=upload_id,
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
            
            # Calcular todas as cotas
            cotas = calcular_todas_cotas(row)
            
            # Upsert/calcula na tabela CalculosProfin: atualizar se existe, senão criar
            calculo_obj = db.query(CalculosProfin).filter(CalculosProfin.escola_id == escola_obj.id).first()
            if calculo_obj:
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
                db.add(calculo_obj)
            else:
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
                "nome_uex": nome_escola,
                **cotas
            }
            
            escolas_calculadas.append(escola_data)
            valor_total_geral += cotas["valor_total"]
        
        db.commit()
        
        return ResponseCalculos(
            success=True,
            message=f"Cálculos realizados e salvos para {len(escolas_calculadas)} escolas",
            total_escolas=len(escolas_calculadas),
            valor_total_geral=round(valor_total_geral, 2),
            escolas=escolas_calculadas,
            upload_id=upload_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valores: {str(e)}")

@app.get("/uploads")
def listar_uploads(
    db: Session = Depends(get_db),
    apenas_ativo: bool = Query(False, description="Retornar apenas upload ativo")
):
    if apenas_ativo:
        upload = obter_upload_ativo(db)
        return {"uploads": [upload] if upload else []}
    
    uploads = db.query(Upload).order_by(Upload.upload_date.desc()).all()
    return {"uploads": uploads}

@app.get("/upload/{upload_id}")
def obter_upload(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado")
    
    escolas = db.query(Escola).filter(Escola.upload_id == upload_id).all()
    
    escolas_com_calculos = []
    for escola in escolas:
        calculo = db.query(CalculosProfin).filter(CalculosProfin.escola_id == escola.id).first()
        escolas_com_calculos.append({
            "escola": escola,
            "calculos": calculo
        })
    
    return {
        "upload": upload,
        "escolas": escolas_com_calculos
    }

@app.delete("/limpar-dados")
def limpar_todos_dados(db: Session = Depends(get_db)):
    """CUIDADO: Apaga TODOS os dados do banco"""
    try:
        uploads = db.query(Upload).all()
        count_uploads = len(uploads)
        for up in uploads:
            db.delete(up)  # usar ORM delete para ativar cascade
        db.commit()
        return {
            "success": True,
            "message": f"✅ {count_uploads} uploads e todos os dados relacionados foram removidos"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar dados: {str(e)}")

@app.get("/configuracao")
def obter_configuracao():
    return {
        "modo_gerenciamento": MODO_GERENCIAMENTO,
        "limite_uploads": LIMITE_UPLOADS if MODO_GERENCIAMENTO == "limite" else None,
        "descricao": {
            "substituir": "Apaga todos os uploads antigos a cada novo upload",
            "historico": "Mantém histórico completo, marca uploads como ativos/inativos",
            "limite": f"Mantém apenas os últimos {LIMITE_UPLOADS} uploads"
        }[MODO_GERENCIAMENTO]
    }

@app.get("/status-dados")
def status_dados(db: Session = Depends(get_db)):
    total_uploads = db.query(Upload).count()
    total_escolas = db.query(Escola).count()
    upload_ativo = obter_upload_ativo(db)
    
    return {
        "dados_disponiveis": dados_armazenados["df"] is not None,
        "memoria": {
            "filename": dados_armazenados["filename"],
            "timestamp": dados_armazenados["timestamp"],
            "upload_id": dados_armazenados["upload_id"],
        } if dados_armazenados["df"] is not None else None,
        "banco": {
            "total_uploads": total_uploads,
            "total_escolas": total_escolas,
            "upload_ativo": {
                "id": upload_ativo.id,
                "filename": upload_ativo.filename,
                "total_escolas": upload_ativo.total_escolas
            } if upload_ativo else None
        },
        "configuracao": {
            "modo": MODO_GERENCIAMENTO,
            "limite": LIMITE_UPLOADS if MODO_GERENCIAMENTO == "limite" else None
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
