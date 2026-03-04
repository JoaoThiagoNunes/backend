"""
Script para limpar parcelas_profin duplicadas/acumuladas do banco de dados.
Mantém apenas as parcelas mais recentes para cada cálculo.
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
from sqlalchemy import func
from src.core.database import get_db
from src.core.logging_config import logger


def limpar_parcelas_duplicadas(ano_letivo_id: int = None):
    """
    Limpa parcelas_profin duplicadas/acumuladas.
    Mantém apenas as parcelas mais recentes para cada cálculo.
    
    Args:
        ano_letivo_id: ID do ano letivo. Se None, limpa todos os anos letivos.
    """
    db: Session = next(get_db())
    
    try:
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
            
            # Buscar todos os cálculos do ano letivo
            calculos = (
                db.query(CalculosProfin)
                .join(Escola, CalculosProfin.escola_id == Escola.id)
                .join(Upload, Escola.upload_id == Upload.id)
                .filter(Upload.ano_letivo_id == ano_id)
                .all()
            )
            
            if not calculos:
                logger.info(f"Nenhum cálculo encontrado para ano letivo {ano_id}")
                continue
            
            logger.info(f"Encontrados {len(calculos)} cálculo(s)")
            
            parcelas_deletadas_ano = 0
            
            for calculo in calculos:
                # Buscar todas as parcelas deste cálculo
                parcelas = (
                    db.query(ParcelasProfin)
                    .filter(ParcelasProfin.calculo_id == calculo.id)
                    .order_by(ParcelasProfin.created_at.desc())
                    .all()
                )
                
                if len(parcelas) <= 2:  # Número esperado de parcelas por cota (fundamental + médio)
                    continue
                
                # Agrupar por (tipo_cota, numero_parcela, tipo_ensino)
                # e manter apenas a mais recente de cada grupo
                grupos = {}
                for parcela in parcelas:
                    chave = (
                        parcela.tipo_cota,
                        parcela.numero_parcela,
                        parcela.tipo_ensino
                    )
                    
                    if chave not in grupos:
                        grupos[chave] = []
                    grupos[chave].append(parcela)
                
                # Para cada grupo, manter apenas a mais recente e deletar as outras
                for chave, parcelas_grupo in grupos.items():
                    if len(parcelas_grupo) > 1:
                        # Ordenar por created_at (mais recente primeiro)
                        parcelas_grupo.sort(key=lambda p: p.created_at, reverse=True)
                        
                        # Manter a primeira (mais recente) e deletar as outras
                        for parcela_antiga in parcelas_grupo[1:]:
                            db.delete(parcela_antiga)
                            parcelas_deletadas_ano += 1
                            logger.debug(
                                f"  Parcela deletada: cálculo {calculo.id}, "
                                f"cota {parcela_antiga.tipo_cota.value}, "
                                f"parcela {parcela_antiga.numero_parcela}, "
                                f"ensino {parcela_antiga.tipo_ensino.value}"
                            )
            
            total_parcelas_deletadas += parcelas_deletadas_ano
            logger.info(f"\nAno letivo {ano_id}: {parcelas_deletadas_ano} parcela(s) duplicada(s) deletada(s)")
        
        # Commit das mudanças
        db.commit()
        
        logger.info(f"\n{'='*60}")
        logger.info("LIMPEZA CONCLUÍDA")
        logger.info(f"{'='*60}")
        logger.info(f"Total de parcelas duplicadas deletadas: {total_parcelas_deletadas}")
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erro durante limpeza: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Limpar parcelas_profin duplicadas")
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
    print("SCRIPT DE LIMPEZA DE PARCELAS DUPLICADAS")
    print("="*60)
    print("\nEste script irá:")
    print("  - Identificar parcelas_profin duplicadas")
    print("  - Manter apenas as parcelas mais recentes")
    print("  - Deletar parcelas antigas duplicadas")
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
    
    limpar_parcelas_duplicadas(args.ano_letivo_id)
