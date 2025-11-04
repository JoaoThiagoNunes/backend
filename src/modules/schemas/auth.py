from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Schema para requisição de login."""
    password: str


class LoginResponse(BaseModel):
    """Schema para resposta de login bem-sucedido."""
    access_token: str
    token_type: str = "bearer"
    message: str = "Login realizado com sucesso"

