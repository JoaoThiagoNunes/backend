from typing import Optional, Tuple, Dict
from src.modules.features.escolas import Escola
from src.modules.shared.constants import (
    PESO_FUNDAMENTAL_INICIAL,
    PESO_FUNDAMENTAL_FINAL,
    PESO_FUNDAMENTAL_INTEGRAL,
    PESO_ESPECIAL_FUNDAMENTAL_REGULAR,
    PESO_ESPECIAL_FUNDAMENTAL_INTEGRAL,
    PESO_PROFISSIONALIZANTE,
    PESO_PROFISSIONALIZANTE_INTEGRADO,
    PESO_ALTERNANCIA,
    PESO_MEDIO_INTEGRAL,
    PESO_MEDIO_REGULAR,
    PESO_ESPECIAL_MEDIO_PARCIAL,
    PESO_ESPECIAL_MEDIO_INTEGRAL,
    PORCENTAGEM_TOTAL,
)

def calcular_porcentagens_ensino(escola: Escola) -> Tuple[float, float]:
    
    valor_fundamental = (
        (escola.fundamental_inicial * PESO_FUNDAMENTAL_INICIAL) +
        (escola.fundamental_final * PESO_FUNDAMENTAL_FINAL) +
        (escola.fundamental_integral * PESO_FUNDAMENTAL_INTEGRAL) +
        (escola.especial_fund_regular * PESO_ESPECIAL_FUNDAMENTAL_REGULAR) +
        (escola.especial_fund_integral * PESO_ESPECIAL_FUNDAMENTAL_INTEGRAL)
    )
    
    valor_medio = (
        (escola.profissionalizante * PESO_PROFISSIONALIZANTE) +
        (escola.profissionalizante_integrado * PESO_PROFISSIONALIZANTE_INTEGRADO) +
        (escola.alternancia * PESO_ALTERNANCIA) +
        (escola.ensino_medio_integral * PESO_MEDIO_INTEGRAL) +
        (escola.ensino_medio_regular * PESO_MEDIO_REGULAR) +
        (escola.especial_medio_parcial * PESO_ESPECIAL_MEDIO_PARCIAL) +
        (escola.especial_medio_integral * PESO_ESPECIAL_MEDIO_INTEGRAL)
    )
    
    denominador = valor_fundamental + valor_medio
    
    if denominador == 0:
        return (0.0, 0.0)
    
    pct_fundamental = (valor_fundamental / denominador) * PORCENTAGEM_TOTAL
    pct_medio = PORCENTAGEM_TOTAL - pct_fundamental
    
    return (round(pct_fundamental, 2), round(pct_medio, 2))


def dividir_em_parcelas(valor_reais: float, saldo_reprogramado: float = 0.0) -> Tuple[int, int]:
    # Converte para centavos 
    valor_centavos = int(valor_reais * 100)

    # Dividir em duas parcelas
    parcela_1 = valor_centavos // 2
    parcela_2 = valor_centavos - parcela_1 

    if saldo_reprogramado > 0:
        saldo_centavos = int(saldo_reprogramado * 100)
        if saldo_centavos <= parcela_1:
            parcela_1 = max(0, parcela_1 - saldo_centavos)
        else:
            saldo_restante = saldo_centavos - parcela_1
            parcela_1 = 0
            parcela_2 = max(0, parcela_2 - saldo_restante)

    return (parcela_1, parcela_2)


def dividir_parcela_por_ensino(
    parcela_centavos: int,
    porcentagem_fundamental: float,
    porcentagem_medio: float
) -> Tuple[int, int]:
    # Calcular valores baseados nas porcentagens
    valor_fundamental = int((parcela_centavos * porcentagem_fundamental) / 100.0)
    valor_medio = int((parcela_centavos * porcentagem_medio) / 100.0)
    
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
    numero_parcelas: int = 2,
    escola: Optional[Escola] = None,
    tipo_cota: Optional[str] = None
) -> Dict[str, Dict[str, int]]:

    # PREUNI sempre vai 100% para o ensino médio, independente da escola ter fundamental
    if tipo_cota == "preuni":
        porcentagem_fundamental = 0.0
        porcentagem_medio = 100.0

    saldo_reprogramado = 0.0
    if escola and tipo_cota:
        if tipo_cota == "gestao" and escola.saldo_reprogramado_gestao:
            saldo_reprogramado = escola.saldo_reprogramado_gestao
        elif tipo_cota == "merenda" and escola.saldo_reprogramado_merenda:
            saldo_reprogramado = escola.saldo_reprogramado_merenda
    
    #KIT ESCOLAR E UNIFORME 
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
        parcela_1_centavos, parcela_2_centavos = dividir_em_parcelas(valor_cota_reais, saldo_reprogramado)
        
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
