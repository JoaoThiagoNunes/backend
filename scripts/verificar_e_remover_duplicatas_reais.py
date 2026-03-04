"""
Script para verificar e remover duplicatas reais.
Mantém apenas 1 cálculo por escola (o mais recente).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.api import *
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.database import get_db_session
from src.core.logging_config import logger
from src.modules.features.uploads.repository import ContextoAtivoRepository


def verificar_e_remover_duplicatas():
    """
    Verifica e remove duplicatas reais, mantendo apenas 1 cálculo por escola.
    """
    with get_db_session() as db:
        logger.info(f"\n{'='*60}")
        logger.info(f"VERIFICACAO E REMOCAO DE DUPLICATAS REAIS")
        logger.info(f"{'='*60}\n")
        
        try:
            # 1. Verificar quantas escolas existem
            logger.info("1. VERIFICANDO ESCOLAS")
            logger.info("-" * 60)
            
            total_escolas = db.execute(text("SELECT COUNT(*) FROM escolas")).scalar()
            logger.info(f"Total de escolas: {total_escolas}")
            
            # Verificar escolas do upload ativo
            contexto_repo = ContextoAtivoRepository(db)
            upload_ativo = None
            try:
                upload_ativo = contexto_repo.find_upload_ativo(None)
            except:
                pass
            
            if upload_ativo:
                escolas_upload_ativo = db.execute(text("""
                    SELECT COUNT(*) FROM escolas WHERE upload_id = :upload_id
                """), {"upload_id": upload_ativo.id}).scalar()
                logger.info(f"Escolas do upload ativo (ID {upload_ativo.id}): {escolas_upload_ativo}")
            else:
                logger.warning("Nenhum upload ativo encontrado!")
                # Buscar o upload mais recente
                upload_mais_recente = db.execute(text("""
                    SELECT id FROM uploads ORDER BY upload_date DESC LIMIT 1
                """)).scalar()
                if upload_mais_recente:
                    escolas_upload_recente = db.execute(text("""
                        SELECT COUNT(*) FROM escolas WHERE upload_id = :upload_id
                    """), {"upload_id": upload_mais_recente}).scalar()
                    logger.info(f"Escolas do upload mais recente (ID {upload_mais_recente}): {escolas_upload_recente}")
            
            # 2. Verificar quantos cálculos existem
            logger.info("\n2. VERIFICANDO CALCULOS")
            logger.info("-" * 60)
            
            total_calculos = db.execute(text("SELECT COUNT(*) FROM calculos_profin")).scalar()
            logger.info(f"Total de calculos: {total_calculos}")
            
            # Verificar quantas escolas distintas têm cálculos
            escolas_com_calculo = db.execute(text("""
                SELECT COUNT(DISTINCT escola_id) FROM calculos_profin
            """)).scalar()
            logger.info(f"Escolas distintas com calculo: {escolas_com_calculo}")
            
            diferenca = total_calculos - escolas_com_calculo
            if diferenca > 0:
                logger.warning(f"ATENCAO: Ha {diferenca} calculo(s) duplicado(s)!")
            
            # 3. Identificar duplicatas detalhadamente
            logger.info("\n3. IDENTIFICANDO DUPLICATAS")
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
            """)
            
            duplicatas = db.execute(query_duplicatas).fetchall()
            
            if duplicatas:
                logger.warning(f"ENCONTRADAS {len(duplicatas)} ESCOLAS COM MULTIPLOS CALCULOS:")
                total_duplicatas = 0
                for escola_id, quantidade, calculo_ids, datas in duplicatas:
                    total_duplicatas += (quantidade - 1)
                    logger.warning(f"  Escola {escola_id}: {quantidade} calculo(s) - IDs: {calculo_ids}")
                
                logger.warning(f"\nTotal de calculos duplicados a remover: {total_duplicatas}")
            else:
                logger.info("Nenhuma duplicata encontrada por escola_id")
            
            # 4. Verificar se há cálculos de escolas que não existem mais
            logger.info("\n4. VERIFICANDO CALCULOS ORFAOS")
            logger.info("-" * 60)
            
            calculos_orfaos = db.execute(text("""
                SELECT COUNT(*) 
                FROM calculos_profin c
                WHERE c.escola_id NOT IN (SELECT id FROM escolas)
            """)).scalar()
            
            logger.info(f"Calculos de escolas que nao existem mais: {calculos_orfaos}")
            
            # 5. Remover duplicatas
            logger.info("\n5. REMOVENDO DUPLICATAS")
            logger.info("-" * 60)
            
            # Primeiro, remover constraint temporariamente
            try:
                db.execute(text("""
                    ALTER TABLE calculos_profin 
                    DROP CONSTRAINT IF EXISTS calculos_profin_escola_id_key;
                """))
                db.commit()
                logger.info("Constraint removida temporariamente")
            except Exception as e:
                logger.warning(f"Nao foi possivel remover constraint: {e}")
                db.rollback()
            
            # Deletar parcelas dos cálculos duplicados
            query_deletar_parcelas = text("""
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
            
            result_parcelas = db.execute(query_deletar_parcelas)
            parcelas_deletadas = result_parcelas.rowcount
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
            
            # Deletar cálculos duplicados (manter apenas o mais recente)
            query_deletar_calculos = text("""
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
            
            result_calculos = db.execute(query_deletar_calculos)
            calculos_deletados = result_calculos.rowcount
            logger.info(f"Calculos duplicados deletados: {calculos_deletados}")
            
            # Deletar cálculos órfãos (escolas que não existem mais)
            if calculos_orfaos > 0:
                query_deletar_orfaos = text("""
                    DELETE FROM parcelas_profin
                    WHERE calculo_id IN (
                        SELECT id FROM calculos_profin
                        WHERE escola_id NOT IN (SELECT id FROM escolas)
                    )
                """)
                db.execute(query_deletar_orfaos)
                
                query_deletar_orfaos_calc = text("""
                    DELETE FROM calculos_profin
                    WHERE escola_id NOT IN (SELECT id FROM escolas)
                """)
                result_orfaos = db.execute(query_deletar_orfaos_calc)
                orfaos_deletados = result_orfaos.rowcount
                logger.info(f"Calculos orfaos deletados: {orfaos_deletados}")
            
            # Recriar constraint
            try:
                db.execute(text("""
                    ALTER TABLE calculos_profin 
                    ADD CONSTRAINT calculos_profin_escola_id_key 
                    UNIQUE (escola_id);
                """))
                logger.info("Constraint recriada com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao recriar constraint: {e}")
            
            # Commit
            db.commit()
            logger.info("\nAlteracoes commitadas!")
            
            # 6. Verificar resultado final
            logger.info("\n6. VERIFICANDO RESULTADO FINAL")
            logger.info("-" * 60)
            
            total_calculos_depois = db.execute(text("SELECT COUNT(*) FROM calculos_profin")).scalar()
            escolas_com_calculo_depois = db.execute(text("""
                SELECT COUNT(DISTINCT escola_id) FROM calculos_profin
            """)).scalar()
            
            logger.info(f"Total de calculos depois: {total_calculos_depois}")
            logger.info(f"Escolas com calculo depois: {escolas_com_calculo_depois}")
            
            # Verificar duplicatas novamente
            duplicatas_depois = db.execute(query_duplicatas).fetchall()
            if duplicatas_depois:
                logger.warning(f"ATENCAO: Ainda ha {len(duplicatas_depois)} duplicata(s)!")
            else:
                logger.info("OK: Nenhuma duplicata restante!")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"REMOCAO CONCLUIDA")
            logger.info(f"{'='*60}")
            logger.info(f"Calculos deletados: {calculos_deletados}")
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
            logger.info(f"Total antes: {total_calculos}")
            logger.info(f"Total depois: {total_calculos_depois}")
            logger.info(f"Esperado: 318 escolas")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.exception("Erro ao remover duplicatas")
            db.rollback()
            raise


if __name__ == "__main__":
    try:
        verificar_e_remover_duplicatas()
    except Exception as e:
        logger.exception("Erro ao executar remocao")
        sys.exit(1)
