from sqlalchemy.orm import Session
from datetime import datetime
from src.modules.features.uploads import Upload
from src.modules.features.uploads.repository import UploadRepository, ContextoAtivoRepository
from src.core.logging_config import logger


def obter_ou_criar_upload_ativo(db: Session, ano_letivo_id: int, filename: str) -> Upload:
    upload_repo = UploadRepository(db)
    contexto_repo = ContextoAtivoRepository(db)

    # Regra: para um mesmo ano letivo deve existir NO MÁXIMO 1 upload.
    # - Se já existir, substituímos (update do registro) mantendo o mesmo ID.
    # - Se não existir, criamos um novo.
    # - Se houver duplicados legados, consolidamos movendo escolas para o upload canônico e removendo os uploads extras.

    upload_atual = contexto_repo.find_upload_ativo(ano_letivo_id)
    if not upload_atual:
        upload_atual = upload_repo.find_latest(ano_letivo_id)

    if upload_atual:
        upload_repo.update(
            upload_atual,
            filename=filename,
            upload_date=datetime.now(),
        )
        contexto_repo.ativar_upload(ano_letivo_id, upload_atual.id)

        # Consolidar duplicados legados do mesmo ano (se existirem)
        uploads_mesmo_ano = upload_repo.find_all_by_ano_letivo(ano_letivo_id)
        extras = [u for u in uploads_mesmo_ano if u.id != upload_atual.id]
        if extras:
            logger.warning(
                f"Encontrados {len(extras)} upload(s) duplicado(s) para ano_letivo_id={ano_letivo_id}. "
                f"Consolidando no upload_id={upload_atual.id}."
            )
            from src.modules.features.escolas import Escola

            for extra in extras:
                # Consolidação segura:
                # - Se não houver colisão (nome_uex,dre) no upload canônico: mover escola para upload canônico
                # - Se houver colisão: migrar liberações para a escola canônica e remover a duplicata
                canon_map = {
                    (n, d): (eid, cnpj)
                    for (eid, n, d, cnpj) in db.query(Escola.id, Escola.nome_uex, Escola.dre, Escola.cnpj)
                    .filter(Escola.upload_id == upload_atual.id)
                    .all()
                }

                escolas_extra = (
                    db.query(Escola)
                    .filter(Escola.upload_id == extra.id)
                    .all()
                )

                moved = 0
                merged = 0
                merge_errors = 0

                for escola_dup in escolas_extra:
                    key = (escola_dup.nome_uex, escola_dup.dre)
                    target = canon_map.get(key)

                    if not target:
                        escola_dup.upload_id = upload_atual.id
                        moved += 1
                        continue

                    target_escola_id = target[0]

                    try:
                        # Migrar liberações (parcelas/projetos/complemento) para a escola alvo
                        from src.modules.features.parcelas.models import LiberacoesParcela
                        from src.modules.features.projetos.models import LiberacoesProjeto
                        from src.modules.features.complemento.models import LiberacoesComplemento

                        # 1) Parcelas: pode colidir por (escola_id,numero_parcela)
                        dup_lps = (
                            db.query(LiberacoesParcela)
                            .filter(LiberacoesParcela.escola_id == escola_dup.id)
                            .all()
                        )
                        for lp in dup_lps:
                            existing = (
                                db.query(LiberacoesParcela)
                                .filter(
                                    LiberacoesParcela.escola_id == target_escola_id,
                                    LiberacoesParcela.numero_parcela == lp.numero_parcela,
                                )
                                .first()
                            )
                            if existing:
                                # Merge conservador: mantém liberada se qualquer um for True
                                existing.liberada = bool(existing.liberada or lp.liberada)
                                if existing.numero_folha is None and lp.numero_folha is not None:
                                    existing.numero_folha = lp.numero_folha
                                if existing.data_liberacao is None and lp.data_liberacao is not None:
                                    existing.data_liberacao = lp.data_liberacao
                                # preservar maior valor_projetos_aprovados (se aplicável)
                                if getattr(lp, "valor_projetos_aprovados", 0.0) > getattr(existing, "valor_projetos_aprovados", 0.0):
                                    existing.valor_projetos_aprovados = lp.valor_projetos_aprovados
                                db.delete(lp)
                            else:
                                lp.escola_id = target_escola_id

                        # 2) Projeto: unique por escola_id
                        dup_proj = (
                            db.query(LiberacoesProjeto)
                            .filter(LiberacoesProjeto.escola_id == escola_dup.id)
                            .first()
                        )
                        if dup_proj:
                            existing_proj = (
                                db.query(LiberacoesProjeto)
                                .filter(LiberacoesProjeto.escola_id == target_escola_id)
                                .first()
                            )
                            if existing_proj:
                                existing_proj.liberada = bool(existing_proj.liberada or dup_proj.liberada)
                                if existing_proj.numero_folha is None and dup_proj.numero_folha is not None:
                                    existing_proj.numero_folha = dup_proj.numero_folha
                                if existing_proj.data_liberacao is None and dup_proj.data_liberacao is not None:
                                    existing_proj.data_liberacao = dup_proj.data_liberacao
                                if dup_proj.valor_projetos_aprovados > existing_proj.valor_projetos_aprovados:
                                    existing_proj.valor_projetos_aprovados = dup_proj.valor_projetos_aprovados
                                db.delete(dup_proj)
                            else:
                                dup_proj.escola_id = target_escola_id

                        # 3) Complemento: unique por (escola_id, complemento_upload_id)
                        dup_comp = (
                            db.query(LiberacoesComplemento)
                            .filter(LiberacoesComplemento.escola_id == escola_dup.id)
                            .all()
                        )
                        for lc in dup_comp:
                            exists_lc = (
                                db.query(LiberacoesComplemento)
                                .filter(
                                    LiberacoesComplemento.escola_id == target_escola_id,
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
                                lc.escola_id = target_escola_id

                        # Após migrar liberações, deletar escola duplicada.
                        # Usar bulk delete para evitar que o ORM tente nullar FKs (ex.: liberacoes_projeto.escola_id),
                        # o que viola NOT NULL no Postgres.
                        db.flush()
                        db.query(Escola).filter(Escola.id == escola_dup.id).delete(synchronize_session=False)
                        merged += 1
                    except Exception as e:
                        merge_errors += 1
                        logger.exception(
                            "Erro ao fazer merge de escola duplicada (extra_upload_id=%s, dup_escola_id=%s, target_escola_id=%s)",
                            extra.id,
                            escola_dup.id,
                            target_escola_id,
                        )

                db.flush()
                logger.info(
                    "Consolidação do upload extra concluída (extra_upload_id=%s, moved=%s, merged=%s, merge_errors=%s)",
                    extra.id,
                    moved,
                    merged,
                    merge_errors,
                )

                # Remover upload extra após mover/mesclar escolas
                upload_repo.delete(extra)

        logger.info(
            f"Upload do ano letivo {ano_letivo_id} substituído (upload_id mantido={upload_atual.id})."
        )
        return upload_atual

    novo_upload = upload_repo.create(
        ano_letivo_id=ano_letivo_id,
        filename=filename,
        total_escolas=0,
        upload_date=datetime.now(),
    )
    contexto_repo.ativar_upload(ano_letivo_id, novo_upload.id)
    logger.info(
        f"Criado novo upload ID {novo_upload.id} para ano_letivo_id={ano_letivo_id} e ativado no contexto."
    )
    return novo_upload

