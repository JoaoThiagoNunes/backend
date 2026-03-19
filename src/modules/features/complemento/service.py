from sqlalchemy.orm import Session, joinedload
from typing import Optional, Dict, Any, List
from io import BytesIO
from datetime import datetime
import pandas as pd
from src.core.logging_config import logger
from src.core.database import transaction
from src.core.exceptions import UploadNaoEncontradoException
from fastapi import HTTPException
from src.modules.features.anos import obter_ano_letivo
from src.modules.features.uploads import UploadService
from src.modules.features.uploads.repository import UploadRepository
from src.modules.features.escolas.repository import EscolaRepository
from .repository import ComplementoUploadRepository, ComplementoEscolaRepository, LiberacaoComplementoRepository, ParcelasComplementoRepository
from .models import ComplementoUpload, ComplementoEscola, StatusComplemento, LiberacoesComplemento, ParcelasComplemento
from .utils import comparar_quantidades, calcular_complemento_valores, calcular_porcentagens_ensino_complemento, dividir_complemento_por_ensino
from src.modules.shared.utils import obter_texto, obter_quantidade
from src.modules.features.calculos import TipoCota, TipoEnsino
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
        liberacao_repo = LiberacaoComplementoRepository(db)
        
        resultados = []
        escolas_com_aumento = 0
        escolas_sem_mudanca = 0
        escolas_com_diminuicao = 0
        escolas_com_erro = 0
        valor_total_complemento = 0.0
        
        with transaction(db):
            # Buscar complementos atuais do ano (pode haver legado); manteremos apenas o novo no final
            complementos_antigos = complemento_repo.find_by_ano_letivo(ano_id)
            antigos_ids = [c.id for c in complementos_antigos]
            
            # Criar registro de ComplementoUpload para este novo processamento
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
                        valor_complemento_sala_recurso=max(0.0, valores_complemento.get('profin_sala_recurso', 0.0)),
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

            # ============
            # MIGRAR LIBERAÇÕES DO COMPLEMENTO ANTIGO PARA O NOVO
            # ============
            if antigos_ids:
                escolas_novas_ids = {
                    ce.escola_id for ce in complemento_escola_repo.find_by_complemento_upload(complemento_upload.id)
                }
                if escolas_novas_ids:
                    antigas_liberacoes = (
                        db.query(LiberacoesComplemento)
                        .filter(LiberacoesComplemento.complemento_upload_id.in_(antigos_ids))
                        .all()
                    )
                    if antigas_liberacoes:
                        logger.info(
                            "Migrando %s liberações de complemento dos complemento_upload_ids=%s para %s",
                            len(antigas_liberacoes),
                            antigos_ids,
                            complemento_upload.id,
                        )
                        # mapa de liberações já existentes no novo complemento (por escola)
                        mapa_existentes_novo = liberacao_repo.create_map_by_escola_id(
                            list(escolas_novas_ids),
                            complemento_upload_id=complemento_upload.id,
                        )
                        for lib_antiga in antigas_liberacoes:
                            escola_id = lib_antiga.escola_id
                            if escola_id not in escolas_novas_ids:
                                # escola não está no novo complemento, descartar liberação
                                db.delete(lib_antiga)
                                continue

                            lib_nova = mapa_existentes_novo.get(escola_id)
                            if lib_nova:
                                lib_nova.liberada = bool(lib_nova.liberada or lib_antiga.liberada)
                                if lib_nova.numero_folha is None and lib_antiga.numero_folha is not None:
                                    lib_nova.numero_folha = lib_antiga.numero_folha
                                if lib_nova.data_liberacao is None and lib_antiga.data_liberacao is not None:
                                    lib_nova.data_liberacao = lib_antiga.data_liberacao
                                db.delete(lib_antiga)
                            else:
                                lib_antiga.complemento_upload_id = complemento_upload.id
                                mapa_existentes_novo[escola_id] = lib_antiga

                        # Garantir que as alterações em LiberacoesComplemento (troca de complemento_upload_id)
                        # sejam persistidas no banco antes de deletarmos os ComplementoUpload antigos
                        # (evita que o ON DELETE CASCADE apague as linhas migradas).
                        db.flush()

                # ============
                # REMOVER COMPLEMENTOS ANTIGOS (mantendo apenas o novo por ano)
                # ============
                for cid in antigos_ids:
                    if cid == complemento_upload.id:
                        continue
                    antigo = complemento_repo.find_by_id(cid)
                    if antigo:
                        db.delete(antigo)
        
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
        _, ano_id = obter_ano_letivo(db, ano_letivo_id)

        # Se não informado complemento_upload_id, buscar o mais recente
        if complemento_upload_id is None:
            complemento_repo = ComplementoUploadRepository(db)
            # Preferir o mais recente que tem ComplementoEscola; se não existir, cair no mais recente geral.
            complemento_upload_recente = (
                complemento_repo.find_mais_recente_com_complemento_escola_por_ano_letivo(ano_id)
                or complemento_repo.find_mais_recente_by_ano_letivo(ano_id)
            )
            if complemento_upload_recente:
                complemento_upload_id = complemento_upload_recente.id

        if not complemento_upload_id:
            return {
                "success": True,
                "total_folhas": 0,
                "total_escolas": 0,
                "valor_total_reais": 0.0,
                "folhas": []
            }

        complemento_escola_repo = ComplementoEscolaRepository(db)
        liberacao_repo = LiberacaoComplementoRepository(db)

        # Importante: não depender do "upload base ativo".
        # Montamos o resumo diretamente a partir dos dados do `complemento_upload_id`.
        complementos_escola = complemento_escola_repo.find_by_complemento_upload(complemento_upload_id)

        # Buscar liberações
        liberacoes = liberacao_repo.find_liberadas(complemento_upload_id=complemento_upload_id)
        mapa_liberacoes: Dict[int, LiberacoesComplemento] = {lib.escola_id: lib for lib in liberacoes}

        # Agrupar por folha
        agrupado: Dict[Optional[int], List[Dict[str, Any]]] = {}
        escolas_por_folha: Dict[Optional[int], set] = {}

        for complemento in complementos_escola:
            escola_id = complemento.escola_id

            liberacao = mapa_liberacoes.get(escola_id)
            if liberacao:
                folha = liberacao.numero_folha
                liberada = liberacao.liberada
            else:
                folha = None
                liberada = False

            if folha not in agrupado:
                agrupado[folha] = []
                escolas_por_folha[folha] = set()

            if escola_id in escolas_por_folha[folha]:
                continue
            escolas_por_folha[folha].add(escola_id)

            parcelas_info = ComplementoService.obter_parcelas_complemento_formatadas(db, complemento)

            info = ComplementoEscolaPrevisaoInfo(
                escola_id=escola_id,
                nome_uex=complemento.escola.nome_uex,
                dre=complemento.escola.dre,
                liberada=liberada,
                numero_folha=folha,
                valor_complemento_total=complemento.valor_complemento_total or 0.0,
                status=complemento.status.value,
                parcelas_por_cota=parcelas_info["parcelas_por_cota"],
                porcentagem_fundamental=parcelas_info["porcentagem_fundamental"],
                porcentagem_medio=parcelas_info["porcentagem_medio"],
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
    
    @staticmethod
    def obter_parcelas_complemento_formatadas(
        db: Session,
        complemento_escola: ComplementoEscola
    ) -> Dict[str, Any]:
        """
        Busca e formata parcelas de complemento para uma escola específica.
        
        Retorna um dicionário com:
        - parcelas: Lista de parcelas detalhadas
        - parcelas_por_cota: Lista agrupada por cota com valores separados por ensino
        - porcentagem_fundamental: Porcentagem de alunos em fundamental
        - porcentagem_medio: Porcentagem de alunos em médio
        
        Se não houver parcelas, retorna None para todos os campos.
        """
        from src.modules.schemas.complemento import ComplementoParcelaDetalhe, ParcelaComplementoPorCota
        
        # Validar entrada
        if complemento_escola is None:
            logger.warning("obter_parcelas_complemento_formatadas recebeu complemento_escola None")
            return {
                "parcelas": None,
                "parcelas_por_cota": None,
                "porcentagem_fundamental": None,
                "porcentagem_medio": None
            }
        
        try:
            parcelas_repo = ParcelasComplementoRepository(db)
            parcelas = parcelas_repo.find_by_complemento_escola_id(complemento_escola.id)
            
            # Calcular porcentagens mesmo quando não há parcelas no banco
            diferencas = {
                'fundamental_inicial': complemento_escola.fundamental_inicial_diferenca or 0,
                'fundamental_final': complemento_escola.fundamental_final_diferenca or 0,
                'fundamental_integral': complemento_escola.fundamental_integral_diferenca or 0,
                'profissionalizante': complemento_escola.profissionalizante_diferenca or 0,
                'profissionalizante_integrado': complemento_escola.profissionalizante_integrado_diferenca or 0,
                'alternancia': complemento_escola.alternancia_diferenca or 0,
                'ensino_medio_integral': complemento_escola.ensino_medio_integral_diferenca or 0,
                'ensino_medio_regular': complemento_escola.ensino_medio_regular_diferenca or 0,
                'especial_fund_regular': complemento_escola.especial_fund_regular_diferenca or 0,
                'especial_fund_integral': complemento_escola.especial_fund_integral_diferenca or 0,
                'especial_medio_parcial': complemento_escola.especial_medio_parcial_diferenca or 0,
                'especial_medio_integral': complemento_escola.especial_medio_integral_diferenca or 0,
            }
            pct_fundamental, pct_medio = calcular_porcentagens_ensino_complemento(diferencas)
            
            if not parcelas:
                # Calcular parcelas_por_cota mesmo sem parcelas no banco usando valores de complemento
                from src.modules.schemas.complemento import ParcelaComplementoPorCota
                
                try:
                    _COTAS_COMPLEMENTO_PROCESSAR = [
                        ("Gestão", "valor_complemento_gestao", TipoCota.GESTAO),
                        ("Merenda", "valor_complemento_merenda", TipoCota.MERENDA),
                        ("Kit Escolar", "valor_complemento_kit_escolar", TipoCota.KIT_ESCOLAR),
                        ("Uniforme", "valor_complemento_uniforme", TipoCota.UNIFORME),
                        ("Sala de Recurso", "valor_complemento_sala_recurso", TipoCota.SALA_RECURSO),
                    ]
                    
                    parcelas_por_cota = []
                    
                    for nome_exibicao, campo_cota, tipo_cota_enum in _COTAS_COMPLEMENTO_PROCESSAR:
                        valor_cota = getattr(complemento_escola, campo_cota, 0.0) or 0.0
                        
                        if valor_cota > 0:
                            try:
                                # Dividir valor por ensino usando porcentagens
                                divisao = dividir_complemento_por_ensino(
                                    valor_cota,
                                    pct_fundamental,
                                    pct_medio,
                                    numero_parcelas=1
                                )
                                
                                parcela_por_cota = ParcelaComplementoPorCota(
                                    tipo_cota=tipo_cota_enum.value,
                                    valor_total_reais=valor_cota,
                                    parcela_1={
                                        "fundamental": divisao["parcela_1"]["fundamental"] / 100.0,
                                        "medio": divisao["parcela_1"]["medio"] / 100.0
                                    },
                                    porcentagens={
                                        "fundamental": pct_fundamental,
                                        "medio": pct_medio
                                    }
                                )
                                parcelas_por_cota.append(parcela_por_cota)
                            except Exception as e:
                                logger.error(f"Erro ao calcular parcela_por_cota para {campo_cota}: {str(e)}", exc_info=True)
                                continue
                    
                    # Retornar porcentagens e parcelas_por_cota calculadas mesmo sem parcelas no banco
                    return {
                        "parcelas": None,
                        "parcelas_por_cota": parcelas_por_cota if parcelas_por_cota else None,
                        "porcentagem_fundamental": pct_fundamental,
                        "porcentagem_medio": pct_medio
                    }
                except Exception as e:
                    logger.error(f"Erro ao calcular parcelas_por_cota para complemento_escola {complemento_escola.id}: {str(e)}", exc_info=True)
                    return {
                        "parcelas": None,
                        "parcelas_por_cota": None,
                        "porcentagem_fundamental": pct_fundamental,
                        "porcentagem_medio": pct_medio
                    }
        except Exception as e:
            logger.error(f"Erro ao buscar parcelas para complemento_escola {complemento_escola.id}: {str(e)}", exc_info=True)
            return {
                "parcelas": None,
                "parcelas_por_cota": None,
                "porcentagem_fundamental": None,
                "porcentagem_medio": None
            }
        
        try:
            # Calcular porcentagens baseado nas diferenças
            diferencas = {
                'fundamental_inicial': complemento_escola.fundamental_inicial_diferenca or 0,
                'fundamental_final': complemento_escola.fundamental_final_diferenca or 0,
                'fundamental_integral': complemento_escola.fundamental_integral_diferenca or 0,
                'profissionalizante': complemento_escola.profissionalizante_diferenca or 0,
                'profissionalizante_integrado': complemento_escola.profissionalizante_integrado_diferenca or 0,
                'alternancia': complemento_escola.alternancia_diferenca or 0,
                'ensino_medio_integral': complemento_escola.ensino_medio_integral_diferenca or 0,
                'ensino_medio_regular': complemento_escola.ensino_medio_regular_diferenca or 0,
                'especial_fund_regular': complemento_escola.especial_fund_regular_diferenca or 0,
                'especial_fund_integral': complemento_escola.especial_fund_integral_diferenca or 0,
                'especial_medio_parcial': complemento_escola.especial_medio_parcial_diferenca or 0,
                'especial_medio_integral': complemento_escola.especial_medio_integral_diferenca or 0,
            }
            pct_fundamental, pct_medio = calcular_porcentagens_ensino_complemento(diferencas)
            
            # Mapear parcelas para detalhes
            parcelas_detalhes = []
            for p in parcelas:
                try:
                    parcela_detalhe = ComplementoParcelaDetalhe(
                        id=p.id,
                        tipo_cota=p.tipo_cota.value,
                        numero_parcela=p.numero_parcela,
                        tipo_ensino=p.tipo_ensino.value,
                        valor_reais=p.valor_reais,
                        valor_centavos=p.valor_centavos,
                        porcentagem_alunos=p.porcentagem_alunos or 0.0,
                        created_at=p.created_at
                    )
                    parcelas_detalhes.append(parcela_detalhe)
                except Exception as e:
                    logger.error(f"Erro ao criar ComplementoParcelaDetalhe para parcela {p.id}: {str(e)}", exc_info=True)
                    continue
            
            # Agrupar parcelas por cota
            parcelas_por_cota_dict = {}
            for parcela in parcelas:
                try:
                    cota_enum_value = parcela.tipo_cota.value
                    if cota_enum_value not in parcelas_por_cota_dict:
                        parcelas_por_cota_dict[cota_enum_value] = {
                            "tipo_cota": cota_enum_value,
                            "valor_total_reais": 0.0,
                            "parcela_1": {"fundamental": 0.0, "medio": 0.0},
                            "porcentagens": {
                                "fundamental": pct_fundamental,
                                "medio": pct_medio
                            }
                        }
                    
                    if parcela.numero_parcela == 1:
                        if parcela.tipo_ensino == TipoEnsino.FUNDAMENTAL:
                            parcelas_por_cota_dict[cota_enum_value]["parcela_1"]["fundamental"] = parcela.valor_reais
                        else:
                            parcelas_por_cota_dict[cota_enum_value]["parcela_1"]["medio"] = parcela.valor_reais
                        
                        parcelas_por_cota_dict[cota_enum_value]["valor_total_reais"] += parcela.valor_reais
                except Exception as e:
                    logger.error(f"Erro ao processar parcela {parcela.id}: {str(e)}", exc_info=True)
                    continue
            
            parcelas_por_cota = []
            for dados in parcelas_por_cota_dict.values():
                try:
                    parcela_por_cota = ParcelaComplementoPorCota(**dados)
                    parcelas_por_cota.append(parcela_por_cota)
                except Exception as e:
                    logger.error(f"Erro ao criar ParcelaComplementoPorCota: {str(e)}", exc_info=True)
                    continue
            
            return {
                "parcelas": parcelas_detalhes if parcelas_detalhes else None,
                "parcelas_por_cota": parcelas_por_cota if parcelas_por_cota else None,
                "porcentagem_fundamental": pct_fundamental,
                "porcentagem_medio": pct_medio
            }
        except Exception as e:
            logger.error(f"Erro ao processar parcelas para complemento_escola {complemento_escola.id}: {str(e)}", exc_info=True)
            return {
                "parcelas": None,
                "parcelas_por_cota": None,
                "porcentagem_fundamental": None,
                "porcentagem_medio": None
            }
    
    @staticmethod
    def separar_complementos_por_ensino(
        db: Session,
        complemento_upload_id: Optional[int] = None,
        ano_letivo_id: Optional[int] = None,
        recalcular: bool = False,
        calculation_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Separa os valores de complemento entre ensino fundamental e médio.
        
        Similar ao processo de separação de parcelas normais, mas aplicado aos complementos.
        """
        from src.core.database import transaction
        
        ano_letivo, ano_id = obter_ano_letivo(db, ano_letivo_id)
        
        # Se não informado complemento_upload_id, buscar o mais recente
        if complemento_upload_id is None:
            complemento_repo = ComplementoUploadRepository(db)
            complemento_upload_recente = complemento_repo.find_mais_recente_by_ano_letivo(ano_id)
            if not complemento_upload_recente:
                raise HTTPException(
                    status_code=404,
                    detail=f"Nenhum complemento encontrado para o ano letivo {ano_letivo.ano}"
                )
            complemento_upload_id = complemento_upload_recente.id
        
        calculation_version = calculation_version or f"v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info("="*60)
        logger.info(f"SEPARANDO COMPLEMENTOS POR ENSINO - ANO LETIVO: {ano_letivo.ano}")
        logger.info(f"Complemento Upload ID: {complemento_upload_id}")
        logger.info(f"Versão do cálculo: {calculation_version}")
        logger.info("="*60)
        
        # Buscar complementos do upload especificado
        complemento_escola_repo = ComplementoEscolaRepository(db)
        complementos_escola = complemento_escola_repo.find_by_complemento_upload(complemento_upload_id)
        
        if not complementos_escola:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum complemento encontrado para complemento_upload_id={complemento_upload_id}"
            )
        
        # Filtrar apenas complementos com aumento (que têm valores)
        complementos_com_valor = [
            c for c in complementos_escola 
            if c.status == StatusComplemento.AUMENTO and c.valor_complemento_total > 0
        ]
        
        if not complementos_com_valor:
            raise HTTPException(
                status_code=404,
                detail="Nenhum complemento com valores encontrado para separar"
            )
        
        # Verificar se já existem parcelas
        deve_deletar_parcelas = False
        if not recalcular:
            parcelas_existentes = db.query(ParcelasComplemento).filter(
                ParcelasComplemento.complemento_escola_id.in_([c.id for c in complementos_com_valor])
            ).all()
            
            if parcelas_existentes:
                logger.info(f"Encontradas {len(parcelas_existentes)} parcela(s) existente(s). Use recalcular=true para recalcular.")
                # Retornar parcelas existentes
                escolas_dict = {}
                for parcela in parcelas_existentes:
                    complemento_escola = parcela.complemento_escola
                    escola = complemento_escola.escola
                    escola_id = escola.id
                    
                    if escola_id not in escolas_dict:
                        # Calcular porcentagens baseado nas diferenças
                        diferencas = {
                            'fundamental_inicial': complemento_escola.fundamental_inicial_diferenca,
                            'fundamental_final': complemento_escola.fundamental_final_diferenca,
                            'fundamental_integral': complemento_escola.fundamental_integral_diferenca,
                            'profissionalizante': complemento_escola.profissionalizante_diferenca,
                            'profissionalizante_integrado': complemento_escola.profissionalizante_integrado_diferenca,
                            'alternancia': complemento_escola.alternancia_diferenca,
                            'ensino_medio_integral': complemento_escola.ensino_medio_integral_diferenca,
                            'ensino_medio_regular': complemento_escola.ensino_medio_regular_diferenca,
                            'especial_fund_regular': complemento_escola.especial_fund_regular_diferenca,
                            'especial_fund_integral': complemento_escola.especial_fund_integral_diferenca,
                            'especial_medio_parcial': complemento_escola.especial_medio_parcial_diferenca,
                            'especial_medio_integral': complemento_escola.especial_medio_integral_diferenca,
                        }
                        pct_fund, pct_medio = calcular_porcentagens_ensino_complemento(diferencas)
                        
                        escolas_dict[escola_id] = {
                            "escola": escola,
                            "complemento_escola": complemento_escola,
                            "pct_fundamental": pct_fund,
                            "pct_medio": pct_medio,
                            "parcelas_por_cota": {}
                        }
                    
                    cota_enum_value = parcela.tipo_cota.value
                    if cota_enum_value not in escolas_dict[escola_id]["parcelas_por_cota"]:
                        escolas_dict[escola_id]["parcelas_por_cota"][cota_enum_value] = {
                            "tipo_cota": cota_enum_value,
                            "valor_total_reais": 0.0,
                            "parcela_1": {"fundamental": 0.0, "medio": 0.0},
                            "porcentagens": {
                                "fundamental": escolas_dict[escola_id]["pct_fundamental"],
                                "medio": escolas_dict[escola_id]["pct_medio"]
                            }
                        }
                    
                    if parcela.numero_parcela == 1:
                        if parcela.tipo_ensino == TipoEnsino.FUNDAMENTAL:
                            escolas_dict[escola_id]["parcelas_por_cota"][cota_enum_value]["parcela_1"]["fundamental"] = parcela.valor_reais
                        else:
                            escolas_dict[escola_id]["parcelas_por_cota"][cota_enum_value]["parcela_1"]["medio"] = parcela.valor_reais
                        
                        escolas_dict[escola_id]["parcelas_por_cota"][cota_enum_value]["valor_total_reais"] += parcela.valor_reais
                
                escolas_lista = []
                for escola_id, dados in escolas_dict.items():
                    escolas_lista.append({
                        "escola_id": escola_id,
                        "nome_uex": dados["escola"].nome_uex,
                        "dre": dados["escola"].dre,
                        "porcentagem_fundamental": dados["pct_fundamental"],
                        "porcentagem_medio": dados["pct_medio"],
                        "parcelas_por_cota": list(dados["parcelas_por_cota"].values())
                    })
                
                return {
                    "success": True,
                    "message": f"Parcelas já existem. Use recalcular=true para recalcular.",
                    "total_escolas": len(escolas_dict),
                    "escolas_processadas": len(escolas_dict),
                    "total_parcelas_criadas": len(parcelas_existentes),
                    "complemento_upload_id": complemento_upload_id,
                    "escolas": escolas_lista,
                    "calculation_version": calculation_version
                }
        else:
            deve_deletar_parcelas = True
        
        # Cotas processadas no complemento
        _COTAS_COMPLEMENTO = [
            ("Gestão", "valor_complemento_gestao", TipoCota.CUSTEIO),
            ("Merenda", "valor_complemento_merenda", TipoCota.MERENDA),
            ("Kit Escolar", "valor_complemento_kit_escolar", TipoCota.KIT_ESCOLAR),
            ("Uniforme", "valor_complemento_uniforme", TipoCota.UNIFORME),
            ("Sala de Recurso", "valor_complemento_sala_recurso", TipoCota.SALA_RECURSO),
        ]
        
        with transaction(db):
            # Deletar parcelas existentes se necessário
            if deve_deletar_parcelas:
                parcelas_para_deletar = db.query(ParcelasComplemento).filter(
                    ParcelasComplemento.complemento_escola_id.in_([c.id for c in complementos_com_valor])
                ).all()
                
                if parcelas_para_deletar:
                    for parcela in parcelas_para_deletar:
                        db.delete(parcela)
                    logger.info(f"Deletadas {len(parcelas_para_deletar)} parcela(s) existente(s)")
                    db.flush()
            
            # Criar novas parcelas
            escolas_processadas = []
            total_parcelas_criadas = 0
            
            for complemento_escola in complementos_com_valor:
                escola = complemento_escola.escola
                if not escola:
                    logger.warning(f"Escola não encontrada para complemento {complemento_escola.id}")
                    continue
                
                # Calcular porcentagens baseado nas diferenças
                diferencas = {
                    'fundamental_inicial': complemento_escola.fundamental_inicial_diferenca,
                    'fundamental_final': complemento_escola.fundamental_final_diferenca,
                    'fundamental_integral': complemento_escola.fundamental_integral_diferenca,
                    'profissionalizante': complemento_escola.profissionalizante_diferenca,
                    'profissionalizante_integrado': complemento_escola.profissionalizante_integrado_diferenca,
                    'alternancia': complemento_escola.alternancia_diferenca,
                    'ensino_medio_integral': complemento_escola.ensino_medio_integral_diferenca,
                    'ensino_medio_regular': complemento_escola.ensino_medio_regular_diferenca,
                    'especial_fund_regular': complemento_escola.especial_fund_regular_diferenca,
                    'especial_fund_integral': complemento_escola.especial_fund_integral_diferenca,
                    'especial_medio_parcial': complemento_escola.especial_medio_parcial_diferenca,
                    'especial_medio_integral': complemento_escola.especial_medio_integral_diferenca,
                }
                
                pct_fundamental, pct_medio = calcular_porcentagens_ensino_complemento(diferencas)
                parcelas_por_cota = []
                
                for nome_exibicao, campo_cota, tipo_cota_enum in _COTAS_COMPLEMENTO:
                    valor_cota = getattr(complemento_escola, campo_cota, 0.0)
                    
                    if valor_cota <= 0:
                        continue
                    
                    # Dividir complemento por ensino (sempre 1 parcela)
                    divisao = dividir_complemento_por_ensino(
                        valor_cota,
                        pct_fundamental,
                        pct_medio,
                        numero_parcelas=1
                    )
                    
                    # Criar parcela fundamental
                    parcela_1_fund = ParcelasComplemento(
                        complemento_escola_id=complemento_escola.id,
                        tipo_cota=tipo_cota_enum,
                        numero_parcela=1,
                        tipo_ensino=TipoEnsino.FUNDAMENTAL,
                        valor_centavos=divisao["parcela_1"]["fundamental"],
                        porcentagem_alunos=pct_fundamental,
                        calculation_version=calculation_version
                    )
                    db.add(parcela_1_fund)
                    total_parcelas_criadas += 1
                    
                    # Criar parcela médio
                    parcela_1_medio = ParcelasComplemento(
                        complemento_escola_id=complemento_escola.id,
                        tipo_cota=tipo_cota_enum,
                        numero_parcela=1,
                        tipo_ensino=TipoEnsino.MEDIO,
                        valor_centavos=divisao["parcela_1"]["medio"],
                        porcentagem_alunos=pct_medio,
                        calculation_version=calculation_version
                    )
                    db.add(parcela_1_medio)
                    total_parcelas_criadas += 1
                    
                    parcelas_por_cota.append({
                        "tipo_cota": tipo_cota_enum.value,
                        "valor_total_reais": valor_cota,
                        "parcela_1": {
                            "fundamental": divisao["parcela_1"]["fundamental"] / 100.0,
                            "medio": divisao["parcela_1"]["medio"] / 100.0
                        },
                        "porcentagens": {
                            "fundamental": pct_fundamental,
                            "medio": pct_medio
                        }
                    })
                
                escolas_processadas.append({
                    "escola_id": escola.id,
                    "nome_uex": escola.nome_uex,
                    "dre": escola.dre,
                    "porcentagem_fundamental": pct_fundamental,
                    "porcentagem_medio": pct_medio,
                    "parcelas_por_cota": parcelas_por_cota
                })
            
            logger.info(f"Criadas {total_parcelas_criadas} parcela(s) para {len(complementos_com_valor)} complemento(s)")
        
        logger.info("="*60)
        logger.info("SEPARAÇÃO DE COMPLEMENTOS CONCLUÍDA")
        logger.info(f"Escolas processadas: {len(escolas_processadas)}")
        logger.info(f"Total de parcelas criadas: {total_parcelas_criadas}")
        logger.info("="*60)
        
        return {
            "success": True,
            "message": f"Separados {len(escolas_processadas)} complemento(s) em {total_parcelas_criadas} parcela(s)",
            "total_escolas": len(complementos_com_valor),
            "escolas_processadas": len(escolas_processadas),
            "total_parcelas_criadas": total_parcelas_criadas,
            "complemento_upload_id": complemento_upload_id,
            "escolas": escolas_processadas,
            "calculation_version": calculation_version
        }

