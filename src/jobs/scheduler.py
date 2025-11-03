# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+
import traceback
import logging

from src.core.database import SessionLocal
from src.core.config import SCHEDULER_TIMEZONE
from src.modules.models import AnoLetivo, StatusAnoLetivo

logger = logging.getLogger("profin.scheduler")
logger.setLevel(logging.INFO)


def arquivar_anos_automaticamente():
    """Executa diariamente à meia-noite: arquiva anos letivos cujo dia seja 31/12 (ou conforme regra)."""
    db = SessionLocal()
    try:
        hoje = datetime.now(tz=ZoneInfo(SCHEDULER_TIMEZONE))
        logger.info("Executando arquivar_anos_automaticamente em %s", hoje.isoformat())

        # Se for 31 de dezembro, arquiva o ano atual
        if hoje.month == 12 and hoje.day == 31:
            ano_atual = hoje.year
            ano_letivo = (
                db.query(AnoLetivo)
                .filter(AnoLetivo.ano == ano_atual, AnoLetivo.status == StatusAnoLetivo.ATIVO)
                .first()
            )
            if ano_letivo:
                ano_letivo.status = StatusAnoLetivo.ARQUIVADO
                ano_letivo.arquivado_em = hoje
                db.commit()
                logger.info("✅ Ano letivo %s arquivado automaticamente em %s", ano_atual, hoje)
            else:
                logger.info("Nenhum ano letivo ativo encontrado para %s", ano_atual)
        else:
            logger.debug("Não é 31/12 — não arquivar (hoje=%s)", hoje.date())

    except Exception:
        logger.error("❌ Erro ao arquivar anos:\n%s", traceback.format_exc())
        db.rollback()
    finally:
        db.close()


def limpar_anos_antigos():
    """Executa diariamente: remove anos arquivados há mais de 5 anos."""
    db = SessionLocal()
    try:
        agora = datetime.now(tz=ZoneInfo(SCHEDULER_TIMEZONE))
        limite_data = agora - timedelta(days=5 * 365)
        logger.info("Executando limpar_anos_antigos (limite=%s)", limite_data.date())

        anos_para_deletar = (
            db.query(AnoLetivo)
            .filter(AnoLetivo.status == StatusAnoLetivo.ARQUIVADO, AnoLetivo.arquivado_em <= limite_data)
            .all()
        )

        count = 0
        for ano in anos_para_deletar:
            logger.info("🗑️ Deletando ano letivo %s (arquivado em %s)", ano.ano, ano.arquivado_em)
            db.delete(ano)  # usa cascade do ORM
            count += 1

        if count > 0:
            db.commit()
            logger.info("✅ %d ano(s) letivo(s) antigo(s) removido(s)", count)
        else:
            logger.info("Nenhum ano letivo antigo para remover.")
    except Exception:
        logger.error("❌ Erro ao limpar anos antigos:\n%s", traceback.format_exc())
        db.rollback()
    finally:
        db.close()


# Scheduler singleton
scheduler: BackgroundScheduler | None = None


def start_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        logger.info("Scheduler já está rodando")
        return

    # instância do scheduler em background
    scheduler = BackgroundScheduler(timezone=ZoneInfo(SCHEDULER_TIMEZONE))

    # Cron: todos os dias à meia-noite e meia (00:00 e 00:30)
    scheduler.add_job(arquivar_anos_automaticamente, CronTrigger(hour=0, minute=0, timezone=ZoneInfo(SCHEDULER_TIMEZONE)))
    scheduler.add_job(limpar_anos_antigos, CronTrigger(hour=0, minute=30, timezone=ZoneInfo(SCHEDULER_TIMEZONE)))

    scheduler.start()
    logger.info("Scheduler iniciado com jobs: %s", scheduler.get_jobs())


def stop_scheduler():
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler parado")
        scheduler = None
