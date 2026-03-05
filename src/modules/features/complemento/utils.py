from typing import Dict, Any
import pandas as pd
from src.modules.features.escolas import Escola
from src.modules.features.complemento.models import StatusComplemento
from src.modules.features.calculos.utils import calcular_todas_cotas


def comparar_quantidades(escola_base: Escola, dados_complemento: Dict[str, Any]) -> Dict[str, Any]:
    # Mapear campos do modelo Escola para nomes das colunas da planilha
    campos_antes = {
        'total_alunos': escola_base.total_alunos or 0,
        'fundamental_inicial': escola_base.fundamental_inicial or 0,
        'fundamental_final': escola_base.fundamental_final or 0,
        'fundamental_integral': escola_base.fundamental_integral or 0,
        'profissionalizante': escola_base.profissionalizante or 0,
        'profissionalizante_integrado': escola_base.profissionalizante_integrado or 0,
        'alternancia': escola_base.alternancia or 0,
        'ensino_medio_integral': escola_base.ensino_medio_integral or 0,
        'ensino_medio_regular': escola_base.ensino_medio_regular or 0,
        'especial_fund_regular': escola_base.especial_fund_regular or 0,
        'especial_fund_integral': escola_base.especial_fund_integral or 0,
        'especial_medio_parcial': escola_base.especial_medio_parcial or 0,
        'especial_medio_integral': escola_base.especial_medio_integral or 0,
        'sala_recurso': escola_base.sala_recurso or 0,
        'preuni': escola_base.preuni or 0,
    }
    
    # Mapear dados do complemento (vindos da planilha)
    campos_depois = {
        'total_alunos': dados_complemento.get('TOTAL', 0),
        'fundamental_inicial': dados_complemento.get('FUNDAMENTAL INICIAL', 0),
        'fundamental_final': dados_complemento.get('FUNDAMENTAL FINAL', 0),
        'fundamental_integral': dados_complemento.get('FUNDAMENTAL INTEGRAL', 0),
        'profissionalizante': dados_complemento.get('PROFISSIONALIZANTE', 0),
        'profissionalizante_integrado': dados_complemento.get('PROFISSIONALIZANTE INTEGRADO', 0),
        'alternancia': dados_complemento.get('ALTERNÂNCIA', 0),
        'ensino_medio_integral': dados_complemento.get('ENSINO MÉDIO INTEGRAL', 0),
        'ensino_medio_regular': dados_complemento.get('ENSINO MÉDIO REGULAR', 0),
        'especial_fund_regular': dados_complemento.get('ESPECIAL FUNDAMENTAL REGULAR', 0),
        'especial_fund_integral': dados_complemento.get('ESPECIAL FUNDAMENTAL INTEGRAL', 0),
        'especial_medio_parcial': dados_complemento.get('ESPECIAL MÉDIO PARCIAL', 0),
        'especial_medio_integral': dados_complemento.get('ESPECIAL MÉDIO INTEGRAL', 0),
        'sala_recurso': dados_complemento.get('SALA DE RECURSO', 0),
        'preuni': dados_complemento.get('PREUNI', 0),
    }
    
    # Calcular diferenças
    diferencas = {}
    tem_aumento = False
    tem_diminuicao = False
    
    for campo in campos_antes.keys():
        antes = campos_antes[campo]
        depois = campos_depois[campo]
        diferenca = depois - antes
        diferencas[campo] = diferenca
        
        if diferenca > 0:
            tem_aumento = True
        elif diferenca < 0:
            tem_diminuicao = True
    
    # Determinar status
    if tem_aumento:
        status = StatusComplemento.AUMENTO
    elif tem_diminuicao:
        status = StatusComplemento.DIMINUICAO
    else:
        status = StatusComplemento.SEM_MUDANCA
    
    return {
        'status': status,
        'diferencas': diferencas,
        'quantidades_antes': campos_antes,
        'quantidades_depois': campos_depois
    }


