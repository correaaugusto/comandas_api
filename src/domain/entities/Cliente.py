from pydantic import BaseModel

#Augusto correa

class Cliente(BaseModel):
    id_cliente: int = None
    nome: str
    cpf: str
    telefone: str