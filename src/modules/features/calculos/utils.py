import pandas as pd
from typing import Dict, Any
from src.modules.shared.utils import obter_quantidade, validar_indigena_e_quilombola
from src.modules.shared.constants import (
    PESO_FUNDAMENTAL_INICIAL,
    PESO_FUNDAMENTAL_FINAL,
    PESO_FUNDAMENTAL_INTEGRAL,
    PESO_PROFISSIONALIZANTE,
    PESO_PROFISSIONALIZANTE_INTEGRADO,
    PESO_ESPECIAL_PROFISSIONALIZANTE_PARCIAL,
    PESO_ESPECIAL_PROFISSIONALIZANTE_INTEGRADO,
    PESO_ALTERNANCIA,
    PESO_MEDIO_INTEGRAL,
    PESO_MEDIO_REGULAR,
    PESO_ESPECIAL_FUNDAMENTAL_REGULAR,
    PESO_ESPECIAL_FUNDAMENTAL_INTEGRAL,
    PESO_ESPECIAL_MEDIO_PARCIAL,
    PESO_ESPECIAL_MEDIO_INTEGRAL,
    MULTIPLICADOR_ALTERNANCIA,
    MULTIPLICADOR_ESPECIAL,
    VALOR_FIXO_GESTAO,
    MULTIPLICADOR_GESTAO,
    BONUS_REPASSE_POR_AREA_VALORES,
    LIMITE_ALUNOS_PROJETO_1,
    LIMITE_ALUNOS_PROJETO_2,
    MULTIPLICADOR_PROJETO_INTEGRAL,
    NUM_PROJETOS_ATE_500,
    NUM_PROJETOS_ATE_1000,
    NUM_PROJETOS_ACIMA_1000,
    VALOR_UNITARIO_KIT_ESCOLAR,
    VALOR_UNITARIO_UNIFORME,
    VALOR_PER_CAPITA_MERENDA,
    MULTIPLICADOR_MERENDA_INTEGRAL,
    MULTIPLICADOR_MERENDA_ALTERNANCIA,
    MULTIPLICADOR_INDIGENA_QUILOMBOLA,
    VALOR_FIXO_SALA_RECURSO,
    VALOR_UNITARIO_SALA_RECURSO,
    # VALOR_UNITARIO_CLIMATIZACAO, # Desativado temporariamente
    VALOR_UNITARIO_PREUNI,
    # VALOR_UNITARIO_PERMANENTE, # Desativado temporariamente
)


