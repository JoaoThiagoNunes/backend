from typing import Dict, Any
import pandas as pd
from src.modules.features.escolas import Escola
from src.modules.features.complemento.models import StatusComplemento
from src.modules.shared.constants import (
    PESO_FUNDAMENTAL_INICIAL,
    PESO_FUNDAMENTAL_FINAL,
    PESO_FUNDAMENTAL_INTEGRAL,
    PESO_PROFISSIONALIZANTE,
    PESO_PROFISSIONALIZANTE_INTEGRADO,
    PESO_ALTERNANCIA,
    PESO_MEDIO_INTEGRAL,
    PESO_MEDIO_REGULAR,
    PESO_ESPECIAL_FUNDAMENTAL_REGULAR,
    PESO_ESPECIAL_FUNDAMENTAL_INTEGRAL,
    PESO_ESPECIAL_MEDIO_PARCIAL,
    PESO_ESPECIAL_MEDIO_INTEGRAL,
    MULTIPLICADOR_ALTERNANCIA,
    MULTIPLICADOR_ESPECIAL,
    MULTIPLICADOR_GESTAO,
    VALOR_PER_CAPITA_MERENDA,
    MULTIPLICADOR_MERENDA_INTEGRAL,
    MULTIPLICADOR_MERENDA_ALTERNANCIA,
    VALOR_UNITARIO_KIT_ESCOLAR,
    VALOR_UNITARIO_UNIFORME,
    VALOR_UNITARIO_SALA_RECURSO,
)


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
    
    # Determinar status baseado no saldo líquido (total_alunos_diferenca)
    # Se o saldo total for negativo, é DIMINUICAO (não recebe complemento)
    total_alunos_diferenca = diferencas.get('total_alunos', 0)
    
    if total_alunos_diferenca < 0:
        # Se o total diminuiu, é DIMINUICAO (não recebe valores)
        status = StatusComplemento.DIMINUICAO
    elif total_alunos_diferenca > 0:
        # Se o total aumentou, é AUMENTO (recebe valores)
        status = StatusComplemento.AUMENTO
    elif tem_aumento and not tem_diminuicao:
        # Se há apenas aumentos em modalidades específicas (mesmo que total seja 0)
        status = StatusComplemento.AUMENTO
    elif tem_diminuicao and not tem_aumento:
        # Se há apenas diminuições em modalidades específicas (mesmo que total seja 0)
        status = StatusComplemento.DIMINUICAO
    else:
        # Sem mudanças
        status = StatusComplemento.SEM_MUDANCA
    
    return {
        'status': status,
        'diferencas': diferencas,
        'quantidades_antes': campos_antes,
        'quantidades_depois': campos_depois
    }


def calcular_complemento_gestao(diferencas: Dict[str, int]) -> float:
    # Usar diferenças diretamente (incluindo negativas) conforme código de teste
    fund_inicial = diferencas.get('fundamental_inicial', 0)
    fund_final = diferencas.get('fundamental_final', 0)
    fund_integral = diferencas.get('fundamental_integral', 0)
    profissionalizante = diferencas.get('profissionalizante', 0)
    profissionalizante_integrado = diferencas.get('profissionalizante_integrado', 0)
    alternancia = diferencas.get('alternancia', 0)
    ensino_medio_integral = diferencas.get('ensino_medio_integral', 0)
    ensino_medio_regular = diferencas.get('ensino_medio_regular', 0)
    especial_fund_regular = diferencas.get('especial_fund_regular', 0)
    especial_fund_integral = diferencas.get('especial_fund_integral', 0)
    especial_medio_parcial = diferencas.get('especial_medio_parcial', 0)
    especial_medio_integral = diferencas.get('especial_medio_integral', 0)
    
    # Calcular cada modalidade individualmente seguindo a fórmula exata do código de teste
    valor_gestao = (
        (fund_inicial * PESO_FUNDAMENTAL_INICIAL) * MULTIPLICADOR_GESTAO +
        (fund_final * PESO_FUNDAMENTAL_FINAL) * MULTIPLICADOR_GESTAO +
        (fund_integral * PESO_FUNDAMENTAL_INTEGRAL) * MULTIPLICADOR_GESTAO +
        (profissionalizante * PESO_PROFISSIONALIZANTE) * MULTIPLICADOR_GESTAO +
        (profissionalizante_integrado * PESO_PROFISSIONALIZANTE_INTEGRADO) * MULTIPLICADOR_GESTAO +
        ((alternancia * PESO_ALTERNANCIA) * MULTIPLICADOR_ALTERNANCIA) * MULTIPLICADOR_GESTAO +
        (ensino_medio_integral * PESO_MEDIO_INTEGRAL) * MULTIPLICADOR_GESTAO +
        (ensino_medio_regular * PESO_MEDIO_REGULAR) * MULTIPLICADOR_GESTAO +
        ((especial_fund_regular * PESO_ESPECIAL_FUNDAMENTAL_REGULAR) * MULTIPLICADOR_ESPECIAL) * MULTIPLICADOR_GESTAO +
        ((especial_fund_integral * PESO_ESPECIAL_FUNDAMENTAL_INTEGRAL) * MULTIPLICADOR_ESPECIAL) * MULTIPLICADOR_GESTAO +
        ((especial_medio_parcial * PESO_ESPECIAL_MEDIO_PARCIAL) * MULTIPLICADOR_ESPECIAL) * MULTIPLICADOR_GESTAO +
        ((especial_medio_integral * PESO_ESPECIAL_MEDIO_INTEGRAL) * MULTIPLICADOR_ESPECIAL) * MULTIPLICADOR_GESTAO
    )
    
    return round(valor_gestao, 2)


