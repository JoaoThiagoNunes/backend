from src.modules.features.escolas.models import Escola


def escola_esta_liberada(escola: Escola) -> bool:
    """
    Deriva estado de liberação das tabelas de liberações.
    
    Uma escola está liberada se:
    - Tem pelo menos uma parcela liberada (liberacoes_parcelas com liberada=True), OU
    - Tem projeto liberado (liberacoes_projetos.liberada=True)
    
    Args:
        escola: Instância da escola
        
    Returns:
        bool: True se a escola está liberada, False caso contrário
    """
    # Verifica liberações de parcelas
    tem_parcela_liberada = any(
        lp.liberada for lp in escola.liberacoes_parcelas
    ) if escola.liberacoes_parcelas else False
    
    # Verifica liberação de projetos
    tem_projeto_liberado = (
        escola.liberacoes_projetos is not None and 
        escola.liberacoes_projetos.liberada
    )
    
    return tem_parcela_liberada or tem_projeto_liberado
