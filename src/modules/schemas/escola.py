from pydantic import BaseModel
from typing import Optional

class EscolaBase(BaseModel):
    nome_uex: str
    dre: Optional[str] = None

class EscolaCreate(EscolaBase):
    total_alunos: Optional[int] = 0
   

class EscolaRead(EscolaBase):
    id: int
    total_alunos: Optional[int] = 0

    class Config:
        orm_mode = True