def calcular_complemento_merenda(diferencas: Dict[str, int]) -> float:
    # Usar diferenças diretamente (incluindo negativas) conforme código de teste
    fund_inicial = diferencas.get('fundamental_inicial', 0)
    fund_final = diferencas.get('fundamental_final', 0)
    profissionalizante = diferencas.get('profissionalizante', 0)
    ensino_medio_regular = diferencas.get('ensino_medio_regular', 0)
    fund_integral = diferencas.get('fundamental_integral', 0)
    ensino_medio_integral = diferencas.get('ensino_medio_integral', 0)
    especial_fund_integral = diferencas.get('especial_fund_integral', 0)
    especial_medio_integral = diferencas.get('especial_medio_integral', 0)
    profissionalizante_integrado = diferencas.get('profissionalizante_integrado', 0)
    especial_fund_regular = diferencas.get('especial_fund_regular', 0)
    especial_medio_parcial = diferencas.get('especial_medio_parcial', 0)
    alternancia = diferencas.get('alternancia', 0)
    
    # Calcular cada modalidade individualmente seguindo a fórmula exata do código de teste
    valor_merenda = (
        fund_inicial * VALOR_PER_CAPITA_MERENDA +
        fund_final * VALOR_PER_CAPITA_MERENDA +
        profissionalizante * VALOR_PER_CAPITA_MERENDA +
        ensino_medio_regular * VALOR_PER_CAPITA_MERENDA +
        (fund_integral * MULTIPLICADOR_MERENDA_INTEGRAL) * VALOR_PER_CAPITA_MERENDA +
        (ensino_medio_integral * MULTIPLICADOR_MERENDA_INTEGRAL) * VALOR_PER_CAPITA_MERENDA +
        (especial_fund_integral * MULTIPLICADOR_MERENDA_INTEGRAL) * VALOR_PER_CAPITA_MERENDA +
        (especial_medio_integral * MULTIPLICADOR_MERENDA_INTEGRAL) * VALOR_PER_CAPITA_MERENDA +
        (profissionalizante_integrado * MULTIPLICADOR_MERENDA_INTEGRAL) * VALOR_PER_CAPITA_MERENDA +
        (especial_fund_regular * MULTIPLICADOR_MERENDA_INTEGRAL) * VALOR_PER_CAPITA_MERENDA +
        (especial_medio_parcial * MULTIPLICADOR_MERENDA_INTEGRAL) * VALOR_PER_CAPITA_MERENDA +
        alternancia * (VALOR_PER_CAPITA_MERENDA * MULTIPLICADOR_MERENDA_ALTERNANCIA)
    )
    
    return round(valor_merenda, 2)


def calcular_complemento_valores(diferencas: Dict[str, int]) -> Dict[str, float]:
    # Calcular gestão e merenda usando as funções específicas de complemento
    profin_gestao = calcular_complemento_gestao(diferencas)
    profin_merenda = calcular_complemento_merenda(diferencas)
    
    # Calcular total_alunos_diferenca (soma de todas as diferenças, conforme código de teste)
    # Excluir total_alunos da soma pois ele é calculado separadamente
    total_alunos_diferenca = sum([
        diferencas.get('fundamental_inicial', 0),
        diferencas.get('fundamental_final', 0),
        diferencas.get('fundamental_integral', 0),
        diferencas.get('profissionalizante', 0),
        diferencas.get('profissionalizante_integrado', 0),
        diferencas.get('alternancia', 0),
        diferencas.get('ensino_medio_integral', 0),
        diferencas.get('ensino_medio_regular', 0),
        diferencas.get('especial_fund_regular', 0),
        diferencas.get('especial_fund_integral', 0),
        diferencas.get('especial_medio_parcial', 0),
        diferencas.get('especial_medio_integral', 0),
    ])
    
    # Calcular kit e uniforme usando total_alunos_diferenca (conforme código de teste)
    profin_kit_escolar = round(total_alunos_diferenca * VALOR_UNITARIO_KIT_ESCOLAR, 2)
    profin_uniforme = round(total_alunos_diferenca * VALOR_UNITARIO_UNIFORME, 2)
    
    # Calcular sala de recurso: diferença * 180
    sala_recurso_diferenca = diferencas.get('sala_recurso', 0)
    profin_sala_recurso = round(sala_recurso_diferenca * VALOR_UNITARIO_SALA_RECURSO, 2)
    
    # Calcular valor total (gestão + merenda + kit + uniforme + sala_recurso para complemento)
    valor_total = profin_gestao + profin_merenda + profin_kit_escolar + profin_uniforme + profin_sala_recurso
    
    return {
        "profin_gestao": profin_gestao,
        "profin_projeto": 0.0,  # Não utilizado no complemento
        "profin_kit_escolar": profin_kit_escolar,
        "profin_uniforme": profin_uniforme,
        "profin_merenda": profin_merenda,
        "profin_sala_recurso": profin_sala_recurso,
        "profin_preuni": 0.0,  # Não utilizado no complemento
        "valor_total": round(valor_total, 2)
    }


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
