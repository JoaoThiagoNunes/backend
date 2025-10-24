from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import BytesIO
from typing import Dict, Any, List
from pydantic import BaseModel

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
# ARMAZENAMENTO EM MEMÓRIA
# ==========================================
dados_armazenados = {
    "df": None,
    "filename": None,
    "timestamp": None
}

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def obter_quantidade(row: pd.Series, coluna: str) -> int:
    """
    Obtém a quantidade de uma coluna específica
    Trata valores nulos, NaN e strings vazias
    """
    valor = row.get(coluna, 0)
    try:
        return int(valor) if pd.notna(valor) else 0
    except (ValueError, TypeError):
        return 0

def validar_indigena_e_quilombola(row: pd.Series, coluna: str) -> str:
    """
    Obtém o valor da coluna INDIGENA & QUILOMBOLA 
    """
    valor = row.get(coluna, 0)
    try:
        return valor if pd.notna(valor) else 0
    except (ValueError, TypeError):
        return 0




# ==========================================
# CÁLCULOS DAS COTAS
# ==========================================

def calcular_profin_custeio(row: pd.Series) -> float:
    """
    Calcula PROFIN Custeio conforme regras estabelecidas
    
    Regras:
    - Valor fixo anual: R$ 2.000,00
    - fórmula 
    """
    # Valor fixo
    valor_fixo = 2000.00
    
    # Obter quantidades de alunos
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
    # Obter quantidades 
    fund_integral = obter_quantidade(row, "FUNDAMENTAL INTEGRAL")
    medio_integral = obter_quantidade(row, "ENSINO MÉDIO INTEGRAL")
    esp_fund_integral = obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL")
    esp_medio_integral = obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL")
    quantidade_aluno = obter_quantidade(row, "TOTAL")

    if (quantidade_aluno <= 500):
        if (fund_integral or medio_integral or esp_fund_integral or esp_medio_integral > 0):
            return round((5.000 * 2), 2)
        return round(5.000, 2)

    elif (quantidade_aluno > 500 and quantidade_aluno <= 1000):
        if (fund_integral or medio_integral or esp_fund_integral or esp_medio_integral > 0):
            return round((10.000 * 2), 2)
        return round(10.000, 2)

    else:
        if (fund_integral or medio_integral or esp_fund_integral or esp_medio_integral > 0):
            return round((15.000 * 2), 2)
        return round(15.000, 2)


def calcular_profin_kit_escolar(row: pd.Series) -> float:
    quantidade_aluno = obter_quantidade(row, "TOTAL")
    return round(quantidade_aluno * 150, 2)


def calcular_profin_uniforme(row: pd.Series) -> float:
    quantidade_aluno = obter_quantidade(row, "TOTAL")
    return round(quantidade_aluno * 60, 2)


