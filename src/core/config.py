import os
from pathlib import Path
from typing import List

# Diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ====================
# BANCO DE DADOS
# ====================
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "123456")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "profin_db")

# ====================
# AUTENTICAÇÃO
# ====================
SECRET_KEY = os.environ.get("SECRET_KEY", "profin-secret-key-change-in-production-2024")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "profin2025")
ACCESS_TOKEN_EXPIRE_HOURS = 12  # Token válido por 12 horas

# ====================
# CORS
# ====================
CORS_ORIGINS: List[str] = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
]

# ====================
# LOGGING
# ====================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"

# ====================
# SCHEDULER
# ====================
SCHEDULER_TIMEZONE = os.environ.get("SCHEDULER_TIMEZONE", "America/Maceio")

# ====================
# ARQUIVOS
# ====================
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "50"))  # 50MB padrão
ALLOWED_EXTENSIONS = [".xlsx", ".xls", ".csv"]

