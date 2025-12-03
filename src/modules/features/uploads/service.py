from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from io import BytesIO
import pandas as pd
from src.core.logging_config import logger
from src.core.database import transaction
from src.core.exceptions import UploadNaoEncontradoException
from src.modules.features.uploads.repository import UploadRepository
from src.modules.features.escolas.repository import EscolaRepository
from src.modules.schemas.upload import UploadListItem, UploadDetailInfo, EscolaPlanilhaInfo
from src.core.utils import (
    obter_ano_letivo,
    obter_texto,
    obter_quantidade,
    validar_indigena_e_quilombola,
)
from src.modules.features.uploads.utils import obter_ou_criar_upload_ativo
from src.modules.features.projetos.utils import obter_quantidade_projetos_aprovados


class UploadService:
    @staticmethod
    def obter_upload_unico(db: Session, ano_letivo_id: Optional[int] = None) -> UploadListItem:
        repo = UploadRepository(db)
        upload = repo.find_latest(ano_letivo_id)
        
        if not upload:
            raise UploadNaoEncontradoException(ano_letivo_id=ano_letivo_id)

        return UploadListItem(
            success=True,
            id=upload.id,
            ano_letivo_id=upload.ano_letivo_id,
            ano_letivo=upload.ano_letivo.ano,
            filename=upload.filename,
            upload_date=upload.upload_date,
            total_escolas=upload.total_escolas,
            is_active=upload.is_active
        )
    
    @staticmethod
    def obter_upload_detalhado(db: Session, ano_letivo_id: Optional[int] = None) -> Dict[str, Any]:
        _, ano_id = obter_ano_letivo(db, ano_letivo_id)
        
        upload_repo = UploadRepository(db)
        upload = upload_repo.find_by_ano_letivo(ano_id)
        if not upload:
            raise UploadNaoEncontradoException(ano_letivo_id=ano_id)
        
        escola_repo = EscolaRepository(db)
        escolas = escola_repo.find_by_upload_id(upload.id)
        escolas_planilha: List[EscolaPlanilhaInfo] = []

        for escola in escolas:
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
                "alternancia": escola.alternancia,
                "ensino_medio_integral": escola.ensino_medio_integral,
                "ensino_medio_regular": escola.ensino_medio_regular,
                "especial_fund_regular": escola.especial_fund_regular,
                "especial_fund_integral": escola.especial_fund_integral,
                "especial_medio_parcial": escola.especial_medio_parcial,
                "especial_medio_integral": escola.especial_medio_integral,
                "sala_recurso": escola.sala_recurso,
                "climatizacao": escola.climatizacao,
                "preuni": escola.preuni,
                "quantidade_projetos_aprovados": escola.quantidade_projetos_aprovados,
                "repasse_por_area": escola.repasse_por_area,
                "indigena_quilombola": escola.indigena_quilombola,
                "estado_liberacao": escola.estado_liberacao,
                "numeracao_folha": escola.numeracao_folha,
                "created_at": escola.created_at,
            }

            escolas_planilha.append(EscolaPlanilhaInfo(dados_planilha=dados_escola))

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
        
        logger.info("="*60)
        logger.info(f"UPLOAD PARA ANO LETIVO: {ano_letivo.ano} (Status: {ano_letivo.status.value})")
        logger.info("="*60)
        
        # Ler arquivo
        if filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(file_contents))
        else:
            df = pd.read_excel(BytesIO(file_contents))
        
        logger.info(f"Arquivo: {filename}")
        logger.info(f"Total de linhas: {len(df)}")
        logger.debug(f"Colunas: {df.columns.tolist()}")
        
        # Obter ou criar upload
        upload = obter_ou_criar_upload_ativo(db, ano_letivo_id, filename)
        db.flush()
        db.refresh(upload)
        
        # Processar escolas
        escola_repo = EscolaRepository(db)
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
                        alternancia=obter_quantidade(row, "ALTERNÂNCIA"),
                        ensino_medio_integral=obter_quantidade(row, "ENSINO MÉDIO INTEGRAL"),
                        ensino_medio_regular=obter_quantidade(row, "ENSINO MÉDIO REGULAR"),
                        especial_fund_regular=obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR"),
                        especial_fund_integral=obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL"),
                        especial_medio_parcial=obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL"),
                        especial_medio_integral=obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL"),
                        sala_recurso=obter_quantidade(row, "SALA DE RECURSO"),
                        climatizacao=obter_quantidade(row, "CLIMATIZAÇÃO"),
                        preuni=obter_quantidade(row, "PREUNI"),
                        quantidade_projetos_aprovados=obter_quantidade_projetos_aprovados(row),
                        repasse_por_area=obter_quantidade(row, "REPASSE POR AREA"),
                        indigena_quilombola=validar_indigena_e_quilombola(row, "INDIGENA & QUILOMBOLA")
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
                        alternancia=obter_quantidade(row, "ALTERNÂNCIA"),
                        ensino_medio_integral=obter_quantidade(row, "ENSINO MÉDIO INTEGRAL"),
                        ensino_medio_regular=obter_quantidade(row, "ENSINO MÉDIO REGULAR"),
                        especial_fund_regular=obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR"),
                        especial_fund_integral=obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL"),
                        especial_medio_parcial=obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL"),
                        especial_medio_integral=obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL"),
                        sala_recurso=obter_quantidade(row, "SALA DE RECURSO"),
                        climatizacao=obter_quantidade(row, "CLIMATIZAÇÃO"),
                        preuni=obter_quantidade(row, "PREUNI"),
                        quantidade_projetos_aprovados=obter_quantidade_projetos_aprovados(row),
                        repasse_por_area=obter_quantidade(row, "REPASSE POR AREA"),
                        indigena_quilombola=validar_indigena_e_quilombola(row, "INDIGENA & QUILOMBOLA")
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
            escolas_para_deletar = [
                e for e in escolas_existentes 
                if e.id not in escolas_processadas
            ]
            
            escolas_removidas_count = 0
            if escolas_para_deletar:
                for escola_para_deletar in escolas_para_deletar:
                    escola_repo.delete(escola_para_deletar)
                    escolas_removidas_count += 1
                logger.info(f"Removidas {escolas_removidas_count} escola(s) que não estão mais no arquivo")
            
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

