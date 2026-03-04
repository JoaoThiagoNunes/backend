"""
Script para diagnosticar duplicatas na tabela calculos_profin.
Verifica constraints do banco e identifica registros duplicados.
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
from sqlalchemy import func, text
from src.core.database import get_db_session
from src.core.logging_config import logger


def diagnosticar_duplicatas_calculos():
    """
    Diagnostica duplicatas na tabela calculos_profin.
    Verifica constraints e identifica registros duplicados.
    """
    with get_db_session() as db:
        logger.info(f"\n{'='*60}")
        logger.info(f"DIAGNÓSTICO DE DUPLICATAS - calculos_profin")
        logger.info(f"{'='*60}\n")
        
        # 1. Verificar constraints da tabela calculos_profin
        logger.info("1. VERIFICANDO CONSTRAINTS DO BANCO DE DADOS")
        logger.info("-" * 60)
        
        try:
            # Verificar constraints unique na tabela calculos_profin
            query_constraints = text("""
                SELECT 
                    conname AS constraint_name,
                    contype AS constraint_type,
                    pg_get_constraintdef(oid) AS constraint_definition
                FROM pg_constraint
                WHERE conrelid = 'calculos_profin'::regclass
                AND contype IN ('u', 'p')
                ORDER BY conname;
            """)
            
            constraints = db.execute(query_constraints).fetchall()
            
            if constraints:
                logger.info(f"Encontradas {len(constraints)} constraint(s):")
                tem_unique_escola_id = False
                for constraint in constraints:
                    constraint_name, constraint_type, constraint_def = constraint
                    logger.info(f"  - {constraint_name} ({'UNIQUE' if constraint_type == 'u' else 'PRIMARY KEY'}): {constraint_def}")
                    if constraint_type == 'u' and 'escola_id' in constraint_def:
                        tem_unique_escola_id = True
                
                if not tem_unique_escola_id:
                    logger.warning("ATENCAO: Nao foi encontrada constraint UNIQUE em escola_id!")
                else:
                    logger.info("OK: Constraint UNIQUE em escola_id encontrada.")
            else:
                logger.warning("⚠️  Nenhuma constraint encontrada na tabela calculos_profin!")
            
        except Exception as e:
            logger.error(f"Erro ao verificar constraints: {e}")
        
        logger.info("")
        
        # 2. Verificar duplicatas por escola_id
        logger.info("2. VERIFICANDO DUPLICATAS POR escola_id")
        logger.info("-" * 60)
        
        try:
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
            
            if duplicatas:
                logger.warning(f"ATENCAO: Encontradas {len(duplicatas)} escola(s) com multiplos calculos:")
                total_duplicatas = 0
                
                for escola_id, quantidade, calculo_ids, datas_calculo in duplicatas:
                    total_duplicatas += (quantidade - 1)
                    logger.warning(f"\n  Escola ID: {escola_id}")
                    logger.warning(f"  Quantidade de cálculos: {quantidade}")
                    logger.warning(f"  IDs dos cálculos: {calculo_ids}")
                    logger.warning(f"  Datas: {datas_calculo}")
                    
                    # Buscar nome da escola
                    escola = db.query(Escola).filter(Escola.id == escola_id).first()
                    if escola:
                        logger.warning(f"  Nome da escola: {escola.nome_uex}")
                        logger.warning(f"  DRE: {escola.dre}")
                
                logger.warning(f"\n  Total de registros duplicados a remover: {total_duplicatas}")
            else:
                logger.info("OK: Nenhuma duplicata encontrada por escola_id.")
        
        except Exception as e:
            logger.error(f"Erro ao verificar duplicatas: {e}")
        
        logger.info("")
        
        # 3. Verificar se há escolas duplicadas
        logger.info("3. VERIFICANDO ESCOLAS DUPLICADAS")
        logger.info("-" * 60)
        
        try:
            query_escolas_duplicadas = text("""
                SELECT 
                    nome_uex,
                    dre,
                    COUNT(*) AS quantidade,
                    ARRAY_AGG(id ORDER BY id) AS escola_ids,
                    ARRAY_AGG(upload_id ORDER BY id) AS upload_ids
                FROM escolas
                GROUP BY nome_uex, dre
                HAVING COUNT(*) > 1
                ORDER BY quantidade DESC
                LIMIT 10;
            """)
            
            escolas_duplicadas = db.execute(query_escolas_duplicadas).fetchall()
            
            if escolas_duplicadas:
                logger.warning(f"⚠️  Encontradas {len(escolas_duplicadas)} combinação(ões) de nome_uex/dre duplicadas:")
                for nome_uex, dre, quantidade, escola_ids, upload_ids in escolas_duplicadas:
                    logger.warning(f"\n  Nome: {nome_uex}")
                    logger.warning(f"  DRE: {dre}")
                    logger.warning(f"  Quantidade: {quantidade}")
                    logger.warning(f"  IDs das escolas: {escola_ids}")
                    logger.warning(f"  IDs dos uploads: {upload_ids}")
            else:
                logger.info("OK: Nenhuma escola duplicada encontrada (mesmo nome_uex e dre).")
        
        except Exception as e:
            logger.error(f"Erro ao verificar escolas duplicadas: {e}")
        
        logger.info("")
        
        # 4. Estatísticas gerais
        logger.info("4. ESTATÍSTICAS GERAIS")
        logger.info("-" * 60)
        
        try:
            total_calculos = db.query(CalculosProfin).count()
            total_escolas = db.query(Escola).count()
            escolas_com_calculo = db.query(func.count(func.distinct(CalculosProfin.escola_id))).scalar()
            escolas_sem_calculo = total_escolas - escolas_com_calculo
            
            logger.info(f"Total de cálculos: {total_calculos}")
            logger.info(f"Total de escolas: {total_escolas}")
            logger.info(f"Escolas com cálculo: {escolas_com_calculo}")
            logger.info(f"Escolas sem cálculo: {escolas_sem_calculo}")
            
            if total_calculos > total_escolas:
                diferenca = total_calculos - total_escolas
                logger.warning(f"ATENCAO: Ha {diferenca} calculo(s) a mais que escolas (possiveis duplicatas)")
        
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
        
        logger.info("")
        logger.info(f"{'='*60}")
        logger.info(f"DIAGNÓSTICO CONCLUÍDO")
        logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Diagnosticar duplicatas em calculos_profin")
    args = parser.parse_args()
    
    try:
        diagnosticar_duplicatas_calculos()
    except Exception as e:
        logger.exception("Erro ao executar diagnóstico")
        sys.exit(1)