def calcular_profin_gestao(row: pd.Series, incluir_valor_fixo_gestao: bool = True) -> float:
    fund_inicial = obter_quantidade(row, "FUNDAMENTAL INICIAL")
    fund_final = obter_quantidade(row, "FUNDAMENTAL FINAL")
    fund_integral = obter_quantidade(row, "FUNDAMENTAL INTEGRAL")
    profissionalizante = obter_quantidade(row, "PROFISSIONALIZANTE")
    profissionalizante_integrado = obter_quantidade(row, "PROFISSIONALIZANTE INTEGRADO")
    especial_profissionalizante_parcial = obter_quantidade(row, "ESPECIAL PROFISSIONALIZANTE PARCIAL")
    especial_profissionalizante_integrado = obter_quantidade(row, "ESPECIAL PROFISSIONALIZANTE INTEGRADO")
    alternancia = obter_quantidade(row, "ALTERNÂNCIA")
    medio_integral = obter_quantidade(row, "ENSINO MÉDIO INTEGRAL")
    medio_regular = obter_quantidade(row, "ENSINO MÉDIO REGULAR")
    esp_fund_regular = obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR")
    esp_fund_integral = obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL")
    esp_medio_parcial = obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL")
    esp_medio_integral = obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL")
    repasse_por_area = obter_quantidade(row, "REPASSE POR AREA")
    
    valor_variavel = (
        (fund_inicial * PESO_FUNDAMENTAL_INICIAL) +
        (fund_final * PESO_FUNDAMENTAL_FINAL) +
        (fund_integral * PESO_FUNDAMENTAL_INTEGRAL) +
        (profissionalizante * PESO_PROFISSIONALIZANTE) +
        (profissionalizante_integrado * PESO_PROFISSIONALIZANTE_INTEGRADO) +
        ((especial_profissionalizante_parcial * PESO_ESPECIAL_PROFISSIONALIZANTE_PARCIAL) * MULTIPLICADOR_ESPECIAL) +
        ((especial_profissionalizante_integrado * PESO_ESPECIAL_PROFISSIONALIZANTE_INTEGRADO) * MULTIPLICADOR_ESPECIAL) +
        ((alternancia * PESO_ALTERNANCIA) * MULTIPLICADOR_ALTERNANCIA) +
        (medio_integral * PESO_MEDIO_INTEGRAL) +
        (medio_regular * PESO_MEDIO_REGULAR) +
        ((esp_fund_regular * PESO_ESPECIAL_FUNDAMENTAL_REGULAR) * MULTIPLICADOR_ESPECIAL) +
        ((esp_fund_integral * PESO_ESPECIAL_FUNDAMENTAL_INTEGRAL) * MULTIPLICADOR_ESPECIAL) +
        ((esp_medio_parcial * PESO_ESPECIAL_MEDIO_PARCIAL) * MULTIPLICADOR_ESPECIAL) +
        ((esp_medio_integral * PESO_ESPECIAL_MEDIO_INTEGRAL) * MULTIPLICADOR_ESPECIAL) 
    ) * MULTIPLICADOR_GESTAO
 
    if not incluir_valor_fixo_gestao:
        return round(valor_variavel, 2)
    
    bonus = 0
    if repasse_por_area in BONUS_REPASSE_POR_AREA_VALORES:
        bonus = repasse_por_area

    valor_total = VALOR_FIXO_GESTAO + valor_variavel + bonus
    return round(valor_total, 2)


def calcular_profin_projeto(row: pd.Series) -> float:
    fund_integral = obter_quantidade(row, "FUNDAMENTAL INTEGRAL")
    medio_integral = obter_quantidade(row, "ENSINO MÉDIO INTEGRAL")
    esp_fund_integral = obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL")
    esp_medio_integral = obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL")
    quantidade_aluno = obter_quantidade(row, "TOTAL")

    # Verificar se tem ensino integral
    tem_integral = (
        fund_integral > 0 or 
        medio_integral > 0 or 
        esp_fund_integral > 0 or 
        esp_medio_integral > 0
    )

    if quantidade_aluno <= LIMITE_ALUNOS_PROJETO_1:
        qt_projeto = NUM_PROJETOS_ATE_500 * (MULTIPLICADOR_PROJETO_INTEGRAL if tem_integral else 1)
    elif quantidade_aluno <= LIMITE_ALUNOS_PROJETO_2:
        qt_projeto = NUM_PROJETOS_ATE_1000 * (MULTIPLICADOR_PROJETO_INTEGRAL if tem_integral else 1)
    else:
        qt_projeto = NUM_PROJETOS_ACIMA_1000 * (MULTIPLICADOR_PROJETO_INTEGRAL if tem_integral else 1)

    return round(qt_projeto, 2)

def calcular_profin_kit_escolar(row: pd.Series) -> float:
    quantidade_aluno = obter_quantidade(row, "TOTAL")
    return round(quantidade_aluno * VALOR_UNITARIO_KIT_ESCOLAR, 2)

def calcular_profin_uniforme(row: pd.Series) -> float:
    quantidade_aluno = obter_quantidade(row, "TOTAL")
    return round(quantidade_aluno * VALOR_UNITARIO_UNIFORME, 2)

