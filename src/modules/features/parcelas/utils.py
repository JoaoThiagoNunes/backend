from typing import Tuple, Dict
from src.modules.features.escolas import Escola

def calcular_porcentagens_ensino(escola: Escola) -> Tuple[float, float]:
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
    porcentagem_medio: float,
    numero_parcelas: int = 2
) -> Dict[str, Dict[str, int]]:
    if numero_parcelas == 1:
        # Apenas 1 parcela - usar o valor total
        valor_centavos = int(round(valor_cota_reais * 100))
        
        # Dividir a parcela única por ensino
        parcela_1_fund, parcela_1_medio = dividir_parcela_por_ensino(
            valor_centavos, porcentagem_fundamental, porcentagem_medio
        )
        
        return {
            "parcela_1": {
                "fundamental": parcela_1_fund,
                "medio": parcela_1_medio
            }
        }
    else:
        # Dividir em 2 parcelas (comportamento original)
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

