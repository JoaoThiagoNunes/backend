"""
Script para listar todos os cálculos e identificar possíveis duplicatas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.api import *
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.database import get_db_session
from src.core.logging_config import logger


def listar_todos_calculos():
    """
    Lista todos os cálculos para identificar duplicatas.
    """
    with get_db_session() as db:
        logger.info(f"\n{'='*60}")
        logger.info(f"LISTAGEM DE TODOS OS CALCULOS")
        logger.info(f"{'='*60}\n")
        
        try:
            # Listar todos os cálculos ordenados por escola_id
            query = text("""
                SELECT 
                    c.id AS calculo_id,
                    c.escola_id,
                    e.nome_uex,
                    e.dre,
                    e.upload_id,
                    u.filename AS upload_filename,
                    c.calculated_at,
                    c.valor_total
                FROM calculos_profin c
                JOIN escolas e ON c.escola_id = e.id
                LEFT JOIN uploads u ON e.upload_id = u.id
                ORDER BY c.escola_id, c.calculated_at DESC
            """)
            
            calculos = db.execute(query).fetchall()
            
            logger.info(f"Total de calculos: {len(calculos)}\n")
            
            # Agrupar por escola_id para identificar duplicatas
            escolas_calculos = {}
            for calc_id, escola_id, nome_uex, dre, upload_id, upload_filename, calculated_at, valor_total in calculos:
                if escola_id not in escolas_calculos:
                    escolas_calculos[escola_id] = []
                escolas_calculos[escola_id].append({
                    'calculo_id': calc_id,
                    'nome_uex': nome_uex,
                    'dre': dre,
                    'upload_id': upload_id,
                    'upload_filename': upload_filename,
                    'calculated_at': calculated_at,
                    'valor_total': valor_total
                })
            
            # Mostrar escolas com múltiplos cálculos
            duplicatas_encontradas = False
            for escola_id, calculos_list in escolas_calculos.items():
                if len(calculos_list) > 1:
                    duplicatas_encontradas = True
                    logger.warning(f"\nESCOLA ID {escola_id} - {calculos_list[0]['nome_uex']} ({calculos_list[0]['dre']})")
                    logger.warning(f"  Tem {len(calculos_list)} calculo(s):")
                    for i, calc in enumerate(calculos_list, 1):
                        logger.warning(f"    {i}. Calculo ID {calc['calculo_id']}")
                        logger.warning(f"       Upload: {calc['upload_id']} ({calc['upload_filename']})")
                        logger.warning(f"       Data: {calc['calculated_at']}")
                        logger.warning(f"       Valor: R$ {calc['valor_total']}")
            
            if not duplicatas_encontradas:
                logger.info("OK: Nenhuma duplicata encontrada!")
                logger.info("\nMostrando primeiros 20 calculos:")
                for i, calc in enumerate(calculos[:20], 1):
                    calc_id, escola_id, nome_uex, dre, upload_id, upload_filename, calculated_at, valor_total = calc
                    logger.info(f"{i}. Calculo ID {calc_id}: Escola {escola_id} ({nome_uex[:50]}...), Upload {upload_id}, Valor R$ {valor_total}")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"LISTAGEM CONCLUIDA")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.exception("Erro ao listar calculos")
            raise


if __name__ == "__main__":
    try:
        listar_todos_calculos()
    except Exception as e:
        logger.exception("Erro ao executar listagem")
        sys.exit(1)
