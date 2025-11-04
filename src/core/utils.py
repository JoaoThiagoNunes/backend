import pandas as pd
from sqlalchemy.orm import Session
from src.modules.models import Upload, AnoLetivo, StatusAnoLetivo, Escola
from src.core.logging_config import logger
from fastapi import HTTPException
from typing import Dict, Any, Optional, Tuple, Union
from datetime import datetime

# ==================
# BUSCAS E LIMPEZA
# ==================
def obter_ou_criar_upload_ativo(db: Session, ano_letivo_id: int, filename: str) -> Upload:
    """
    Busca upload ativo do ano letivo ou cria novo.
    Se encontrar upload ativo, atualiza filename e data.
    Mantém o mesmo upload_id para substituir dados ao invés de deletar.
    
    Args:
        db: Sessão do banco de dados
        ano_letivo_id: ID do ano letivo
        filename: Nome do arquivo sendo enviado
    
    Returns:
        Upload (existente atualizado ou novo criado)
    """
    # Buscar upload ativo do ano
    upload_existente = db.query(Upload).filter(
        Upload.ano_letivo_id == ano_letivo_id,
        Upload.is_active == True
    ).first()
    
    if upload_existente:
        # Atualizar upload existente (substituir, não deletar)
        upload_existente.filename = filename
        upload_existente.upload_date = datetime.now()
        upload_existente.total_escolas = 0  # Será atualizado depois
        logger.info(f"📝 Atualizando upload existente ID {upload_existente.id} (substituindo dados)")
        return upload_existente
    else:
        # Criar novo upload
        novo_upload = Upload(
            ano_letivo_id=ano_letivo_id,
            filename=filename,
            total_escolas=0,
            upload_date=datetime.now(),
            is_active=True
        )
        db.add(novo_upload)
        logger.info(f"✨ Criando novo upload para ano letivo {ano_letivo_id}")
        return novo_upload

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

# ===================
# PARCELAS E ENSINO
# ===================
def calcular_porcentagens_ensino(escola: Escola) -> Tuple[float, float]:
    """
    Calcula a porcentagem de alunos em cada tipo de ensino (fundamental vs médio).
    
    Usa pesos (multiplicadores) para cada tipo de modalidade antes de calcular a porcentagem.
    
    Args:
        escola: Objeto Escola com dados dos alunos
    
    Returns:
        Tupla (porcentagem_fundamental, porcentagem_medio)
        Valores entre 0.0 e 100.0
    """
    # Pesos (multiplicadores) para cada modalidade
    PESO_FUND_INICIAL = 1.0
    PESO_FUND_FINAL = 1.10
    PESO_FUND_INTEGRAL = 1.40
    PESO_ESP_FUND_REGULAR = 1.0
    PESO_ESP_FUND_INTEGRAL = 1.40
    
    PESO_PROFISSIONALIZANTE = 1.30
    PESO_ALTERNANCIA = 1.40
    PESO_MEDIO_INTEGRAL = 1.40
    PESO_MEDIO_REGULAR = 1.25
    PESO_ESP_MEDIO_PARCIAL = 1.25
    PESO_ESP_MEDIO_INTEGRAL = 1.40
    
    # Calcular valor ponderado de FUNDAMENTAL (numerador)
    valor_fundamental = (
        (escola.fundamental_inicial * PESO_FUND_INICIAL) +
        (escola.fundamental_final * PESO_FUND_FINAL) +
        (escola.fundamental_integral * PESO_FUND_INTEGRAL) +
        (escola.especial_fund_regular * PESO_ESP_FUND_REGULAR) +
        (escola.especial_fund_integral * PESO_ESP_FUND_INTEGRAL)
    )
    
    # Calcular valor ponderado de MÉDIO
    valor_medio = (
        (escola.profissionalizante * PESO_PROFISSIONALIZANTE) +
        (escola.alternancia * PESO_ALTERNANCIA) +
        (escola.ensino_medio_integral * PESO_MEDIO_INTEGRAL) +
        (escola.ensino_medio_regular * PESO_MEDIO_REGULAR) +
        (escola.especial_medio_parcial * PESO_ESP_MEDIO_PARCIAL) +
        (escola.especial_medio_integral * PESO_ESP_MEDIO_INTEGRAL)
    )
    
    # Denominador = soma de TODOS (fundamental + médio) com pesos
    denominador = valor_fundamental + valor_medio
    
    # Verificar se há alunos (denominador > 0)
    if denominador == 0:
        return (0.0, 0.0)
    
    # Calcular porcentagem de FUNDAMENTAL
    pct_fundamental = (valor_fundamental / denominador) * 100.0
    
    # MÉDIO = o que falta para completar 100%
    pct_medio = 100.0 - pct_fundamental
    
    return (round(pct_fundamental, 2), round(pct_medio, 2))


