"""
Script SQL direto para remover duplicatas em calculos_profin.
Remove todos os cálculos duplicados, mantendo apenas o mais recente por escola_id.
"""
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.api import *
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.database import get_db_session
from src.core.logging_config import logger


def remover_duplicatas_sql():
    """
    Remove duplicatas usando SQL direto.
    """
    with get_db_session() as db:
        logger.info(f"\n{'='*60}")
        logger.info(f"REMOCAO DE DUPLICATAS - SQL DIRETO")
        logger.info(f"{'='*60}\n")
        
        try:
            # 1. Verificar duplicatas antes
            logger.info("1. VERIFICANDO DUPLICATAS ANTES DA REMOCAO")
            logger.info("-" * 60)
            
            query_antes = text("""
                SELECT 
                    escola_id,
                    COUNT(*) AS quantidade
                FROM calculos_profin
                GROUP BY escola_id
                HAVING COUNT(*) > 1
                ORDER BY quantidade DESC;
            """)
            
            duplicatas_antes = db.execute(query_antes).fetchall()
            logger.info(f"Duplicatas encontradas: {len(duplicatas_antes)}")
            
            if duplicatas_antes:
                for escola_id, quantidade in duplicatas_antes:
                    logger.info(f"  Escola ID {escola_id}: {quantidade} calculo(s)")
            
            # 2. Deletar parcelas dos cálculos duplicados primeiro
            logger.info("\n2. DELETANDO PARCELAS DOS CALCULOS DUPLICADOS")
            logger.info("-" * 60)
            
            query_deletar_parcelas = text("""
                DELETE FROM parcelas_profin
                WHERE calculo_id IN (
                    SELECT id
                    FROM (
                        SELECT 
                            id,
                            ROW_NUMBER() OVER (
                                PARTITION BY escola_id 
                                ORDER BY calculated_at DESC
                            ) as rn
                        FROM calculos_profin
                    ) ranked
                    WHERE rn > 1
                )
            """)
            
            result_parcelas = db.execute(query_deletar_parcelas)
            parcelas_deletadas = result_parcelas.rowcount
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
            
            # 3. Deletar cálculos duplicados (manter apenas o mais recente)
            logger.info("\n3. DELETANDO CALCULOS DUPLICADOS")
            logger.info("-" * 60)
            
            query_deletar_calculos = text("""
                DELETE FROM calculos_profin
                WHERE id IN (
                    SELECT id
                    FROM (
                        SELECT 
                            id,
                            ROW_NUMBER() OVER (
                                PARTITION BY escola_id 
                                ORDER BY calculated_at DESC
                            ) as rn
                        FROM calculos_profin
                    ) ranked
                    WHERE rn > 1
                )
            """)
            
            result_calculos = db.execute(query_deletar_calculos)
            calculos_deletados = result_calculos.rowcount
            logger.info(f"Calculos deletados: {calculos_deletados}")
            
            # 4. Commit das alterações
            db.commit()
            logger.info("\nAlteracoes commitadas com sucesso!")
            
            # 5. Verificar duplicatas depois
            logger.info("\n4. VERIFICANDO DUPLICATAS DEPOIS DA REMOCAO")
            logger.info("-" * 60)
            
            duplicatas_depois = db.execute(query_antes).fetchall()
            logger.info(f"Duplicatas restantes: {len(duplicatas_depois)}")
            
            if duplicatas_depois:
                logger.warning("ATENCAO: Ainda ha duplicatas!")
                for escola_id, quantidade in duplicatas_depois:
                    logger.warning(f"  Escola ID {escola_id}: {quantidade} calculo(s)")
            else:
                logger.info("OK: Nenhuma duplicata restante!")
            
            # 6. Estatísticas finais
            logger.info("\n5. ESTATISTICAS FINAIS")
            logger.info("-" * 60)
            
            total_calculos = db.execute(text("SELECT COUNT(*) FROM calculos_profin")).scalar()
            total_escolas = db.execute(text("SELECT COUNT(*) FROM escolas")).scalar()
            
            logger.info(f"Total de calculos: {total_calculos}")
            logger.info(f"Total de escolas: {total_escolas}")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"REMOCAO CONCLUIDA")
            logger.info(f"{'='*60}")
            logger.info(f"Calculos deletados: {calculos_deletados}")
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.exception("Erro ao remover duplicatas")
            db.rollback()
            raise


if __name__ == "__main__":
    try:
        remover_duplicatas_sql()
    except Exception as e:
        logger.exception("Erro ao executar remocao")
        sys.exit(1)
