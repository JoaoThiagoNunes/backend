from pydantic import BaseModel

class RootResponse(BaseModel):
    message: str

class LoginRequest(BaseModel):
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    message: str = "Login realizado com sucesso"

class LimparDadosResponse(BaseModel):
    success: bool = True
    message: str



