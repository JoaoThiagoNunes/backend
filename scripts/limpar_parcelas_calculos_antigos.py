"""
Script para limpar parcelas_profin de cálculos de uploads não ativos.
Mantém apenas parcelas dos cálculos do upload ativo.
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
from src.core.database import get_db
from src.modules.features.uploads.repository import UploadRepository, ContextoAtivoRepository
from src.core.logging_config import logger


def limpar_parcelas_calculos_antigos(ano_letivo_id: int = None):
    """
    Limpa parcelas_profin de cálculos de uploads não ativos.
    Mantém apenas parcelas dos cálculos do upload ativo.
    
    Args:
        ano_letivo_id: ID do ano letivo. Se None, limpa todos os anos letivos.
    """
    db: Session = next(get_db())
    
    try:
        upload_repo = UploadRepository(db)
        contexto_repo = ContextoAtivoRepository(db)
        
        # Determinar quais anos letivos processar
        if ano_letivo_id:
            anos_letivos = [ano_letivo_id]
        else:
            # Buscar todos os anos letivos que têm uploads
            from src.modules.features.anos.repository import AnoLetivoRepository
            ano_repo = AnoLetivoRepository(db)
            anos_letivos = [ano.id for ano in ano_repo.find_all_ordered()]
        
        total_parcelas_deletadas = 0
        
        for ano_id in anos_letivos:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processando ano letivo ID: {ano_id}")
            logger.info(f"{'='*60}")
            
            # Buscar upload ativo
            upload_ativo = contexto_repo.find_upload_ativo(ano_id)
            
            if not upload_ativo:
                logger.warning(f"Nenhum upload ativo encontrado para ano letivo {ano_id}")
                continue
            
            logger.info(f"Upload ativo: ID {upload_ativo.id} - {upload_ativo.filename}")
            
            # Buscar todos os cálculos do upload ativo
            calculos_ativos = (
                db.query(CalculosProfin)
                .join(Escola, CalculosProfin.escola_id == Escola.id)
                .filter(Escola.upload_id == upload_ativo.id)
                .all()
            )
            
            calculos_ids_ativos = {c.id for c in calculos_ativos}
            logger.info(f"Cálculos ativos: {len(calculos_ids_ativos)}")
            
            # Buscar todos os cálculos do ano letivo
            todos_calculos = (
                db.query(CalculosProfin)
                .join(Escola, CalculosProfin.escola_id == Escola.id)
                .join(Upload, Escola.upload_id == Upload.id)
                .filter(Upload.ano_letivo_id == ano_id)
                .all()
            )
            
            # Identificar cálculos não ativos
            calculos_nao_ativos = [c for c in todos_calculos if c.id not in calculos_ids_ativos]
            
            if not calculos_nao_ativos:
                logger.info(f"Nenhum cálculo não ativo encontrado para ano letivo {ano_id}")
                continue
            
            logger.info(f"Cálculos não ativos: {len(calculos_nao_ativos)}")
            
            # Deletar parcelas dos cálculos não ativos
            calculos_ids_nao_ativos = [c.id for c in calculos_nao_ativos]
            
            parcelas_deletadas = (
                db.query(ParcelasProfin)
                .filter(ParcelasProfin.calculo_id.in_(calculos_ids_nao_ativos))
                .delete(synchronize_session=False)
            )
            
            total_parcelas_deletadas += parcelas_deletadas
            logger.info(f"Parcelas deletadas: {parcelas_deletadas}")
        
        # Commit das mudanças
        db.commit()
        
        logger.info(f"\n{'='*60}")
        logger.info("LIMPEZA CONCLUÍDA")
        logger.info(f"{'='*60}")
        logger.info(f"Total de parcelas deletadas: {total_parcelas_deletadas}")
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erro durante limpeza: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Limpar parcelas_profin de cálculos não ativos")
    parser.add_argument(
        "--ano-letivo-id",
        type=int,
        default=None,
        help="ID do ano letivo (opcional, se não informado limpa todos)"
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Pular confirmação e executar automaticamente"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("SCRIPT DE LIMPEZA DE PARCELAS DE CÁLCULOS ANTIGOS")
    print("="*60)
    print("\nEste script irá:")
    print("  - Identificar parcelas_profin de cálculos não ativos")
    print("  - Deletar essas parcelas")
    print("  - Manter apenas parcelas dos cálculos do upload ativo")
    print("\n" + "="*60)
    
    if not args.yes:
        try:
            resposta = input("\nDeseja continuar? (s/N): ").strip().lower()
            if resposta not in ['s', 'sim', 'y', 'yes']:
                print("Operação cancelada.")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\nOperação cancelada (entrada não disponível).")
            print("Use --yes para executar sem confirmação.")
            sys.exit(0)
    
    limpar_parcelas_calculos_antigos(args.ano_letivo_id)
