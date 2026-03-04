"""
Script para limpar cálculos duplicados na tabela calculos_profin.
Mantém apenas o cálculo mais recente para cada escola_id.
"""
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar todos os modelos para garantir que os relacionamentos sejam configurados
from src.modules.api import (
    AnoLetivo,
    Upload,
    ContextoAtivo,
    Escola,
    CalculosProfin,
    ParcelasProfin,
    LiberacoesParcela,
    LiberacoesProjeto,
    ComplementoUpload,
    ComplementoEscola
)

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from src.core.database import get_db_session
from src.core.logging_config import logger


def limpar_calculos_duplicados(ano_letivo_id: int = None, dry_run: bool = False):
    """
    Limpa cálculos duplicados na tabela calculos_profin.
    Mantém apenas o cálculo mais recente para cada escola_id.
    
    Args:
        ano_letivo_id: ID do ano letivo. Se None, limpa todos os anos letivos.
        dry_run: Se True, apenas mostra o que seria deletado sem deletar.
    """
    with get_db_session() as db:
        logger.info(f"\n{'='*60}")
        logger.info(f"SCRIPT DE LIMPEZA DE CÁLCULOS DUPLICADOS")
        logger.info(f"{'='*60}")
        
        if dry_run:
            logger.info("MODO DRY-RUN: Nenhuma alteracao sera feita no banco\n")
        else:
            logger.info("Este script irá:\n  - Identificar cálculos duplicados por escola_id\n  - Manter apenas o cálculo mais recente\n  - Deletar cálculos duplicados e suas parcelas\n")
        
        logger.info(f"{'='*60}\n")
        
        try:
            # 1. Identificar duplicatas
            logger.info("1. IDENTIFICANDO CÁLCULOS DUPLICADOS")
            logger.info("-" * 60)
            
            query_duplicatas = text("""
                SELECT 
                    escola_id,
                    COUNT(*) AS quantidade,
                    ARRAY_AGG(id ORDER BY calculated_at DESC) AS calculo_ids,
                    ARRAY_AGG(calculated_at ORDER BY calculated_at DESC) AS datas_calculo
                FROM calculos_profin
                GROUP BY escola_id
                HAVING COUNT(*) > 1
                ORDER BY quantidade DESC;
            """)
            
            duplicatas = db.execute(query_duplicatas).fetchall()
            
            if not duplicatas:
                logger.info("OK: Nenhuma duplicata encontrada. Nada a fazer.")
                return
            
            logger.info(f"Encontradas {len(duplicatas)} escola(s) com múltiplos cálculos.\n")
            
            # 2. Preparar lista de cálculos para deletar
            calculos_para_deletar = []
            total_parcelas_para_deletar = 0
            
            for escola_id, quantidade, calculo_ids, datas_calculo in duplicatas:
                # Manter o primeiro (mais recente), deletar os demais
                calculo_ids_list = list(calculo_ids)
                calculo_manter = calculo_ids_list[0]
                calculos_deletar = calculo_ids_list[1:]
                
                # Buscar nome da escola
                escola = db.query(Escola).filter(Escola.id == escola_id).first()
                nome_escola = escola.nome_uex if escola else "N/A"
                
                logger.info(f"Escola ID {escola_id} ({nome_escola}):")
                logger.info(f"  - Manter cálculo ID {calculo_manter} (mais recente)")
                logger.info(f"  - Deletar cálculos IDs: {calculos_deletar}")
                
                # Contar parcelas dos cálculos que serão deletados
                for calc_id in calculos_deletar:
                    parcelas_count = db.query(ParcelasProfin).filter(
                        ParcelasProfin.calculo_id == calc_id
                    ).count()
                    total_parcelas_para_deletar += parcelas_count
                    logger.info(f"    Cálculo {calc_id}: {parcelas_count} parcela(s) associada(s)")
                    
                    calculos_para_deletar.append({
                        'id': calc_id,
                        'escola_id': escola_id,
                        'parcelas_count': parcelas_count
                    })
                
                logger.info("")
            
            logger.info(f"Total de cálculos a deletar: {len(calculos_para_deletar)}")
            logger.info(f"Total de parcelas a deletar: {total_parcelas_para_deletar}")
            logger.info("")
            
            if dry_run:
                logger.info("DRY-RUN: Nenhuma alteracao foi feita.")
                return
            
            # 3. Confirmar antes de deletar
            logger.info("2. DELETANDO CÁLCULOS DUPLICADOS")
            logger.info("-" * 60)
            
            calculos_deletados = 0
            parcelas_deletadas = 0
            
            for calc_info in calculos_para_deletar:
                calc_id = calc_info['id']
                escola_id = calc_info['escola_id']
                parcelas_count = calc_info['parcelas_count']
                
                try:
                    # Deletar parcelas primeiro (cascade também faria isso, mas sendo explícito)
                    if parcelas_count > 0:
                        db.query(ParcelasProfin).filter(
                            ParcelasProfin.calculo_id == calc_id
                        ).delete(synchronize_session=False)
                        parcelas_deletadas += parcelas_count
                    
                    # Deletar cálculo
                    calculo = db.query(CalculosProfin).filter(
                        CalculosProfin.id == calc_id
                    ).first()
                    
                    if calculo:
                        db.delete(calculo)
                        calculos_deletados += 1
                        logger.info(f"OK: Deletado calculo ID {calc_id} (escola {escola_id})")
                    
                except Exception as e:
                    logger.error(f"ERRO: Erro ao deletar calculo ID {calc_id}: {e}")
                    db.rollback()
                    raise
            
            # Commit das alterações
            db.commit()
            
            logger.info("")
            logger.info(f"{'='*60}")
            logger.info(f"LIMPEZA CONCLUÍDA")
            logger.info(f"{'='*60}")
            logger.info(f"Cálculos deletados: {calculos_deletados}")
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.exception("Erro ao limpar cálculos duplicados")
            db.rollback()
            raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Limpar cálculos duplicados em calculos_profin")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas mostrar o que seria deletado sem deletar"
    )
    parser.add_argument(
        "--ano-letivo-id",
        type=int,
        help="ID do ano letivo (não usado ainda, mas mantido para compatibilidade)"
    )
    
    args = parser.parse_args()
    
    try:
        limpar_calculos_duplicados(
            ano_letivo_id=args.ano_letivo_id,
            dry_run=args.dry_run
        )
    except Exception as e:
        logger.exception("Erro ao executar limpeza")
        sys.exit(1)
