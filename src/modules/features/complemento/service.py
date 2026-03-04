from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from io import BytesIO
from datetime import datetime
import pandas as pd
from src.core.logging_config import logger
from src.core.database import transaction
from src.core.exceptions import UploadNaoEncontradoException
from src.modules.features.anos import obter_ano_letivo
from src.modules.features.uploads import UploadService
from src.modules.features.uploads.repository import UploadRepository
from src.modules.features.escolas.repository import EscolaRepository
from .repository import ComplementoUploadRepository, ComplementoEscolaRepository
from .models import ComplementoUpload, ComplementoEscola, StatusComplemento
from .utils import comparar_quantidades, calcular_complemento_valores
from src.modules.shared.utils import obter_texto, obter_quantidade


class ComplementoService:
    @staticmethod
    def obter_upload_base(
        db: Session,
        ano_letivo_id: Optional[int] = None,
        upload_base_id: Optional[int] = None
    ):
        if upload_base_id:
            upload_repo = UploadRepository(db)
            upload = upload_repo.find_by_id(upload_base_id)
            if not upload:
                raise UploadNaoEncontradoException(upload_id=upload_base_id)
            return upload
        
        # Buscar upload ativo
        _, ano_id = obter_ano_letivo(db, ano_letivo_id)
        upload_list_item = UploadService.obter_upload_unico(db, ano_id)

    
        
        upload_repo = UploadRepository(db)
        return upload_repo.find_by_id(upload_list_item.id)
    
    @staticmethod
    def processar_planilha_complemento(
        db: Session,
        file_contents: bytes,
        filename: str,
        ano_letivo_id: Optional[int] = None,
        upload_base_id: Optional[int] = None
    ) -> Dict[str, Any]:
        ano_letivo, ano_id = obter_ano_letivo(db, ano_letivo_id)
        logger.info(f"PROCESSANDO COMPLEMENTO PARA ANO LETIVO: {ano_letivo.ano}")
        
        # 1. Obter upload base
        upload_base = ComplementoService.obter_upload_base(db, ano_id, upload_base_id)
        logger.info(f"Upload base ID: {upload_base.id}, Filename: {upload_base.filename}")
        
        # 2. Processar planilha complementar
        if filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(file_contents))
        else:
            df = pd.read_excel(BytesIO(file_contents))
        
        logger.info(f"Planilha complementar: {filename}, Total de linhas: {len(df)}")
        
        # 3. Criar upload temporário para planilha complementar (sem ativar no contexto)
        upload_repo = UploadRepository(db)
        upload_complemento = upload_repo.create(
            ano_letivo_id=ano_id,
            filename=f"complemento_{filename}",
            total_escolas=0,
            upload_date=datetime.now()
        )
        db.flush()
        
        # 4. Obter escolas do upload base
        escola_repo = EscolaRepository(db)
        escolas_base = escola_repo.find_by_upload_id(upload_base.id)
        mapa_escolas_base = {
            (e.nome_uex.strip().upper(), (e.dre or "").strip().upper()): e
            for e in escolas_base
        }
        
        logger.info(f"Escolas no upload base: {len(escolas_base)}")
        
        # 5. Processar comparações
        complemento_repo = ComplementoUploadRepository(db)
        complemento_escola_repo = ComplementoEscolaRepository(db)
        
        resultados = []
        escolas_com_aumento = 0
        escolas_sem_mudanca = 0
        escolas_com_diminuicao = 0
        escolas_com_erro = 0
        valor_total_complemento = 0.0
        
        with transaction(db):
            # Criar registro de ComplementoUpload
            complemento_upload = complemento_repo.create(
                ano_letivo_id=ano_id,
                upload_base_id=upload_base.id,
                upload_complemento_id=upload_complemento.id,
                filename=filename,
                total_escolas_processadas=0,
                escolas_com_aumento=0,
                escolas_sem_mudanca=0,
                escolas_com_diminuicao=0,
                escolas_com_erro=0
            )
            db.flush()
            
            # Processar cada linha da planilha complementar
            for idx, row in df.iterrows():
                try:
                    nome_escola = (
                        row.get('NOME DA UEX') or 
                        row.get('nome') or 
                        row.get('Escola') or 
                        f"Escola {idx + 1}"
                    )
                    nome_escola = str(nome_escola).strip()
                    dre_val = obter_texto(row, "DRE", None) or ""
                    dre_val = dre_val.strip()
                    
                    chave_escola = (nome_escola.upper(), dre_val.upper())
                    escola_base = mapa_escolas_base.get(chave_escola)
                    
                    if not escola_base:
                        logger.warning(f"Escola não encontrada: {nome_escola} (DRE: {dre_val})")
                        escolas_com_erro += 1
                        continue
                    
                    # Extrair dados do complemento
                    dados_complemento = {
                        'TOTAL': obter_quantidade(row, "TOTAL"),
                        'FUNDAMENTAL INICIAL': obter_quantidade(row, "FUNDAMENTAL INICIAL"),
                        'FUNDAMENTAL FINAL': obter_quantidade(row, "FUNDAMENTAL FINAL"),
                        'FUNDAMENTAL INTEGRAL': obter_quantidade(row, "FUNDAMENTAL INTEGRAL"),
                        'PROFISSIONALIZANTE': obter_quantidade(row, "PROFISSIONALIZANTE"),
                        'PROFISSIONALIZANTE INTEGRADO': obter_quantidade(row, "PROFISSIONALIZANTE INTEGRADO"),
                        'ALTERNÂNCIA': obter_quantidade(row, "ALTERNÂNCIA"),
                        'ENSINO MÉDIO INTEGRAL': obter_quantidade(row, "ENSINO MÉDIO INTEGRAL"),
                        'ENSINO MÉDIO REGULAR': obter_quantidade(row, "ENSINO MÉDIO REGULAR"),
                        'ESPECIAL FUNDAMENTAL REGULAR': obter_quantidade(row, "ESPECIAL FUNDAMENTAL REGULAR"),
                        'ESPECIAL FUNDAMENTAL INTEGRAL': obter_quantidade(row, "ESPECIAL FUNDAMENTAL INTEGRAL"),
                        'ESPECIAL MÉDIO PARCIAL': obter_quantidade(row, "ESPECIAL MÉDIO PARCIAL"),
                        'ESPECIAL MÉDIO INTEGRAL': obter_quantidade(row, "ESPECIAL MÉDIO INTEGRAL"),
                        'SALA DE RECURSO': obter_quantidade(row, "SALA DE RECURSO"),
                        'PREUNI': obter_quantidade(row, "PREUNI"),
                    }
                    
                    # Comparar quantidades
                    comparacao = comparar_quantidades(escola_base, dados_complemento)
                    status = comparacao['status']
                    
                    # Calcular valores se houver aumento
                    valores_complemento = {}
                    if status == StatusComplemento.AUMENTO:
                        valores_complemento = calcular_complemento_valores(comparacao['diferencas'])
                        valor_total_complemento += valores_complemento.get('valor_total', 0.0)
                        escolas_com_aumento += 1
                    elif status == StatusComplemento.SEM_MUDANCA:
                        escolas_sem_mudanca += 1
                    elif status == StatusComplemento.DIMINUICAO:
                        escolas_com_diminuicao += 1
                    
                    # Criar ComplementoEscola
                    diferencas = comparacao['diferencas']
                    quantidades_antes = comparacao['quantidades_antes']
                    quantidades_depois = comparacao['quantidades_depois']
                    
                    complemento_escola = complemento_escola_repo.create(
                        complemento_upload_id=complemento_upload.id,
                        escola_id=escola_base.id,
                        # Quantidades antes
                        total_alunos_antes=quantidades_antes['total_alunos'],
                        fundamental_inicial_antes=quantidades_antes['fundamental_inicial'],
                        fundamental_final_antes=quantidades_antes['fundamental_final'],
                        fundamental_integral_antes=quantidades_antes['fundamental_integral'],
                        profissionalizante_antes=quantidades_antes['profissionalizante'],
                        profissionalizante_integrado_antes=quantidades_antes['profissionalizante_integrado'],
                        alternancia_antes=quantidades_antes['alternancia'],
                        ensino_medio_integral_antes=quantidades_antes['ensino_medio_integral'],
                        ensino_medio_regular_antes=quantidades_antes['ensino_medio_regular'],
                        especial_fund_regular_antes=quantidades_antes['especial_fund_regular'],
                        especial_fund_integral_antes=quantidades_antes['especial_fund_integral'],
                        especial_medio_parcial_antes=quantidades_antes['especial_medio_parcial'],
                        especial_medio_integral_antes=quantidades_antes['especial_medio_integral'],
                        sala_recurso_antes=quantidades_antes['sala_recurso'],
                        preuni_antes=quantidades_antes['preuni'],
                        # Quantidades depois
                        total_alunos_depois=quantidades_depois['total_alunos'],
                        fundamental_inicial_depois=quantidades_depois['fundamental_inicial'],
                        fundamental_final_depois=quantidades_depois['fundamental_final'],
                        fundamental_integral_depois=quantidades_depois['fundamental_integral'],
                        profissionalizante_depois=quantidades_depois['profissionalizante'],
                        profissionalizante_integrado_depois=quantidades_depois['profissionalizante_integrado'],
                        alternancia_depois=quantidades_depois['alternancia'],
                        ensino_medio_integral_depois=quantidades_depois['ensino_medio_integral'],
                        ensino_medio_regular_depois=quantidades_depois['ensino_medio_regular'],
                        especial_fund_regular_depois=quantidades_depois['especial_fund_regular'],
                        especial_fund_integral_depois=quantidades_depois['especial_fund_integral'],
                        especial_medio_parcial_depois=quantidades_depois['especial_medio_parcial'],
                        especial_medio_integral_depois=quantidades_depois['especial_medio_integral'],
                        sala_recurso_depois=quantidades_depois['sala_recurso'],
                        preuni_depois=quantidades_depois['preuni'],
                        # Diferenças (apenas positivas para cálculo)
                        total_alunos_diferenca=max(0, diferencas['total_alunos']),
                        fundamental_inicial_diferenca=max(0, diferencas['fundamental_inicial']),
                        fundamental_final_diferenca=max(0, diferencas['fundamental_final']),
                        fundamental_integral_diferenca=max(0, diferencas['fundamental_integral']),
                        profissionalizante_diferenca=max(0, diferencas['profissionalizante']),
                        profissionalizante_integrado_diferenca=max(0, diferencas['profissionalizante_integrado']),
                        alternancia_diferenca=max(0, diferencas['alternancia']),
                        ensino_medio_integral_diferenca=max(0, diferencas['ensino_medio_integral']),
                        ensino_medio_regular_diferenca=max(0, diferencas['ensino_medio_regular']),
                        especial_fund_regular_diferenca=max(0, diferencas['especial_fund_regular']),
                        especial_fund_integral_diferenca=max(0, diferencas['especial_fund_integral']),
                        especial_medio_parcial_diferenca=max(0, diferencas['especial_medio_parcial']),
                        especial_medio_integral_diferenca=max(0, diferencas['especial_medio_integral']),
                        sala_recurso_diferenca=max(0, diferencas['sala_recurso']),
                        preuni_diferenca=max(0, diferencas['preuni']),
                        # Status e valores
                        status=status,
                        valor_complemento_gestao=valores_complemento.get('profin_gestao', 0.0),
                        valor_complemento_projeto=valores_complemento.get('profin_projeto', 0.0),
                        valor_complemento_kit_escolar=valores_complemento.get('profin_kit_escolar', 0.0),
                        valor_complemento_uniforme=valores_complemento.get('profin_uniforme', 0.0),
                        valor_complemento_merenda=valores_complemento.get('profin_merenda', 0.0),
                        valor_complemento_sala_recurso=valores_complemento.get('profin_sala_recurso', 0.0),
                        valor_complemento_preuni=valores_complemento.get('profin_preuni', 0.0),
                        valor_complemento_total=valores_complemento.get('valor_total', 0.0),
                    )
                    
                    resultados.append({
                        'escola_id': escola_base.id,
                        'nome_uex': escola_base.nome_uex,
                        'status': status.value,
                        'valor_complemento_total': valores_complemento.get('valor_total', 0.0)
                    })
                    
                except Exception as e:
                    logger.error(f"Erro ao processar linha {idx + 1}: {str(e)}")
                    escolas_com_erro += 1
                    continue
            
            # Atualizar estatísticas do ComplementoUpload
            total_processadas = len(resultados) + escolas_com_erro
            complemento_repo.update(
                complemento_upload,
                total_escolas_processadas=total_processadas,
                escolas_com_aumento=escolas_com_aumento,
                escolas_sem_mudanca=escolas_sem_mudanca,
                escolas_com_diminuicao=escolas_com_diminuicao,
                escolas_com_erro=escolas_com_erro
            )
        
        logger.info("="*60)
        logger.info("COMPLEMENTO PROCESSADO")
        logger.info(f"Total processadas: {total_processadas}")
        logger.info(f"  - Com aumento: {escolas_com_aumento}")
        logger.info(f"  - Sem mudança: {escolas_sem_mudanca}")
        logger.info(f"  - Com diminuição: {escolas_com_diminuicao}")
        logger.info(f"  - Com erro: {escolas_com_erro}")
        logger.info(f"Valor total complemento: R$ {valor_total_complemento:,.2f}")
        logger.info("="*60)
        
        return {
            "complemento_upload_id": complemento_upload.id,
            "ano_letivo_id": ano_id,
            "ano_letivo": ano_letivo.ano,
            "filename": filename,
            "total_escolas_processadas": total_processadas,
            "escolas_com_aumento": escolas_com_aumento,
            "escolas_sem_mudanca": escolas_sem_mudanca,
            "escolas_com_diminuicao": escolas_com_diminuicao,
            "escolas_com_erro": escolas_com_erro,
            "valor_complemento_total": valor_total_complemento,
            "resultados": resultados
        }
