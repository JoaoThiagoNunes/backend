from src.core.logging_config import logger
from src.core.exceptions import BadRequestException
from src.core.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME, SECRET_KEY, ADMIN_PASSWORD


class ConfigValidator:
    @staticmethod
    def validate_database_config() -> None:
        # Validar que as configurações foram carregadas (mesmo que sejam valores padrão)
        if not DB_USER or not DB_PASS or not DB_HOST or not DB_NAME:
            raise BadRequestException(
                detail="Configurações do banco de dados não podem estar vazias"
            )
        
        # Validar porta
        try:
            port = int(DB_PORT)
            if port < 1 or port > 65535:
                raise BadRequestException(
                    detail=f"Porta do banco de dados inválida: {DB_PORT}"
                )
        except ValueError:
            raise BadRequestException(
                detail=f"Porta do banco de dados deve ser um número: {DB_PORT}"
            )
        
        logger.info("Configurações do banco de dados validadas")
    
    @staticmethod
    def validate_auth_config() -> None:
        # Verificar se está usando valores padrão (não seguros para produção)
        import os
        if not os.environ.get("SECRET_KEY"):
            logger.warning(
                "SECRET_KEY não configurada. Usando valor padrão (NÃO SEGURO PARA PRODUÇÃO)"
            )
        elif len(SECRET_KEY) < 32:
            logger.warning(
                "SECRET_KEY muito curta. Recomenda-se pelo menos 32 caracteres"
            )
        
        if not os.environ.get("ADMIN_PASSWORD"):
            logger.warning(
                "ADMIN_PASSWORD não configurada. Usando valor padrão (NÃO SEGURO PARA PRODUÇÃO)"
            )
        
        logger.info("Configurações de autenticação validadas")
    
    @staticmethod
    def validate_all() -> None:
        logger.info("Validando configurações da aplicação...")
        ConfigValidator.validate_database_config()
        ConfigValidator.validate_auth_config()
        logger.info("Todas as configurações validadas com sucesso")