def calcular_profin_merenda(row: pd.Series) -> float:
    valor_per_capita = VALOR_PER_CAPITA_MERENDA

    fund_inicial = obter_quantidade(row, "FUNDAMENTAL INICIAL")
    fund_final = obter_quantidade(row, "FUNDAMENTAL FINAL")
    profissionalizante = obter_quantidade(row, "PROFISSIONALIZANTE")
    profissionalizante_integrado = obter_quantidade(row, "PROFISSIONALIZANTE INTEGRADO")
    medio_regular = obter_quantidade(row, "ENSINO MÉDIO REGULAR")
    fund_integral = obter_quantidade(row, "FUNDAMENTAL INTEGRAL")
    medio_integral = obter_quantidade(row, "ENSINO MÉDIO INTEGRAL")
    esp_fund_integral = obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL")
    esp_medio_integral = obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL")
    esp_fund_regular = obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR")
    esp_medio_parcial = obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL")
    alternancia = obter_quantidade(row, "ALTERNÂNCIA")
    fic_senac = obter_quantidade(row, "FIC SENAC")
    especial_profissionalizante_parcial = obter_quantidade(row, "ESPECIAL PROFISSIONALIZANTE PARCIAL")
    especial_profissionalizante_integrado = obter_quantidade(row, "ESPECIAL PROFISSIONALIZANTE INTEGRADO")

    valor_total = (
        ((fund_inicial + fund_final + profissionalizante + medio_regular + fic_senac) * valor_per_capita) + 
        ((fund_integral + medio_integral + esp_fund_integral + esp_medio_integral + profissionalizante_integrado + esp_fund_regular + esp_medio_parcial + especial_profissionalizante_parcial + especial_profissionalizante_integrado) * MULTIPLICADOR_MERENDA_INTEGRAL * valor_per_capita) +
        (alternancia * (valor_per_capita * MULTIPLICADOR_MERENDA_ALTERNANCIA))
    )

    if (validar_indigena_e_quilombola(row, "INDIGENA & QUILOMBOLA") != "NÃO"):
        return round(valor_total * MULTIPLICADOR_INDIGENA_QUILOMBOLA, 2)

    return round(valor_total, 2)

def calcular_profin_sala_recurso(row: pd.Series) -> float:
    if (obter_quantidade(row, "SALA DE RECURSO") != 0):
        quantidade_aluno = obter_quantidade(row, "SALA DE RECURSO")
        return round(quantidade_aluno * VALOR_UNITARIO_SALA_RECURSO + VALOR_FIXO_SALA_RECURSO, 2)
    return 0.00



#def calcular_profin_climatizacao(row: pd.Series) -> float:
#    qtd_aparelhos = obter_quantidade(row, "CLIMATIZAÇÃO")
#    return round(qtd_aparelhos * VALOR_UNITARIO_CLIMATIZACAO, 2)

def calcular_profin_preuni(row: pd.Series) -> float:
    qtd_alunos_preuni = obter_quantidade(row, "PREUNI")
    return round(qtd_alunos_preuni * VALOR_UNITARIO_PREUNI, 2)

#def calcular_profin_permanente(row: pd.Series) -> float:
#    quantidade_aluno = obter_quantidade(row, "TOTAL")
#    return round(quantidade_aluno * VALOR_UNITARIO_PERMANENTE, 2)

def calcular_todas_cotas(row: pd.Series, incluir_valor_fixo_gestao: bool = True) -> Dict[str, Any]:
    profin_gestao = calcular_profin_gestao(row, incluir_valor_fixo_gestao=incluir_valor_fixo_gestao)
    profin_projeto = calcular_profin_projeto(row)
    profin_kit_escolar = calcular_profin_kit_escolar(row)
    profin_uniforme = calcular_profin_uniforme(row)
    profin_merenda = calcular_profin_merenda(row)
    profin_sala_recurso = calcular_profin_sala_recurso(row)
    # profin_permanente = calcular_profin_permanente(row) # Desativado temporariamente
    # profin_climatizacao = calcular_profin_climatizacao(row) # Desativado temporariamente
    profin_preuni = calcular_profin_preuni(row)
    
    cotas = {
        "profin_gestao": profin_gestao,
        "profin_projeto": profin_projeto,
        "profin_kit_escolar": profin_kit_escolar,
        "profin_uniforme": profin_uniforme,
        "profin_merenda": profin_merenda,
        "profin_sala_recurso": profin_sala_recurso,
        # "profin_permanente": profin_permanente, # Desativado temporariamente
        # "profin_climatizacao": profin_climatizacao, # Desativado temporariamente
        "profin_preuni": profin_preuni,
    }
    
    cotas["valor_total"] = round(sum([
        v for k, v in cotas.items() 
        if k not in ["tem_alternancia", "valor_total"] and isinstance(v, (int, float))
    ]), 2)
    
    return cotas

