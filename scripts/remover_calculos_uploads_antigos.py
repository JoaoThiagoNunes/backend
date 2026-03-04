"""
Script para remover cálculos de escolas que não estão no upload ativo.
Mantém apenas cálculos das escolas do upload ativo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.api import *
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.database import get_db_session
from src.core.logging_config import logger
from src.modules.features.uploads.repository import UploadRepository
from src.modules.features.anos.repository import AnoLetivoRepository
from src.modules.features.uploads.repository import ContextoAtivoRepository


def remover_calculos_uploads_antigos(ano_letivo_id: int = None):
    """
    Remove cálculos de escolas que não estão no upload ativo.
    """
    with get_db_session() as db:
        logger.info(f"\n{'='*60}")
        logger.info(f"REMOCAO DE CALCULOS DE UPLOADS ANTIGOS")
        logger.info(f"{'='*60}\n")
        
        try:
            # 1. Identificar upload ativo
            logger.info("1. IDENTIFICANDO UPLOAD ATIVO")
            logger.info("-" * 60)
            
            contexto_repo = ContextoAtivoRepository(db)
            upload_ativo = contexto_repo.find_upload_ativo(ano_letivo_id)
            
            if not upload_ativo:
                logger.error("Nenhum upload ativo encontrado!")
                return
            
            logger.info(f"Upload ativo: ID {upload_ativo.id} - {upload_ativo.filename}")
            
            # 2. Contar cálculos antes
            logger.info("\n2. CONTANDO CALCULOS ANTES DA REMOCAO")
            logger.info("-" * 60)
            
            total_antes = db.execute(text("SELECT COUNT(*) FROM calculos_profin")).scalar()
            logger.info(f"Total de calculos antes: {total_antes}")
            
            # 3. Identificar cálculos a deletar (escolas não do upload ativo)
            logger.info("\n3. IDENTIFICANDO CALCULOS PARA DELETAR")
            logger.info("-" * 60)
            
            query_calculos_antigos = text("""
                SELECT COUNT(*)
                FROM calculos_profin c
                JOIN escolas e ON c.escola_id = e.id
                WHERE e.upload_id != :upload_id
            """)
            
            calculos_antigos_count = db.execute(
                query_calculos_antigos, 
                {"upload_id": upload_ativo.id}
            ).scalar()
            
            logger.info(f"Calculos de escolas fora do upload ativo: {calculos_antigos_count}")
            
            if calculos_antigos_count == 0:
                logger.info("OK: Nenhum calculo de upload antigo encontrado!")
                return
            
            # 4. Deletar parcelas primeiro
            logger.info("\n4. DELETANDO PARCELAS DOS CALCULOS ANTIGOS")
            logger.info("-" * 60)
            
            query_deletar_parcelas = text("""
                DELETE FROM parcelas_profin
                WHERE calculo_id IN (
                    SELECT c.id
                    FROM calculos_profin c
                    JOIN escolas e ON c.escola_id = e.id
                    WHERE e.upload_id != :upload_id
                )
            """)
            
            result_parcelas = db.execute(
                query_deletar_parcelas,
                {"upload_id": upload_ativo.id}
            )
            parcelas_deletadas = result_parcelas.rowcount
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
            
            # 5. Deletar cálculos
            logger.info("\n5. DELETANDO CALCULOS ANTIGOS")
            logger.info("-" * 60)
            
            query_deletar_calculos = text("""
                DELETE FROM calculos_profin
                WHERE id IN (
                    SELECT c.id
                    FROM calculos_profin c
                    JOIN escolas e ON c.escola_id = e.id
                    WHERE e.upload_id != :upload_id
                )
            """)
            
            result_calculos = db.execute(
                query_deletar_calculos,
                {"upload_id": upload_ativo.id}
            )
            calculos_deletados = result_calculos.rowcount
            logger.info(f"Calculos deletados: {calculos_deletados}")
            
            # 6. Commit
            db.commit()
            logger.info("\nAlteracoes commitadas com sucesso!")
            
            # 7. Verificar depois
            logger.info("\n6. VERIFICANDO DEPOIS DA REMOCAO")
            logger.info("-" * 60)
            
            total_depois = db.execute(text("SELECT COUNT(*) FROM calculos_profin")).scalar()
            logger.info(f"Total de calculos depois: {total_depois}")
            
            # Verificar se ainda há duplicatas
            query_duplicatas = text("""
                SELECT 
                    escola_id,
                    COUNT(*) AS quantidade
                FROM calculos_profin
                GROUP BY escola_id
                HAVING COUNT(*) > 1;
            """)
            
            duplicatas = db.execute(query_duplicatas).fetchall()
            if duplicatas:
                logger.warning(f"ATENCAO: Ainda ha {len(duplicatas)} duplicata(s)!")
            else:
                logger.info("OK: Nenhuma duplicata encontrada!")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"REMOCAO CONCLUIDA")
            logger.info(f"{'='*60}")
            logger.info(f"Calculos deletados: {calculos_deletados}")
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
            logger.info(f"Total antes: {total_antes}")
            logger.info(f"Total depois: {total_depois}")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.exception("Erro ao remover calculos antigos")
            db.rollback()
            raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remover calculos de uploads antigos")
    parser.add_argument("--ano-letivo-id", type=int, help="ID do ano letivo")
    
    args = parser.parse_args()
    
    try:
        remover_calculos_uploads_antigos(args.ano_letivo_id)
    except Exception as e:
        logger.exception("Erro ao executar remocao")
        sys.exit(1)
