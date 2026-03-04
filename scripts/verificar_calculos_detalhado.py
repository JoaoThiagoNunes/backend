"""
Script para verificar cálculos de forma mais detalhada.
Mostra todos os cálculos e suas escolas para identificar possíveis duplicatas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.api import *
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from src.core.database import get_db_session
from src.core.logging_config import logger


def verificar_calculos_detalhado():
    """
    Verifica cálculos de forma detalhada.
    """
    with get_db_session() as db:
        logger.info(f"\n{'='*60}")
        logger.info(f"VERIFICACAO DETALHADA DE CALCULOS")
        logger.info(f"{'='*60}\n")
        
        try:
            # 1. Verificar se há múltiplos cálculos com mesmo escola_id (ignorando constraint)
            logger.info("1. VERIFICANDO CALCULOS POR escola_id")
            logger.info("-" * 60)
            
            query_duplicatas = text("""
                SELECT 
                    escola_id,
                    COUNT(*) AS quantidade,
                    STRING_AGG(id::text, ', ' ORDER BY calculated_at DESC) AS calculo_ids,
                    STRING_AGG(calculated_at::text, ', ' ORDER BY calculated_at DESC) AS datas
                FROM calculos_profin
                GROUP BY escola_id
                HAVING COUNT(*) > 1
                ORDER BY quantidade DESC
                LIMIT 20;
            """)
            
            duplicatas = db.execute(query_duplicatas).fetchall()
            
            if duplicatas:
                logger.warning(f"ENCONTRADAS {len(duplicatas)} DUPLICATAS:")
                for escola_id, quantidade, calculo_ids, datas in duplicatas:
                    logger.warning(f"\n  Escola ID: {escola_id}")
                    logger.warning(f"  Quantidade: {quantidade}")
                    logger.warning(f"  Calculo IDs: {calculo_ids}")
                    logger.warning(f"  Datas: {datas}")
            else:
                logger.info("OK: Nenhuma duplicata encontrada por escola_id")
            
            # 2. Verificar se há cálculos com escola_id NULL ou inválido
            logger.info("\n2. VERIFICANDO CALCULOS COM escola_id INVALIDO")
            logger.info("-" * 60)
            
            query_invalidos = text("""
                SELECT COUNT(*) 
                FROM calculos_profin c
                WHERE c.escola_id NOT IN (SELECT id FROM escolas)
                OR c.escola_id IS NULL;
            """)
            
            invalidos = db.execute(query_invalidos).scalar()
            logger.info(f"Calculos com escola_id invalido: {invalidos}")
            
            # 3. Verificar total de cálculos vs escolas
            logger.info("\n3. COMPARACAO TOTAL")
            logger.info("-" * 60)
            
            total_calculos = db.execute(text("SELECT COUNT(*) FROM calculos_profin")).scalar()
            total_escolas = db.execute(text("SELECT COUNT(*) FROM escolas")).scalar()
            escolas_com_calculo = db.execute(text("""
                SELECT COUNT(DISTINCT escola_id) FROM calculos_profin
            """)).scalar()
            
            logger.info(f"Total de calculos: {total_calculos}")
            logger.info(f"Total de escolas: {total_escolas}")
            logger.info(f"Escolas distintas com calculo: {escolas_com_calculo}")
            
            diferenca = total_calculos - escolas_com_calculo
            if diferenca > 0:
                logger.warning(f"ATENCAO: Ha {diferenca} calculo(s) a mais que escolas distintas!")
            
            # 4. Listar alguns cálculos para inspeção manual
            logger.info("\n4. AMOSTRA DE CALCULOS (primeiros 10)")
            logger.info("-" * 60)
            
            query_amostra = text("""
                SELECT 
                    c.id,
                    c.escola_id,
                    e.nome_uex,
                    c.calculated_at,
                    c.valor_total
                FROM calculos_profin c
                LEFT JOIN escolas e ON c.escola_id = e.id
                ORDER BY c.id
                LIMIT 10;
            """)
            
            amostra = db.execute(query_amostra).fetchall()
            for calc_id, escola_id, nome_uex, calculated_at, valor_total in amostra:
                logger.info(f"  Calculo ID {calc_id}: Escola {escola_id} ({nome_uex}), Data: {calculated_at}, Total: R$ {valor_total}")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"VERIFICACAO CONCLUIDA")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.exception("Erro ao verificar calculos")
            raise


if __name__ == "__main__":
    try:
        verificar_calculos_detalhado()
    except Exception as e:
        logger.exception("Erro ao executar verificacao")
        sys.exit(1)
