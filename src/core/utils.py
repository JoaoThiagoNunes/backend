import pandas as pd
from sqlalchemy.orm import Session
from src.modules.models import Upload, AnoLetivo, StatusAnoLetivo
from src.core.logging_config import logger
from fastapi import HTTPException
from typing import Dict, Any, Optional, Tuple, Union

# ==================
# BUSCAS E LIMPEZA
# ==================
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
    if count > 0:
        db.commit()
        logger.info(f"🗑️ {count} upload(s) anterior(es) do ano letivo removido(s)")
    else:
        db.rollback()  # Se não há nada para deletar, não precisa de commit

def obter_ano_letivo(
    db: Session,
    ano_letivo_id: Optional[int] = None,
    raise_if_not_found: bool = True
) -> Union[Tuple[AnoLetivo, int], Tuple[None, None]]:
    """
    Determina e retorna o ano letivo baseado no ID fornecido ou no ano ativo.
    
    Esta função centraliza a lógica duplicada de determinar ano letivo
    que estava espalhada em várias rotas.
    
    Args:
        db: Sessão do banco de dados
        ano_letivo_id: ID do ano letivo (opcional). Se None, busca o ano ativo.
        raise_if_not_found: Se True, lança exceção se não encontrar. Se False, retorna None.
    
    Returns:
        Tupla (AnoLetivo, ano_letivo_id)
    
    Raises:
        HTTPException: Se ano_letivo_id não for encontrado ou não houver ano ativo.
    
    Exemplo:
        ano_letivo, ano_id = obter_ano_letivo(db, ano_letivo_id=2024)
        ano_letivo, ano_id = obter_ano_letivo(db)  # Usa ano ativo
    """
    if ano_letivo_id is None:
        # Buscar ano letivo ativo
        ano_letivo = db.query(AnoLetivo).filter(
            AnoLetivo.status == StatusAnoLetivo.ATIVO
        ).first()
        
        if not ano_letivo:
            if raise_if_not_found:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhum ano letivo ativo encontrado. Crie um ano primeiro."
                )
            return None, None
        
        ano_letivo_id = ano_letivo.id
    else:
        # Buscar ano letivo por ID
        ano_letivo = db.query(AnoLetivo).filter(
            AnoLetivo.id == ano_letivo_id
        ).first()
        
        if not ano_letivo:
            if raise_if_not_found:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ano letivo ID {ano_letivo_id} não encontrado"
                )
            return None, None
    
    return ano_letivo, ano_letivo_id

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

# ===================
# CÁLCULOS DAS COTAS 
# ===================
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

    # Verificar se tem ensino integral (corrigido: cada variável deve ser verificada separadamente)
    tem_integral = (
        fund_integral > 0 or 
        medio_integral > 0 or 
        esp_fund_integral > 0 or 
        esp_medio_integral > 0
    )
    
    if quantidade_aluno <= 500:
        if tem_integral:
            return round((5000 * 2), 2)
        return round(5000, 2)
    elif quantidade_aluno > 500 and quantidade_aluno <= 1000:
        if tem_integral:
            return round((10000 * 2), 2)
        return round(10000, 2)
    else:
        if tem_integral:
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