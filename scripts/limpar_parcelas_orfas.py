"""
Script para limpar parcelas_profin órfãs (parcelas de cálculos que não existem mais).
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
from src.core.logging_config import logger


def limpar_parcelas_orfas():
    """
    Limpa parcelas_profin órfãs (parcelas de cálculos que não existem mais).
    """
    db: Session = next(get_db())
    
    try:
        # Buscar todas as parcelas que não têm cálculo associado
        parcelas_orfas = (
            db.query(ParcelasProfin)
            .outerjoin(CalculosProfin, ParcelasProfin.calculo_id == CalculosProfin.id)
            .filter(CalculosProfin.id.is_(None))
            .all()
        )
        
        total_parcelas_orfas = len(parcelas_orfas)
        
        if total_parcelas_orfas == 0:
            logger.info("Nenhuma parcela órfã encontrada.")
            return
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Encontradas {total_parcelas_orfas} parcela(s) órfã(s)")
        logger.info(f"{'='*60}")
        
        # Deletar parcelas órfãs
        calculos_ids_orfaos = {p.calculo_id for p in parcelas_orfas}
        
        deleted = (
            db.query(ParcelasProfin)
            .filter(ParcelasProfin.calculo_id.in_(list(calculos_ids_orfaos)))
            .delete(synchronize_session=False)
        )
        
        db.commit()
        
        logger.info(f"\n{'='*60}")
        logger.info("LIMPEZA CONCLUÍDA")
        logger.info(f"{'='*60}")
        logger.info(f"Total de parcelas órfãs deletadas: {deleted}")
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erro durante limpeza: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Limpar parcelas_profin órfãs")
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Pular confirmação e executar automaticamente"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("SCRIPT DE LIMPEZA DE PARCELAS ÓRFÃS")
    print("="*60)
    print("\nEste script irá:")
    print("  - Identificar parcelas_profin de cálculos que não existem mais")
    print("  - Deletar essas parcelas órfãs")
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
    
    limpar_parcelas_orfas()