def calcular_profin_merenda(row: pd.Series) -> float:
    valor_per_capita = 35.0

    #Alunos regulares
    fund_inicial = obter_quantidade(row, "FUNDAMENTAL INICIAL")
    fund_final = obter_quantidade(row, "FUNDAMENTAL FINAL")
    profissionalizante = obter_quantidade(row, "PROFISSIONALIZANTE")
    medio_regular = obter_quantidade(row, "ENSINO MÉDIO REGULAR")

    #Alunos integrais
    fund_integral = obter_quantidade(row, "FUNDAMENTAL INTEGRAL")
    medio_integral = obter_quantidade(row, "ENSINO MÉDIO INTEGRAL")
    esp_fund_integral = obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL")
    esp_medio_integral = obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL")
    esp_fund_regular = obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR")
    esp_medio_parcial = obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL")

    #Alunos alternantes
    alternancia = obter_quantidade(row, "ALTERNÂNCIA")

    valor_total = (
        (((fund_inicial + fund_final + profissionalizante + medio_regular) * valor_per_capita) + 
        (((fund_integral + medio_integral + esp_fund_integral + esp_medio_integral + esp_fund_regular + esp_medio_parcial)*2)*valor_per_capita)+
        (alternancia * (valor_per_capita * 4)))  
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
    """
    Calcula todas as cotas para uma escola
    """
    # Calcular cada cota
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
    
    # Calcular valor total (soma de todas as cotas)
    cotas["valor_total"] = round(sum([
        v for k, v in cotas.items() 
        if k not in ["tem_alternancia", "valor_total"] and isinstance(v, (int, float))
    ]), 2)
    
    return cotas

# ==========================================
# MODELOS DE DADOS
# ==========================================

class ResponseCalculos(BaseModel):
    success: bool
    message: str
    total_escolas: int
    valor_total_geral: float
    escolas: List[Dict[str, Any]]

# ==========================================
# ROTAS
# ==========================================

@app.get("/")
def read_root():
    return {"message": "API de Upload de Excel funcionando!"}


@app.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Rota para fazer upload do Excel e armazenar em memória
    """
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls ou .csv)")
    
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # Armazenar em memória
        from datetime import datetime
        dados_armazenados["df"] = df
        dados_armazenados["filename"] = file.filename
        dados_armazenados["timestamp"] = datetime.now()
        
        # Converter para dicionário
        data = df.to_dict(orient='records')
        
        info = {
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data": data
        }
        
        return {
            "success": True,
            "message": "Arquivo processado e armazenado com sucesso!",
            "info": info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")


@app.post("/calcular-valores", response_model=ResponseCalculos)
async def calcular_valores():
    """
    Calcula os valores usando o último arquivo enviado (armazenado em memória)
    """
    if dados_armazenados["df"] is None:
        raise HTTPException(
            status_code=400, 
            detail="Nenhum arquivo foi enviado ainda. Faça upload primeiro usando /upload-excel"
        )
    
    try:
        df = dados_armazenados["df"]
        
        escolas_calculadas = []
        valor_total_geral = 0.0
        
        # Processar cada escola
        for idx, row in df.iterrows():
            # Obter nome da escola
            nome_escola = (
                row.get('NOME DA UEX') or 
                row.get('nome') or 
                row.get('Escola') or 
                f"Escola {idx + 1}"
            )
            
            # Calcular todas as cotas
            cotas = calcular_todas_cotas(row)
            
            # Montar objeto da escola
            escola_data = {
                "nome_uex": nome_escola,
                **cotas
            }
            
            escolas_calculadas.append(escola_data)
            valor_total_geral += cotas["valor_total"]
        
        return ResponseCalculos(
            success=True,
            message=f"Cálculos realizados para {len(escolas_calculadas)} escolas",
            total_escolas=len(escolas_calculadas),
            valor_total_geral=round(valor_total_geral, 2),
            escolas=escolas_calculadas
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valores: {str(e)}")


@app.get("/status-dados")
def status_dados():
    """
    Verifica se existem dados armazenados em memória
    """
    if dados_armazenados["df"] is None:
        return {
            "dados_disponiveis": False,
            "message": "Nenhum arquivo foi carregado ainda"
        }
    
    df = dados_armazenados["df"]
    return {
        "dados_disponiveis": True,
        "filename": dados_armazenados["filename"],
        "timestamp": dados_armazenados["timestamp"],
        "total_escolas": len(df),
        "colunas": df.columns.tolist()
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ==========================================
# EXEMPLO DE TESTE MANUAL
# ==========================================
"""
Para testar individualmente o cálculo de uma escola, você pode adicionar:

@app.post("/testar-calculo-individual")
async def testar_calculo_individual(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_excel(BytesIO(contents))
    
    # Pegar apenas a primeira escola para teste
    primeira_escola = df.iloc[0]
    
    resultado = {
        "nome": primeira_escola.get('NOME DA UEX', 'Não informado'),
        "tem_alternancia": verificar_escola_com_alternancia(primeira_escola),
        "alunos": {
            "fundamental_inicial": obter_quantidade_alunos(primeira_escola, "FUNDAMENTAL INICIAL"),
            "fundamental_final": obter_quantidade_alunos(primeira_escola, "FUNDAMENTAL FINAL"),
            "alternancia": obter_quantidade_alunos(primeira_escola, "ALTERNÂNCIA"),
        },
        "calculos": calcular_todas_cotas(primeira_escola)
    }
    
    return resultado
"""