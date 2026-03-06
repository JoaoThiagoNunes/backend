from sqlalchemy.orm import Session, joinedload
from typing import Optional, Dict, Any, List
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
from .repository import ComplementoUploadRepository, ComplementoEscolaRepository, LiberacaoComplementoRepository
from .models import ComplementoUpload, ComplementoEscola, StatusComplemento, LiberacoesComplemento
from .utils import comparar_quantidades, calcular_complemento_valores
from src.modules.shared.utils import obter_texto, obter_quantidade
from src.modules.schemas.complemento import (
    LiberacaoComplementoInfo,
    ComplementoEscolaPrevisaoInfo,
    ComplementoFolhaInfo
)


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
            # Deletar TODOS os ComplementoUpload existentes para este ano_letivo
            # Isso garante substituição completa - a cada nova inserção, remove todos os anteriores do ano
            deleted_count = complemento_repo.delete_all_by_ano_letivo(ano_id)
            
            if deleted_count > 0:
                logger.info(
                    f"{deleted_count} ComplementoUpload(s) existente(s) deletado(s) "
                    f"para ano_letivo_id={ano_id}. "
                    f"Substituindo por novo processamento."
                )
                # O cascade definido no modelo já deleta automaticamente os ComplementoEscola relacionados
                db.flush()  # Garantir que a deleção foi commitada antes de criar novo
            
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
            
            # Set para rastrear escolas já processadas neste complemento (evitar duplicatas)
            escolas_processadas = set()
            
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
                    
                    # Verificar se esta escola já foi processada neste complemento
                    if escola_base.id in escolas_processadas:
                        logger.warning(
                            f"Escola duplicada na planilha ignorada: {nome_escola} (ID: {escola_base.id}, DRE: {dre_val}). "
                            f"Usando apenas o primeiro registro."
                        )
                        continue
                    
                    # Marcar escola como processada
                    escolas_processadas.add(escola_base.id)
                    
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
    @staticmethod
    def mapear_liberacao_complemento(liberacao: LiberacoesComplemento) -> LiberacaoComplementoInfo:
        """Mapeia uma liberação de complemento para o schema de resposta."""
        escola = liberacao.escola
        
        return LiberacaoComplementoInfo(
            id=liberacao.id,
            escola_id=escola.id if escola else liberacao.escola_id,
            nome_uex=escola.nome_uex if escola else "",
            dre=escola.dre if escola else None,
            complemento_upload_id=liberacao.complemento_upload_id,
            liberada=liberacao.liberada,
            numero_folha=liberacao.numero_folha,
            data_liberacao=liberacao.data_liberacao,
            created_at=liberacao.created_at,
            updated_at=liberacao.updated_at
        )
    
    @staticmethod
    def liberar_escolas_complemento(
        db: Session,
        escola_ids: List[int],
        numero_folha: int,
        complemento_upload_id: Optional[int] = None,
        ano_letivo_id: Optional[int] = None
    ) -> List[LiberacoesComplemento]:
        """Libera escolas para uma folha de complemento."""
        if not escola_ids:
            raise ValueError("Informe ao menos uma escola para liberar")
        
        if numero_folha <= 0:
            raise ValueError("numero_folha deve ser um inteiro maior ou igual a 1")
        
        # Se não informado complemento_upload_id, buscar o mais recente
        if complemento_upload_id is None:
            _, ano_id = obter_ano_letivo(db, ano_letivo_id)
            complemento_repo = ComplementoUploadRepository(db)
            complemento_upload_recente = complemento_repo.find_mais_recente_by_ano_letivo(ano_id)
            if complemento_upload_recente:
                complemento_upload_id = complemento_upload_recente.id
        
        escola_ids_unicos = list(dict.fromkeys(escola_ids))
        
        escola_repo = EscolaRepository(db)
        escolas = escola_repo.find_by_ids(escola_ids_unicos)
        
        if len(escolas) != len(escola_ids_unicos):
            ids_encontrados = {escola.id for escola in escolas}
            ids_invalidos = [eid for eid in escola_ids_unicos if eid not in ids_encontrados]
            raise ValueError(f"Escolas não encontradas: {ids_invalidos}")
        
        liberacao_repo = LiberacaoComplementoRepository(db)
        liberacoes_existentes = liberacao_repo.find_by_escolas_ids(escola_ids_unicos, complemento_upload_id)
        
        mapa_liberacoes: Dict[int, LiberacoesComplemento] = {
            liberacao.escola_id: liberacao for liberacao in liberacoes_existentes
        }
        
        agora = datetime.now()
        liberacoes_resultado: List[LiberacoesComplemento] = []
        
        with transaction(db):
            for escola in escolas:
                liberacao = mapa_liberacoes.get(escola.id)
                
                if liberacao:
                    liberacao.liberada = True
                    liberacao.numero_folha = numero_folha
                    liberacao.data_liberacao = agora
                else:
                    liberacao = LiberacoesComplemento(
                        escola_id=escola.id,
                        complemento_upload_id=complemento_upload_id,
                        liberada=True,
                        numero_folha=numero_folha,
                        data_liberacao=agora
                    )
                    db.add(liberacao)
                    mapa_liberacoes[escola.id] = liberacao
                
                liberacao.escola = escola
                liberacoes_resultado.append(liberacao)
        
        return liberacoes_resultado
    
    @staticmethod
    def obter_complementos_agrupados(
        db: Session,
        ano_letivo_id: Optional[int] = None,
        complemento_upload_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtém resumo de complementos agrupados por folhas."""
        from src.modules.features.uploads.repository import ContextoAtivoRepository
        
        _, ano_id = obter_ano_letivo(db, ano_letivo_id)
        
        # Se não informado complemento_upload_id, buscar o mais recente
        if complemento_upload_id is None:
            complemento_repo = ComplementoUploadRepository(db)
            complemento_upload_recente = complemento_repo.find_mais_recente_by_ano_letivo(ano_id)
            if complemento_upload_recente:
                complemento_upload_id = complemento_upload_recente.id
        
        # Buscar upload ativo para filtrar escolas
        contexto_repo = ContextoAtivoRepository(db)
        upload_ativo = contexto_repo.find_upload_ativo(ano_id)
        
        if not upload_ativo:
            return {
                "success": True,
                "total_folhas": 0,
                "total_escolas": 0,
                "valor_total_reais": 0.0,
                "folhas": []
            }
        
        # Buscar escolas do upload ativo que têm complemento
        escola_repo = EscolaRepository(db)
        escolas = escola_repo.find_by_upload_id(upload_ativo.id)
        
        # Buscar complementos das escolas
        complemento_escola_repo = ComplementoEscolaRepository(db)
        liberacao_repo = LiberacaoComplementoRepository(db)
        
        # Filtrar por complemento_upload_id se fornecido
        if complemento_upload_id:
            complementos_escola = complemento_escola_repo.find_by_complemento_upload(complemento_upload_id)
            escola_ids_com_complemento = {ce.escola_id for ce in complementos_escola}
            escolas = [e for e in escolas if e.id in escola_ids_com_complemento]
        
        # Buscar liberações
        liberacoes = liberacao_repo.find_liberadas(complemento_upload_id=complemento_upload_id)
        mapa_liberacoes: Dict[int, LiberacoesComplemento] = {
            lib.escola_id: lib for lib in liberacoes
        }
        
        # Agrupar por folha
        agrupado: Dict[Optional[int], List[Dict[str, Any]]] = {}
        escolas_por_folha: Dict[Optional[int], set] = {}
        
        for escola in escolas:
            # Buscar complemento da escola
            complementos = complemento_escola_repo.find_by_escola(escola.id)
            if complemento_upload_id:
                complementos = [c for c in complementos if c.complemento_upload_id == complemento_upload_id]
            
            if not complementos:
                continue
            
            # Usar o complemento mais recente
            complemento = complementos[0]
            
            # Verificar se escola tem liberação
            liberacao = mapa_liberacoes.get(escola.id)
            
            if liberacao:
                folha = liberacao.numero_folha
                liberada = liberacao.liberada
            else:
                folha = None
                liberada = False
            
            if folha not in agrupado:
                agrupado[folha] = []
                escolas_por_folha[folha] = set()
            
            if escola.id in escolas_por_folha[folha]:
                continue
            
            escolas_por_folha[folha].add(escola.id)
            
            info = ComplementoEscolaPrevisaoInfo(
                escola_id=escola.id,
                nome_uex=escola.nome_uex,
                dre=escola.dre,
                liberada=liberada,
                numero_folha=folha,
                valor_complemento_total=complemento.valor_complemento_total or 0.0,
                status=complemento.status.value
            )
            
            agrupado[folha].append(info.dict())
        
        # Criar lista de folhas
        folhas_info: List[ComplementoFolhaInfo] = []
        total_valor = 0.0
        total_escolas = 0
        
        for folha, escolas_lista in sorted(agrupado.items(), key=lambda x: x[0] if x[0] is not None else 999999):
            valor_folha = sum(e["valor_complemento_total"] for e in escolas_lista)
            total_valor += valor_folha
            total_escolas += len(escolas_lista)
            
            folhas_info.append(ComplementoFolhaInfo(
                numero_folha=folha,
                total_escolas=len(escolas_lista),
                valor_total_reais=round(valor_folha, 2),
                escolas=[ComplementoEscolaPrevisaoInfo(**e) for e in escolas_lista]
            ))
        
        return {
            "success": True,
            "total_folhas": len(folhas_info),
            "total_escolas": total_escolas,
            "valor_total_reais": round(total_valor, 2),
            "folhas": folhas_info
        }

