from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from io import BytesIO
import pandas as pd
from src.core.logging_config import logger
from src.core.database import transaction
from src.core.exceptions import UploadNaoEncontradoException, EscolaNaoEncontradaException
from src.modules.features.uploads.repository import UploadRepository
from src.modules.features.uploads import Upload
from src.modules.features.escolas.repository import EscolaRepository
from src.modules.features.escolas.utils import escola_esta_liberada
from src.modules.schemas.upload import UploadListItem, UploadDetailInfo, EscolaPlanilhaInfo
from src.modules.features.anos import obter_ano_letivo
from .utils import obter_ou_criar_upload_ativo
from src.modules.features.projetos import obter_quantidade_projetos_aprovados
from src.modules.shared.utils import obter_texto, obter_quantidade, obter_valor_float, validar_indigena_e_quilombola


class UploadService:
    @staticmethod
    def obter_upload_unico(db: Session, ano_letivo_id: Optional[int] = None) -> UploadListItem:
        from src.modules.features.uploads.repository import ContextoAtivoRepository
        
        _, ano_id = obter_ano_letivo(db, ano_letivo_id)
        contexto_repo = ContextoAtivoRepository(db)
        upload = contexto_repo.find_upload_ativo(ano_id)
        
        if not upload:
            # Fallback para o mais recente se não houver contexto ativo
            upload_repo = UploadRepository(db)
            upload = upload_repo.find_latest(ano_id)
            if not upload:
                raise UploadNaoEncontradoException(ano_letivo_id=ano_id)

        return UploadListItem(
            success=True,
            id=upload.id,
            ano_letivo_id=upload.ano_letivo_id,
            ano_letivo=upload.ano_letivo.ano,
            filename=upload.filename,
            upload_date=upload.upload_date,
            total_escolas=upload.total_escolas
        )
    
    @staticmethod
    def obter_upload_detalhado(
        db: Session, 
        escola_id: Optional[int] = None,
        ano_letivo_id: Optional[int] = None
    ) -> Dict[str, Any]:
        escola_repo = EscolaRepository(db)
        upload_repo = UploadRepository(db)
        
        # Se escola_id for fornecido, buscar a escola diretamente
        if escola_id is not None:
            escola = escola_repo.find_by_id(escola_id)
            if not escola:
                raise EscolaNaoEncontradaException(escola_id=escola_id)
            
            # Buscar o upload da escola
            upload = upload_repo.find_by_id(escola.upload_id)
            if not upload:
                raise UploadNaoEncontradoException(upload_id=escola.upload_id)
            
            # Retornar apenas a escola filtrada
            escolas = [escola]
        else:
            # Caso contrário, usar a lógica anterior com ano_letivo_id
            from src.modules.features.uploads.repository import ContextoAtivoRepository
            
            _, ano_id = obter_ano_letivo(db, ano_letivo_id)
            contexto_repo = ContextoAtivoRepository(db)
            upload = contexto_repo.find_upload_ativo(ano_id)
            
            if not upload:
                # Fallback para o mais recente se não houver contexto ativo
                upload = upload_repo.find_latest(ano_id)
                if not upload:
                    raise UploadNaoEncontradoException(ano_letivo_id=ano_id)
            
            # Buscar todas as escolas do upload
            escolas = escola_repo.find_by_upload_id(upload.id)
        
        escolas_planilha: List[EscolaPlanilhaInfo] = []

        for escola in escolas:
            try:
                dados_escola = {
                    "id": escola.id,
                    "upload_id": escola.upload_id,
                    "nome_uex": escola.nome_uex,
                    "dre": escola.dre,
                    "cnpj": escola.cnpj,
                    "total_alunos": escola.total_alunos,
                    "fundamental_inicial": escola.fundamental_inicial,
                    "fundamental_final": escola.fundamental_final,
                    "fundamental_integral": escola.fundamental_integral,
                    "profissionalizante": escola.profissionalizante,
                    "profissionalizante_integrado": escola.profissionalizante_integrado,
                    "alternancia": escola.alternancia,
                    "ensino_medio_integral": escola.ensino_medio_integral,
                    "ensino_medio_regular": escola.ensino_medio_regular,
                    "especial_fund_regular": escola.especial_fund_regular,
                    "especial_fund_integral": escola.especial_fund_integral,
                    "especial_medio_parcial": escola.especial_medio_parcial,
                    "especial_medio_integral": escola.especial_medio_integral,
                    "sala_recurso": escola.sala_recurso,
                    #"climatizacao": escola.climatizacao, # Desativado temporariamente
                    "preuni": escola.preuni,
                    "quantidade_projetos_aprovados": escola.quantidade_projetos_aprovados,
                    "repasse_por_area": escola.repasse_por_area,
                    "indigena_quilombola": escola.indigena_quilombola,
                    "estado_liberacao": escola_esta_liberada(escola),
                    "numeracao_folha": escola.numeracao_folha,
                    "created_at": escola.created_at,
                    "codigo_ept": escola.codigo_ept,
                    "codigo_inep": escola.codigo_inep,
                    "saldo_reprogramado_gestao": escola.saldo_reprogramado_gestao,
                    "saldo_reprogramado_merenda": escola.saldo_reprogramado_merenda,
                }

                escolas_planilha.append(EscolaPlanilhaInfo(dados_planilha=dados_escola))
            except Exception as e:
                logger.error(f"Erro ao processar escola {escola.id} ({escola.nome_uex}): {str(e)}")
                logger.error(f"profissionalizante_integrado = {escola.profissionalizante_integrado} (tipo: {type(escola.profissionalizante_integrado)})")
                logger.exception("Detalhes completos do erro:")
                # Continuar processando outras escolas, mas logar o erro
                continue

        return {
            "upload": UploadDetailInfo(
                id=upload.id,
                ano_letivo_id=upload.ano_letivo_id,
                ano_letivo=upload.ano_letivo.ano,
                filename=upload.filename,
                upload_date=upload.upload_date,
                total_escolas=upload.total_escolas
            ),
            "escolas": escolas_planilha
        }
    
    @staticmethod
    def processar_planilha_excel(
        db: Session,
        file_contents: bytes,
        filename: str,
        ano_letivo_id: Optional[int] = None
    ) -> Dict[str, Any]:
        ano_letivo, ano_letivo_id = obter_ano_letivo(db, ano_letivo_id)
        logger.info(f"UPLOAD PARA ANO LETIVO: {ano_letivo.ano} (Status: {ano_letivo.status.value})")
        
        if filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(file_contents))
        else:
            df = pd.read_excel(BytesIO(file_contents))
        
        logger.info(f"Arquivo: {filename}")
        logger.info(f"Total de linhas: {len(df)}")
        logger.debug(f"Colunas: {df.columns.tolist()}")
        
        # Identificar upload anterior ANTES de criar novo (para limpar dados relacionados)
        from src.modules.features.uploads.repository import ContextoAtivoRepository
        contexto_repo = ContextoAtivoRepository(db)
        upload_anterior = contexto_repo.find_upload_ativo(ano_letivo_id)
        
        # Obter ou criar upload (cria novo e ativa)
        upload = obter_ou_criar_upload_ativo(db, ano_letivo_id, filename)
        db.flush()
        db.refresh(upload)
        
        # Processar escolas
        upload_repo = UploadRepository(db)
        escola_repo = EscolaRepository(db)
        
        # Limpar dados relacionados do upload anterior (preservando liberações)
        if upload_anterior and upload_anterior.id != upload.id:
            logger.info(f"Limpando dados relacionados do upload anterior ID: {upload_anterior.id}")
            escolas_anteriores = escola_repo.find_by_upload_id(upload_anterior.id)
            
            from src.modules.features.calculos.repository import CalculoRepository
            from src.modules.features.complemento.repository import ComplementoEscolaRepository
            
            calculo_repo = CalculoRepository(db)
            complemento_escola_repo = ComplementoEscolaRepository(db)
            
            calculos_deletados = 0
            complementos_deletados = 0
            
            for escola_antiga in escolas_anteriores:
                # Deletar cálculos (cascade deleta parcelas automaticamente)
                calculo_existente = calculo_repo.find_by_escola_id(escola_antiga.id)
                if calculo_existente:
                    calculo_repo.delete(calculo_existente)
                    calculos_deletados += 1
                
                # Deletar complementos
                deleted = complemento_escola_repo.delete_by_escola_id(escola_antiga.id)
                complementos_deletados += deleted
            
            logger.info(f"Dados limpos: {calculos_deletados} cálculos e {complementos_deletados} complementos deletados")
            logger.info("Liberações de parcelas e projetos preservadas")
        
        # Limpar escolas de uploads não ativos (preservando apenas as que têm liberações)
        logger.info("Iniciando limpeza de escolas de uploads não ativos...")
        uploads_nao_ativos = upload_repo.find_all_by_ano_letivo(ano_letivo_id)
        uploads_nao_ativos = [u for u in uploads_nao_ativos if u.id != upload.id]
        
        escolas_deletadas_nao_ativas = 0
        escolas_preservadas_com_liberacoes = 0
        
        if uploads_nao_ativos:
            logger.info(f"Encontrados {len(uploads_nao_ativos)} upload(s) não ativo(s) para limpeza")
            
            for upload_nao_ativo in uploads_nao_ativos:
                escolas_upload_antigo = escola_repo.find_by_upload_id(upload_nao_ativo.id)
                logger.debug(f"Processando upload não ativo ID {upload_nao_ativo.id}: {len(escolas_upload_antigo)} escola(s)")
                
                for escola_antiga in escolas_upload_antigo:
                    # Verificar se tem liberações
                    tem_liberacoes = (
                        len(escola_antiga.liberacoes_parcelas) > 0 or
                        escola_antiga.liberacoes_projetos is not None
                    )
                    
                    if not tem_liberacoes:
                        # Deletar escola (cascade deleta cálculos e complementos automaticamente)
                        escola_repo.delete(escola_antiga)
                        escolas_deletadas_nao_ativas += 1
                    else:
                        escolas_preservadas_com_liberacoes += 1
                        logger.debug(f"Escola {escola_antiga.id} ({escola_antiga.nome_uex}) preservada - possui liberações")
            
            logger.info(f"Limpeza concluída: {escolas_deletadas_nao_ativas} escola(s) deletada(s), {escolas_preservadas_com_liberacoes} preservada(s) (com liberações)")
        else:
            logger.info("Nenhum upload não ativo encontrado para limpeza")
        
        mapa_escolas_existentes = escola_repo.create_map_by_nome_dre(upload.id)
        escolas_existentes = list(mapa_escolas_existentes.values())
        
        logger.info(f"Upload {'atualizado' if escolas_existentes else 'criado'} com ID: {upload.id}")
        logger.info(f"Escolas existentes no upload: {len(escolas_existentes)}")
        
        escolas_processadas = set()
        escolas_salvas = 0
        escolas_atualizadas = 0
        escolas_criadas = 0
        escolas_com_erro = []
        
        with transaction(db):
            for idx, row in df.iterrows():
                try:
                    nome_escola = (
                        row.get('NOME DA UEX') or 
                        row.get('nome') or 
                        row.get('Escola') or 
                        f"Escola {idx + 1}"
                    )
                    nome_escola = str(nome_escola).strip()
                    
                    dre_val = obter_texto(row, "DRE", None)
                    chave_escola = (nome_escola, dre_val)
                    
                    if (idx + 1) % 50 == 0 or idx == 0:
                        logger.debug(f"[{idx + 1}/{len(df)}] Processando: {nome_escola} (DRE: {dre_val or 'N/A'})")
                    
                    escola_existente = mapa_escolas_existentes.get(chave_escola)

                    codigo_ept_val = obter_texto(row, "CODIGO DE EPT", "")
                    if not codigo_ept_val:
                        codigo_ept_val = obter_texto(row, "EPT", "")
                    codigo_ept_val = codigo_ept_val or None
                    
                    if escola_existente:
                        # Atualizar escola existente
                        escola_repo.update(
                            escola_existente,
                            total_alunos=obter_quantidade(row, "TOTAL"),
                            cnpj=obter_texto(row, "CNPJ", None),
                            fundamental_inicial=obter_quantidade(row, "FUNDAMENTAL INICIAL"),
                            fundamental_final=obter_quantidade(row, "FUNDAMENTAL FINAL"),
                            fundamental_integral=obter_quantidade(row, "FUNDAMENTAL INTEGRAL"),
                            profissionalizante=obter_quantidade(row, "PROFISSIONALIZANTE"),
                            profissionalizante_integrado=obter_quantidade(row, "PROFISSIONALIZANTE INTEGRADO"), 
                            alternancia=obter_quantidade(row, "ALTERNÂNCIA"),
                            ensino_medio_integral=obter_quantidade(row, "ENSINO MÉDIO INTEGRAL"),
                            ensino_medio_regular=obter_quantidade(row, "ENSINO MÉDIO REGULAR"),
                            especial_fund_regular=obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR"),
                            especial_fund_integral=obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL"),
                            especial_medio_parcial=obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL"),
                            especial_medio_integral=obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL"),
                            sala_recurso=obter_quantidade(row, "SALA DE RECURSO"),
                            #climatizacao=obter_quantidade(row, "CLIMATIZAÇÃO"),
                            preuni=obter_quantidade(row, "PREUNI"),
                            quantidade_projetos_aprovados=obter_quantidade_projetos_aprovados(row),
                            repasse_por_area=obter_quantidade(row, "REPASSE POR AREA"),
                            indigena_quilombola=validar_indigena_e_quilombola(row, "INDIGENA & QUILOMBOLA"),
                            codigo_ept=obter_texto(row, "EPT"),
                            codigo_inep=obter_texto(row, "INEP"),
                            saldo_reprogramado_gestao=obter_valor_float(row, "SALDO GESTAO"),
                            saldo_reprogramado_merenda=obter_valor_float(row, "SALDO MERENDA"),
                        )

                        escolas_atualizadas += 1
                        escolas_processadas.add(escola_existente.id)
                    else:
                        # Criar nova escola
                        escola_obj = escola_repo.create(
                            upload_id=upload.id,
                            nome_uex=nome_escola,
                            dre=dre_val,
                            cnpj=obter_texto(row, "CNPJ", None),
                            total_alunos=obter_quantidade(row, "TOTAL"),
                            fundamental_inicial=obter_quantidade(row, "FUNDAMENTAL INICIAL"),
                            fundamental_final=obter_quantidade(row, "FUNDAMENTAL FINAL"),
                            fundamental_integral=obter_quantidade(row, "FUNDAMENTAL INTEGRAL"),
                            profissionalizante=obter_quantidade(row, "PROFISSIONALIZANTE"),
                            profissionalizante_integrado=obter_quantidade(row, "PROFISSIONALIZANTE INTEGRADO"),
                            alternancia=obter_quantidade(row, "ALTERNÂNCIA"),
                            ensino_medio_integral=obter_quantidade(row, "ENSINO MÉDIO INTEGRAL"),
                            ensino_medio_regular=obter_quantidade(row, "ENSINO MÉDIO REGULAR"),
                            especial_fund_regular=obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR"),
                            especial_fund_integral=obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL"),
                            especial_medio_parcial=obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL"),
                            especial_medio_integral=obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL"),
                            sala_recurso=obter_quantidade(row, "SALA DE RECURSO"),
                            #climatizacao=obter_quantidade(row, "CLIMATIZAÇÃO"),
                            preuni=obter_quantidade(row, "PREUNI"),
                            quantidade_projetos_aprovados=obter_quantidade_projetos_aprovados(row),
                            repasse_por_area=obter_quantidade(row, "REPASSE POR AREA"),
                            indigena_quilombola=validar_indigena_e_quilombola(row, "INDIGENA & QUILOMBOLA"),
                            codigo_ept=obter_texto(row, "EPT"),
                            codigo_inep=obter_texto(row, "INEP"),
                            saldo_reprogramado_gestao=obter_valor_float(row, "SALDO GESTAO"),
                            saldo_reprogramado_merenda=obter_valor_float(row, "SALDO MERENDA"),
                        )
                        
                        escolas_criadas += 1
                        escolas_processadas.add(escola_obj.id)
                        mapa_escolas_existentes[chave_escola] = escola_obj
                    
                    escolas_salvas += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(
                        "Erro ao processar linha %s (%s): %s",
                        idx + 1,
                        nome_escola if 'nome_escola' in locals() else 'Desconhecido',
                        error_msg,
                    )
                    escolas_com_erro.append({
                        "linha": idx + 1,
                        "nome": nome_escola if 'nome_escola' in locals() else 'Desconhecido',
                        "erro": error_msg
                    })
                    continue
            
            # Remover escolas que não estão mais no arquivo
            # IMPORTANTE: Deletar apenas se não houver liberações para preservar histórico
            escolas_para_deletar = [
                e for e in escolas_existentes 
                if e.id not in escolas_processadas
            ]
            
            escolas_removidas_count = 0
            escolas_com_liberacao_nao_deletadas = 0
            
            if escolas_para_deletar:
                for escola_para_deletar in escolas_para_deletar:
                    # Verificar se tem liberações antes de deletar
                    tem_liberacoes = (
                        len(escola_para_deletar.liberacoes_parcelas) > 0 or
                        escola_para_deletar.liberacoes_projetos is not None
                    )
                    
                    if tem_liberacoes:
                        # Preservar escola se tiver liberações (apenas limpar dados relacionados)
                        from src.modules.features.calculos.repository import CalculoRepository
                        from src.modules.features.complemento.repository import ComplementoEscolaRepository
                        
                        calculo_repo_temp = CalculoRepository(db)
                        complemento_escola_repo_temp = ComplementoEscolaRepository(db)
                        
                        # Limpar apenas cálculos e complementos, mantendo escola e liberações
                        calculo_existente = calculo_repo_temp.find_by_escola_id(escola_para_deletar.id)
                        if calculo_existente:
                            calculo_repo_temp.delete(calculo_existente)
                        
                        complemento_escola_repo_temp.delete_by_escola_id(escola_para_deletar.id)
                        
                        escolas_com_liberacao_nao_deletadas += 1
                        logger.debug(f"Escola {escola_para_deletar.id} ({escola_para_deletar.nome_uex}) preservada devido a liberações")
                    else:
                        # Deletar escola se não tiver liberações
                        escola_repo.delete(escola_para_deletar)
                        escolas_removidas_count += 1
                
                if escolas_removidas_count > 0:
                    logger.info(f"Removidas {escolas_removidas_count} escola(s) que não estão mais no arquivo")
                if escolas_com_liberacao_nao_deletadas > 0:
                    logger.info(f"Preservadas {escolas_com_liberacao_nao_deletadas} escola(s) com liberações (dados relacionados limpos)")
            
            upload_repo.update(upload, total_escolas=escolas_salvas)
        
        if escolas_atualizadas > 0:
            logger.info(f"{escolas_atualizadas} escola(s) atualizada(s) (mantendo IDs)")
        if escolas_criadas > 0:
            logger.info(f"{escolas_criadas} escola(s) criada(s) (novos IDs)")
        
        total_no_banco = escola_repo.count_by_upload_id(upload.id)
        
        logger.info("="*60)
        logger.info("UPLOAD CONCLUÍDO")
        logger.info(f"Ano letivo: {ano_letivo.ano}")
        logger.info(f"Escolas processadas: {escolas_salvas}")
        logger.info(f"  - Atualizadas: {escolas_atualizadas} (IDs mantidos)")
        logger.info(f"  - Criadas: {escolas_criadas} (novos IDs)")
        if escolas_removidas_count > 0:
            logger.info(f"  - Removidas: {escolas_removidas_count}")
        logger.info(f"Total confirmado no banco: {total_no_banco}")
        logger.warning(f"Erros: {len(escolas_com_erro)}" if escolas_com_erro else "Sem erros")
        logger.info("="*60)
        
        return {
            "upload_id": upload.id,
            "ano_letivo_id": ano_letivo_id,
            "ano_letivo": ano_letivo.ano,
            "filename": filename,
            "total_linhas": len(df),
            "escolas_salvas": escolas_salvas,
            "escolas_confirmadas_banco": total_no_banco,
            "escolas_com_erro": len(escolas_com_erro),
            "colunas": df.columns.tolist(),
            "escolas_com_erro_lista": escolas_com_erro,
            "escolas_atualizadas": escolas_atualizadas,
            "escolas_criadas": escolas_criadas,
            "escolas_removidas": escolas_removidas_count,
        }