def calcular_complemento_valores(diferencas: Dict[str, int]) -> Dict[str, float]:
    # Criar Series do pandas apenas com diferenças positivas
    # Mapear nomes de campos do modelo para nomes de colunas da planilha
    row_diferenca = pd.Series({
        'TOTAL': max(0, diferencas.get('total_alunos', 0)),
        'FUNDAMENTAL INICIAL': max(0, diferencas.get('fundamental_inicial', 0)),
        'FUNDAMENTAL FINAL': max(0, diferencas.get('fundamental_final', 0)),
        'FUNDAMENTAL INTEGRAL': max(0, diferencas.get('fundamental_integral', 0)),
        'PROFISSIONALIZANTE': max(0, diferencas.get('profissionalizante', 0)),
        'PROFISSIONALIZANTE INTEGRADO': max(0, diferencas.get('profissionalizante_integrado', 0)),
        'ALTERNÂNCIA': max(0, diferencas.get('alternancia', 0)),
        'ENSINO MÉDIO INTEGRAL': max(0, diferencas.get('ensino_medio_integral', 0)),
        'ENSINO MÉDIO REGULAR': max(0, diferencas.get('ensino_medio_regular', 0)),
        'ESPECIAL FUNDAMENTAL REGULAR': max(0, diferencas.get('especial_fund_regular', 0)),
        'ESPECIAL FUNDAMENTAL INTEGRAL': max(0, diferencas.get('especial_fund_integral', 0)),
        'ESPECIAL MÉDIO PARCIAL': max(0, diferencas.get('especial_medio_parcial', 0)),
        'ESPECIAL MÉDIO INTEGRAL': max(0, diferencas.get('especial_medio_integral', 0)),
        'SALA DE RECURSO': max(0, diferencas.get('sala_recurso', 0)),
        'PREUNI': max(0, diferencas.get('preuni', 0)),
        # Campos adicionais necessários para cálculos
        'PROJETOS': 0,  # Não consideramos projetos no complemento
        'INDIGENA & QUILOMBOLA': 'NÃO',  # Não consideramos no complemento
        'REPASSE POR AREA': 0,  # Não consideramos no complemento
        'EPT': None,
        'INEP': None,
    })
    
    # Usar função existente de cálculo
    # Para complemento, não incluímos o valor fixo de gestão (R$ 2000,00)
    cotas = calcular_todas_cotas(row_diferenca, incluir_valor_fixo_gestao=False)
    
    return cotas


def criar_row_diferenca(diferencas: Dict[str, int]) -> pd.Series:
    return pd.Series({
        'TOTAL': max(0, diferencas.get('total_alunos', 0)),
        'FUNDAMENTAL INICIAL': max(0, diferencas.get('fundamental_inicial', 0)),
        'FUNDAMENTAL FINAL': max(0, diferencas.get('fundamental_final', 0)),
        'FUNDAMENTAL INTEGRAL': max(0, diferencas.get('fundamental_integral', 0)),
        'PROFISSIONALIZANTE': max(0, diferencas.get('profissionalizante', 0)),
        'PROFISSIONALIZANTE INTEGRADO': max(0, diferencas.get('profissionalizante_integrado', 0)),
        'ALTERNÂNCIA': max(0, diferencas.get('alternancia', 0)),
        'ENSINO MÉDIO INTEGRAL': max(0, diferencas.get('ensino_medio_integral', 0)),
        'ENSINO MÉDIO REGULAR': max(0, diferencas.get('ensino_medio_regular', 0)),
        'ESPECIAL FUNDAMENTAL REGULAR': max(0, diferencas.get('especial_fund_regular', 0)),
        'ESPECIAL FUNDAMENTAL INTEGRAL': max(0, diferencas.get('especial_fund_integral', 0)),
        'ESPECIAL MÉDIO PARCIAL': max(0, diferencas.get('especial_medio_parcial', 0)),
        'ESPECIAL MÉDIO INTEGRAL': max(0, diferencas.get('especial_medio_integral', 0)),
        'SALA DE RECURSO': max(0, diferencas.get('sala_recurso', 0)),
        'PREUNI': max(0, diferencas.get('preuni', 0)),
        'PROJETOS': 0,
        'INDIGENA & QUILOMBOLA': 'NÃO',
        'REPASSE POR AREA': 0,
        'EPT': None,
        'INEP': None,
    })
