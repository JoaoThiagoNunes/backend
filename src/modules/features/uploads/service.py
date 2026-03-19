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
                    "fic_senac": escola.fic_senac,
                    "especial_profissionalizante_parcial": escola.especial_profissionalizante_parcial,
                    "especial_profissionalizante_integrado": escola.especial_profissionalizante_integrado,
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
        def _normalize_cnpj(value: Optional[str]) -> Optional[str]:
            if not value:
                return None
            digits = "".join(ch for ch in str(value) if ch.isdigit())
            return digits or None

        ano_letivo, ano_letivo_id = obter_ano_letivo(db, ano_letivo_id)
        logger.info(f"UPLOAD PARA ANO LETIVO: {ano_letivo.ano} (Status: {ano_letivo.status.value})")
        
        if filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(file_contents))
        else:
            df = pd.read_excel(BytesIO(file_contents))
        
        logger.info(f"Arquivo: {filename}")
        logger.info(f"Total de linhas: {len(df)}")
        logger.debug(f"Colunas: {df.columns.tolist()}")

        # Obter/criar upload do ano letivo (substitui mantendo 1 upload por ano)
        upload = obter_ou_criar_upload_ativo(db, ano_letivo_id, filename)
        db.flush()
        db.refresh(upload)

        escola_repo = EscolaRepository(db)

        # Mapas de escolas existentes no upload atual:
        # - Preferir CNPJ normalizado
        # - Fallback para (nome_uex, dre)
        escolas_existentes = escola_repo.find_by_upload_id(upload.id)
        mapa_por_cnpj = {}
        mapa_por_nome_dre = {}
        for e in escolas_existentes:
            cnpj_norm = _normalize_cnpj(e.cnpj)
            if cnpj_norm:
                mapa_por_cnpj[cnpj_norm] = e
            mapa_por_nome_dre[(e.nome_uex, e.dre)] = e

        logger.info(f"Upload do ano letivo {ano_letivo.ano} com ID: {upload.id}")
        logger.info(f"Escolas existentes no upload: {len(escolas_existentes)}")
        
        escolas_processadas = set()
        escolas_salvas = 0
        escolas_atualizadas = 0
        escolas_criadas = 0
        escolas_com_erro = []

        # Repositórios para limpar dados recalculáveis (sem tocar liberações)
        from src.modules.features.calculos.repository import CalculoRepository
        from src.modules.features.complemento.repository import ComplementoEscolaRepository
        calculo_repo = CalculoRepository(db)
        complemento_escola_repo = ComplementoEscolaRepository(db)
        
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
                    cnpj_raw = obter_texto(row, "CNPJ", None)
                    cnpj_norm = _normalize_cnpj(cnpj_raw)
                    chave_nome_dre = (nome_escola, dre_val)
                    
                    if (idx + 1) % 50 == 0 or idx == 0:
                        logger.debug(f"[{idx + 1}/{len(df)}] Processando: {nome_escola} (DRE: {dre_val or 'N/A'})")
                    
                    escola_existente = None
                    if cnpj_norm:
                        escola_existente = mapa_por_cnpj.get(cnpj_norm)
                    if not escola_existente:
                        escola_existente = mapa_por_nome_dre.get(chave_nome_dre)

                    codigo_ept_val = obter_texto(row, "CODIGO DE EPT", "")
                    if not codigo_ept_val:
                        codigo_ept_val = obter_texto(row, "EPT", "")
                    codigo_ept_val = codigo_ept_val or None
                    
                    if escola_existente:
                        # Atualizar escola existente
                        escola_repo.update(
                            escola_existente,
                            total_alunos=obter_quantidade(row, "TOTAL"),
                            cnpj=cnpj_raw,
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
                            fic_senac=obter_quantidade(row, "FIC SENAC"),
                            especial_profissionalizante_parcial=obter_quantidade(row, "ESPECIAL PROFISSIONALIZANTE PARCIAL"),
                            especial_profissionalizante_integrado=obter_quantidade(row, "ESPECIAL PROFISSIONALIZANTE INTEGRADO"),
                        )

                        escolas_atualizadas += 1
                        escolas_processadas.add(escola_existente.id)

                        # Limpar dados recalculáveis do fluxo base (mantém liberações).
                        # IMPORTANTE: não tocar dados de complemento aqui — complemento só muda
                        # quando o usuário envia explicitamente um upload de complemento.
                        calculo_existente = calculo_repo.find_by_escola_id(escola_existente.id)
                        if calculo_existente:
                            calculo_repo.delete(calculo_existente)
                    else:
                        # Criar nova escola
                        escola_obj = escola_repo.create(
                            upload_id=upload.id,
                            nome_uex=nome_escola,
                            dre=dre_val,
                            cnpj=cnpj_raw,
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
                            fic_senac=obter_quantidade(row, "FIC SENAC"),
                            especial_profissionalizante_parcial=obter_quantidade(row, "ESPECIAL PROFISSIONALIZANTE PARCIAL"),
                            especial_profissionalizante_integrado=obter_quantidade(row, "ESPECIAL PROFISSIONALIZANTE INTEGRADO"),
                        )
                        
                        escolas_criadas += 1
                        escolas_processadas.add(escola_obj.id)
                        if cnpj_norm:
                            mapa_por_cnpj[cnpj_norm] = escola_obj
                        mapa_por_nome_dre[chave_nome_dre] = escola_obj
                    
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

            # Deduplicação por CNPJ no mesmo upload:
            # Como não deletamos escolas ausentes da planilha, podem existir "sobras históricas" com o mesmo CNPJ.
            # Para manter consistência (1 escola por CNPJ), fazemos merge conservador de liberações e removemos duplicatas.

            # Buscar escolas do upload e agrupar por CNPJ normalizado
            escolas_upload = escola_repo.find_by_upload_id(upload.id)
            by_cnpj: Dict[str, List[Any]] = {}
            for e in escolas_upload:
                cnpj_norm = _normalize_cnpj(e.cnpj)
                if not cnpj_norm:
                    continue
                by_cnpj.setdefault(cnpj_norm, []).append(e)

            dup_groups = {k: v for k, v in by_cnpj.items() if len(v) > 1}
            if dup_groups:
                logger.warning(
                    "Detectadas %s duplicidade(s) por CNPJ no upload_id=%s. Iniciando merge.",
                    len(dup_groups),
                    upload.id,
                )

            if dup_groups:
                from src.modules.features.parcelas.models import LiberacoesParcela
                from src.modules.features.projetos.models import LiberacoesProjeto
                from src.modules.features.complemento.models import LiberacoesComplemento
                from src.modules.features.escolas.models import Escola as EscolaModel

                merged_dups = 0
                for cnpj_norm, escolas in dup_groups.items():
                    # Escolher canônica: a que tiver liberações; senão, a de menor id
                    escolas_sorted = sorted(escolas, key=lambda x: x.id)
                    canon = None
                    for cand in escolas_sorted:
                        has_rel = (
                            (cand.liberacoes_projetos is not None)
                            or (cand.liberacoes_parcelas and len(cand.liberacoes_parcelas) > 0)
                            or (cand.liberacoes_complementos and len(cand.liberacoes_complementos) > 0)
                        )
                        if has_rel:
                            canon = cand
                            break
                    canon = canon or escolas_sorted[0]

                    for dup in escolas_sorted:
                        if dup.id == canon.id:
                            continue

                        # Migrar liberações parcelas
                        for lp in db.query(LiberacoesParcela).filter(LiberacoesParcela.escola_id == dup.id).all():
                            existing = (
                                db.query(LiberacoesParcela)
                                .filter(
                                    LiberacoesParcela.escola_id == canon.id,
                                    LiberacoesParcela.numero_parcela == lp.numero_parcela,
                                )
                                .first()
                            )
                            if existing:
                                existing.liberada = bool(existing.liberada or lp.liberada)
                                if existing.numero_folha is None and lp.numero_folha is not None:
                                    existing.numero_folha = lp.numero_folha
                                if existing.data_liberacao is None and lp.data_liberacao is not None:
                                    existing.data_liberacao = lp.data_liberacao
                                if getattr(lp, "valor_projetos_aprovados", 0.0) > getattr(existing, "valor_projetos_aprovados", 0.0):
                                    existing.valor_projetos_aprovados = lp.valor_projetos_aprovados
                                db.delete(lp)
                            else:
                                lp.escola_id = canon.id

                        # Migrar liberação projeto
                        dp = db.query(LiberacoesProjeto).filter(LiberacoesProjeto.escola_id == dup.id).first()
                        if dp:
                            cp = db.query(LiberacoesProjeto).filter(LiberacoesProjeto.escola_id == canon.id).first()
                            if cp:
                                cp.liberada = bool(cp.liberada or dp.liberada)
                                if cp.numero_folha is None and dp.numero_folha is not None:
                                    cp.numero_folha = dp.numero_folha
                                if cp.data_liberacao is None and dp.data_liberacao is not None:
                                    cp.data_liberacao = dp.data_liberacao
                                if dp.valor_projetos_aprovados > cp.valor_projetos_aprovados:
                                    cp.valor_projetos_aprovados = dp.valor_projetos_aprovados
                                db.delete(dp)
                            else:
                                dp.escola_id = canon.id

                        # Migrar liberações complemento
                        for lc in db.query(LiberacoesComplemento).filter(LiberacoesComplemento.escola_id == dup.id).all():
                            exists_lc = (
                                db.query(LiberacoesComplemento)
                                .filter(
                                    LiberacoesComplemento.escola_id == canon.id,
                                    LiberacoesComplemento.complemento_upload_id == lc.complemento_upload_id,
                                )
                                .first()
                            )
                            if exists_lc:
                                exists_lc.liberada = bool(exists_lc.liberada or lc.liberada)
                                if exists_lc.numero_folha is None and lc.numero_folha is not None:
                                    exists_lc.numero_folha = lc.numero_folha
                                if exists_lc.data_liberacao is None and lc.data_liberacao is not None:
                                    exists_lc.data_liberacao = lc.data_liberacao
                                db.delete(lc)
                            else:
                                lc.escola_id = canon.id

                        db.flush()
                        # Bulk delete escola duplicada para evitar nullify de FKs NOT NULL
                        db.query(EscolaModel).filter(EscolaModel.id == dup.id).delete(synchronize_session=False)
                        merged_dups += 1

                logger.info(
                    "Deduplicação por CNPJ concluída (upload_id=%s, merged_dups=%s)",
                    upload.id,
                    merged_dups,
                )

            # Importante (requisito): NÃO deletar escolas ausentes do arquivo no mesmo ano letivo.
            # Mantemos escolas (e suas liberações) mesmo que não venham na nova planilha.
            upload_repo = UploadRepository(db)
            upload_repo.update(upload, total_escolas=escola_repo.count_by_upload_id(upload.id))
        
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
            "escolas_removidas": 0,
        }

