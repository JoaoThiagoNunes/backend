"""
Script para remover cálculos de escolas que não estão no upload mais recente.
Mantém apenas cálculos das 318 escolas do upload mais recente.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.api import *
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.database import get_db_session
from src.core.logging_config import logger


def remover_calculos_escolas_antigas():
    """
    Remove cálculos de escolas que não estão no upload mais recente.
    """
    with get_db_session() as db:
        logger.info(f"\n{'='*60}")
        logger.info(f"REMOCAO DE CALCULOS DE ESCOLAS ANTIGAS")
        logger.info(f"{'='*60}\n")
        
        try:
            # 1. Identificar upload mais recente
            logger.info("1. IDENTIFICANDO UPLOAD MAIS RECENTE")
            logger.info("-" * 60)
            
            upload_mais_recente = db.execute(text("""
                SELECT id, filename, upload_date, ano_letivo_id
                FROM uploads 
                ORDER BY upload_date DESC 
                LIMIT 1
            """)).fetchone()
            
            if not upload_mais_recente:
                logger.error("Nenhum upload encontrado!")
                return
            
            upload_id, filename, upload_date, ano_letivo_id = upload_mais_recente
            logger.info(f"Upload mais recente: ID {upload_id}")
            logger.info(f"  Arquivo: {filename}")
            logger.info(f"  Data: {upload_date}")
            logger.info(f"  Ano letivo ID: {ano_letivo_id}")
            
            # Contar escolas desse upload
            escolas_upload_recente = db.execute(text("""
                SELECT COUNT(*) FROM escolas WHERE upload_id = :upload_id
            """), {"upload_id": upload_id}).scalar()
            logger.info(f"  Escolas neste upload: {escolas_upload_recente}")
            
            # 2. Contar cálculos antes
            logger.info("\n2. CONTANDO CALCULOS ANTES DA REMOCAO")
            logger.info("-" * 60)
            
            total_calculos_antes = db.execute(text("SELECT COUNT(*) FROM calculos_profin")).scalar()
            logger.info(f"Total de calculos antes: {total_calculos_antes}")
            
            # Contar cálculos do upload mais recente
            calculos_upload_recente = db.execute(text("""
                SELECT COUNT(*) 
                FROM calculos_profin c
                JOIN escolas e ON c.escola_id = e.id
                WHERE e.upload_id = :upload_id
            """), {"upload_id": upload_id}).scalar()
            logger.info(f"Calculos do upload mais recente: {calculos_upload_recente}")
            
            # Contar cálculos de outros uploads
            calculos_outros_uploads = total_calculos_antes - calculos_upload_recente
            logger.info(f"Calculos de outros uploads: {calculos_outros_uploads}")
            
            if calculos_outros_uploads == 0:
                logger.info("OK: Nenhum calculo de upload antigo encontrado!")
                return
            
            # 3. Deletar parcelas dos cálculos antigos primeiro
            logger.info("\n3. DELETANDO PARCELAS DOS CALCULOS ANTIGOS")
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
            
            result_parcelas = db.execute(query_deletar_parcelas, {"upload_id": upload_id})
            parcelas_deletadas = result_parcelas.rowcount
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
            
            # 4. Deletar cálculos de escolas de outros uploads
            logger.info("\n4. DELETANDO CALCULOS DE ESCOLAS ANTIGAS")
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
            
            result_calculos = db.execute(query_deletar_calculos, {"upload_id": upload_id})
            calculos_deletados = result_calculos.rowcount
            logger.info(f"Calculos deletados: {calculos_deletados}")
            
            # 5. Commit
            db.commit()
            logger.info("\nAlteracoes commitadas com sucesso!")
            
            # 6. Verificar resultado final
            logger.info("\n5. VERIFICANDO RESULTADO FINAL")
            logger.info("-" * 60)
            
            total_calculos_depois = db.execute(text("SELECT COUNT(*) FROM calculos_profin")).scalar()
            calculos_upload_recente_depois = db.execute(text("""
                SELECT COUNT(*) 
                FROM calculos_profin c
                JOIN escolas e ON c.escola_id = e.id
                WHERE e.upload_id = :upload_id
            """), {"upload_id": upload_id}).scalar()
            
            logger.info(f"Total de calculos depois: {total_calculos_depois}")
            logger.info(f"Calculos do upload mais recente: {calculos_upload_recente_depois}")
            logger.info(f"Esperado: {escolas_upload_recente} calculos")
            
            if total_calculos_depois == escolas_upload_recente:
                logger.info("OK: Quantidade correta de calculos!")
            else:
                logger.warning(f"ATENCAO: Esperado {escolas_upload_recente}, mas ha {total_calculos_depois}")
            
            # Verificar se ainda há duplicatas
            query_duplicatas = text("""
                SELECT escola_id, COUNT(*) 
                FROM calculos_profin 
                GROUP BY escola_id 
                HAVING COUNT(*) > 1
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
            logger.info(f"Total antes: {total_calculos_antes}")
            logger.info(f"Total depois: {total_calculos_depois}")
            logger.info(f"Esperado: {escolas_upload_recente}")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.exception("Erro ao remover calculos antigos")
            db.rollback()
            raise


if __name__ == "__main__":
    try:
        remover_calculos_escolas_antigas()
    except Exception as e:
        logger.exception("Erro ao executar remocao")
        sys.exit(1)