def dividir_em_parcelas(valor_reais: float) -> Tuple[int, int]:
    """
    Divide um valor em duas parcelas iguais (ou quase iguais).
    Retorna valores em centavos (inteiros).
    
    Args:
        valor_reais: Valor em reais (float)
    
    Returns:
        Tupla (parcela_1_centavos, parcela_2_centavos)
    """
    # Converter para centavos (multiplicar por 100 e arredondar)
    valor_centavos = int(round(valor_reais * 100))
    
    # Dividir em duas parcelas
    parcela_1 = valor_centavos // 2
    parcela_2 = valor_centavos - parcela_1  # Resto vai para a segunda parcela
    
    return (parcela_1, parcela_2)


def dividir_parcela_por_ensino(
    parcela_centavos: int,
    porcentagem_fundamental: float,
    porcentagem_medio: float
) -> Tuple[int, int]:
    """
    Divide uma parcela entre ensino fundamental e médio baseado nas porcentagens.
    Distribui o resto de centavos de forma determinística.
    
    Args:
        parcela_centavos: Valor da parcela em centavos (inteiro)
        porcentagem_fundamental: Porcentagem de alunos em fundamental (0-100)
        porcentagem_medio: Porcentagem de alunos em médio (0-100)
    
    Returns:
        Tupla (valor_fundamental_centavos, valor_medio_centavos)
    """
    # Calcular valores baseados nas porcentagens
    valor_fundamental = int(round((parcela_centavos * porcentagem_fundamental) / 100.0))
    valor_medio = int(round((parcela_centavos * porcentagem_medio) / 100.0))
    
    # Distribuir o resto (se houver)
    resto = parcela_centavos - (valor_fundamental + valor_medio)
    
    if resto != 0:
        # Distribuir resto para o tipo de ensino com maior porcentagem
        # Se empate, dar para fundamental
        if porcentagem_fundamental >= porcentagem_medio:
            valor_fundamental += resto
        else:
            valor_medio += resto
    
    return (valor_fundamental, valor_medio)


def dividir_cota_em_parcelas_por_ensino(
    valor_cota_reais: float,
    porcentagem_fundamental: float,
    porcentagem_medio: float
) -> Dict[str, Dict[str, int]]:
    """
    Divide uma cota completa em 2 parcelas, e cada parcela por tipo de ensino.
    
    Args:
        valor_cota_reais: Valor total da cota em reais
        porcentagem_fundamental: Porcentagem de alunos em fundamental
        porcentagem_medio: Porcentagem de alunos em médio
    
    Returns:
        Dicionário com estrutura:
        {
            "parcela_1": {
                "fundamental": centavos,
                "medio": centavos
            },
            "parcela_2": {
                "fundamental": centavos,
                "medio": centavos
            }
        }
    """
    # Dividir em 2 parcelas
    parcela_1_centavos, parcela_2_centavos = dividir_em_parcelas(valor_cota_reais)
    
    # Dividir cada parcela por ensino
    parcela_1_fund, parcela_1_medio = dividir_parcela_por_ensino(
        parcela_1_centavos, porcentagem_fundamental, porcentagem_medio
    )
    
    parcela_2_fund, parcela_2_medio = dividir_parcela_por_ensino(
        parcela_2_centavos, porcentagem_fundamental, porcentagem_medio
    )
    
    return {
        "parcela_1": {
            "fundamental": parcela_1_fund,
            "medio": parcela_1_medio
        },
        "parcela_2": {
            "fundamental": parcela_2_fund,
            "medio": parcela_2_medio
        }
    }