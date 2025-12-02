import logging
import sys
from logging.handlers import RotatingFileHandler
from src.core.config import LOG_DIR, LOG_LEVEL

# Formato de log padrão
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str = LOG_LEVEL) -> logging.Logger:
    # Criar logger principal
    logger = logging.getLogger("profin")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Handler para arquivo (com rotação)
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Adicionar handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Configurar loggers de bibliotecas externas
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    
    return logger


# Logger global do projeto
logger = setup_logging()

