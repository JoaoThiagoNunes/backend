"""
Sistema de autenticação simples para endpoints críticos.
Usa JWT para tokens de acesso e senha armazenada em variável de ambiente.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.core.config import SECRET_KEY, ADMIN_PASSWORD, ACCESS_TOKEN_EXPIRE_HOURS

# Configurações
ALGORITHM = "HS256"

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme para FastAPI
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha fornecida corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera hash da senha (não usado no sistema atual, mas disponível para expansão)."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT.
    
    Args:
        data: Dados a serem incluídos no token (ex: {"sub": "admin"})
        expires_delta: Tempo de expiração do token. Se None, usa o padrão.
    
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verifica e decodifica um token JWT.
    
    Esta função é usada como dependência do FastAPI para proteger endpoints.
    
    Args:
        credentials: Credenciais HTTP contendo o token Bearer
    
    Returns:
        Dados decodificados do token
    
    Raises:
        HTTPException: Se o token for inválido ou expirado
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_admin(password: str) -> bool:
    """
    Autentica o admin verificando se a senha está correta.
    
    Args:
        password: Senha fornecida pelo usuário
    
    Returns:
        True se a senha estiver correta, False caso contrário
    """
    return password == ADMIN_PASSWORD


# Dependência para proteger endpoints
def get_current_admin(token_data: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Dependência do FastAPI que garante que o usuário está autenticado.
    
    Use esta dependência em rotas que precisam de autenticação:
    
    @router.delete("/endpoint")
    def endpoint_protegido(current_admin: dict = Depends(get_current_admin)):
        ...
    
    Args:
        token_data: Dados do token decodificado (injetado automaticamente)
    
    Returns:
        Dados do token (pode conter informações do usuário)
    """
    # Se chegou até aqui, o token é válido
    return token_data

