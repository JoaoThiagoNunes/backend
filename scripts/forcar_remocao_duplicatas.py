"""
Script para forçar remoção de duplicatas, mesmo que a constraint não detecte.
Remove todos os cálculos duplicados mantendo apenas o mais recente.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.api import *
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.database import get_db_session
from src.core.logging_config import logger


def forcar_remocao_duplicatas():
    """
    Força remoção de duplicatas usando SQL direto.
    """
    with get_db_session() as db:
        logger.info(f"\n{'='*60}")
        logger.info(f"FORCAR REMOCAO DE DUPLICATAS")
        logger.info(f"{'='*60}\n")
        
        try:
            # 1. Desabilitar temporariamente a constraint (se possível)
            logger.info("1. VERIFICANDO CONSTRAINT")
            logger.info("-" * 60)
            
            # Tentar remover constraint temporariamente (pode falhar se houver dados)
            try:
                db.execute(text("""
                    ALTER TABLE calculos_profin 
                    DROP CONSTRAINT IF EXISTS calculos_profin_escola_id_key;
                """))
                db.commit()
                logger.info("Constraint removida temporariamente")
                constraint_removida = True
            except Exception as e:
                logger.warning(f"Nao foi possivel remover constraint: {e}")
                constraint_removida = False
                db.rollback()
            
            # 2. Remover duplicatas usando ROW_NUMBER
            logger.info("\n2. REMOVENDO DUPLICATAS")
            logger.info("-" * 60)
            
            # Deletar parcelas primeiro
            query_parcelas = text("""
                DELETE FROM parcelas_profin
                WHERE calculo_id IN (
                    SELECT id FROM (
                        SELECT 
                            id,
                            ROW_NUMBER() OVER (
                                PARTITION BY escola_id 
                                ORDER BY calculated_at DESC, id DESC
                            ) as rn
                        FROM calculos_profin
                    ) ranked
                    WHERE rn > 1
                )
            """)
            
            result_parcelas = db.execute(query_parcelas)
            parcelas_deletadas = result_parcelas.rowcount
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
            
            # Deletar cálculos duplicados
            query_calculos = text("""
                DELETE FROM calculos_profin
                WHERE id IN (
                    SELECT id FROM (
                        SELECT 
                            id,
                            ROW_NUMBER() OVER (
                                PARTITION BY escola_id 
                                ORDER BY calculated_at DESC, id DESC
                            ) as rn
                        FROM calculos_profin
                    ) ranked
                    WHERE rn > 1
                )
            """)
            
            result_calculos = db.execute(query_calculos)
            calculos_deletados = result_calculos.rowcount
            logger.info(f"Calculos deletados: {calculos_deletados}")
            
            # 3. Recriar constraint se foi removida
            if constraint_removida:
                logger.info("\n3. RECRIANDO CONSTRAINT")
                logger.info("-" * 60)
                try:
                    db.execute(text("""
                        ALTER TABLE calculos_profin 
                        ADD CONSTRAINT calculos_profin_escola_id_key 
                        UNIQUE (escola_id);
                    """))
                    logger.info("Constraint recriada com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao recriar constraint: {e}")
            
            # 4. Commit
            db.commit()
            logger.info("\nAlteracoes commitadas!")
            
            # 5. Verificar resultado
            logger.info("\n4. VERIFICANDO RESULTADO")
            logger.info("-" * 60)
            
            total_calculos = db.execute(text("SELECT COUNT(*) FROM calculos_profin")).scalar()
            total_escolas = db.execute(text("SELECT COUNT(*) FROM escolas")).scalar()
            
            logger.info(f"Total de calculos: {total_calculos}")
            logger.info(f"Total de escolas: {total_escolas}")
            
            # Verificar duplicatas novamente
            query_duplicatas = text("""
                SELECT escola_id, COUNT(*) 
                FROM calculos_profin 
                GROUP BY escola_id 
                HAVING COUNT(*) > 1
            """)
            
            duplicatas = db.execute(query_duplicatas).fetchall()
            if duplicatas:
                logger.warning(f"ATENCAO: Ainda ha {len(duplicatas)} duplicata(s)!")
                for escola_id, quantidade in duplicatas:
                    logger.warning(f"  Escola {escola_id}: {quantidade} calculo(s)")
            else:
                logger.info("OK: Nenhuma duplicata encontrada!")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"REMOCAO CONCLUIDA")
            logger.info(f"{'='*60}")
            logger.info(f"Calculos deletados: {calculos_deletados}")
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.exception("Erro ao forcar remocao")
            db.rollback()
            raise


if __name__ == "__main__":
    try:
        forcar_remocao_duplicatas()
    except Exception as e:
        logger.exception("Erro ao executar remocao")
        sys.exit(1)
