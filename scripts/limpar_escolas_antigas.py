"""
Script para limpar escolas de uploads não ativos do banco de dados.
Preserva escolas que possuem liberações (parcelas ou projetos).
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
from src.modules.features.escolas.repository import EscolaRepository
from src.core.logging_config import logger


def limpar_escolas_antigas(ano_letivo_id: int = None):
    """
    Limpa escolas de uploads não ativos.
    
    Args:
        ano_letivo_id: ID do ano letivo. Se None, limpa todos os anos letivos.
    """
    db: Session = next(get_db())
    
    try:
        upload_repo = UploadRepository(db)
        contexto_repo = ContextoAtivoRepository(db)
        escola_repo = EscolaRepository(db)
        
        # Determinar quais anos letivos processar
        if ano_letivo_id:
            anos_letivos = [ano_letivo_id]
        else:
            # Buscar todos os anos letivos que têm uploads
            from src.modules.features.anos.repository import AnoLetivoRepository
            ano_repo = AnoLetivoRepository(db)
            anos_letivos = [ano.id for ano in ano_repo.find_all_ordered()]
        
        total_escolas_deletadas = 0
        total_escolas_preservadas = 0
        
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
            
            # Buscar todos os uploads do ano letivo
            todos_uploads = upload_repo.find_all_by_ano_letivo(ano_id)
            uploads_nao_ativos = [u for u in todos_uploads if u.id != upload_ativo.id]
            
            if not uploads_nao_ativos:
                logger.info(f"Nenhum upload não ativo encontrado para ano letivo {ano_id}")
                continue
            
            logger.info(f"Encontrados {len(uploads_nao_ativos)} upload(s) não ativo(s)")
            
            escolas_deletadas_ano = 0
            escolas_preservadas_ano = 0
            
            for upload_nao_ativo in uploads_nao_ativos:
                logger.info(f"\nProcessando upload não ativo ID {upload_nao_ativo.id} - {upload_nao_ativo.filename}")
                escolas_upload_antigo = escola_repo.find_by_upload_id(upload_nao_ativo.id)
                
                logger.info(f"  Encontradas {len(escolas_upload_antigo)} escola(s) neste upload")
                
                for escola_antiga in escolas_upload_antigo:
                    # Verificar se tem liberações
                    tem_liberacoes = (
                        len(escola_antiga.liberacoes_parcelas) > 0 or
                        escola_antiga.liberacoes_projetos is not None
                    )
                    
                    if not tem_liberacoes:
                        # Deletar escola (cascade deleta cálculos e complementos automaticamente)
                        escola_repo.delete(escola_antiga)
                        escolas_deletadas_ano += 1
                        logger.debug(f"  ✓ Escola {escola_antiga.id} ({escola_antiga.nome_uex}) deletada")
                    else:
                        escolas_preservadas_ano += 1
                        logger.debug(f"  ⊗ Escola {escola_antiga.id} ({escola_antiga.nome_uex}) preservada (tem liberações)")
                
                logger.info(f"  Upload {upload_nao_ativo.id}: {escolas_deletadas_ano} deletada(s), {escolas_preservadas_ano} preservada(s)")
            
            total_escolas_deletadas += escolas_deletadas_ano
            total_escolas_preservadas += escolas_preservadas_ano
            
            logger.info(f"\nAno letivo {ano_id}: Total deletadas: {escolas_deletadas_ano}, Total preservadas: {escolas_preservadas_ano}")
        
        # Commit das mudanças
        db.commit()
        
        logger.info(f"\n{'='*60}")
        logger.info("LIMPEZA CONCLUÍDA")
        logger.info(f"{'='*60}")
        logger.info(f"Total de escolas deletadas: {total_escolas_deletadas}")
        logger.info(f"Total de escolas preservadas: {total_escolas_preservadas}")
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erro durante limpeza: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Limpar escolas de uploads não ativos")
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
    print("SCRIPT DE LIMPEZA DE ESCOLAS ANTIGAS")
    print("="*60)
    print("\nEste script irá:")
    print("  - Identificar o upload ativo de cada ano letivo")
    print("  - Deletar escolas de uploads não ativos")
    print("  - PRESERVAR escolas que possuem liberações")
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
    
    limpar_escolas_antigas(args.ano_letivo_id)
