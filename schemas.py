from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    # Este schema define qué datos debe mandar el cliente
    # cuando quiere crear un usuario.
    # Pydantic valida automáticamente que:
    # - los campos obligatorios estén presentes
    # - los tipos sean correctos
    # Si algo falla → FastAPI devuelve 422 automáticamente

    nombre: str   # obligatorio, debe ser texto
    email: str    # obligatorio, debe ser texto

class UserResponse(BaseModel):
    # Este schema define qué datos devuelve la API
    # al mostrar un usuario.
    # FastAPI filtra automáticamente — si el modelo tiene
    # más campos (como un password en el futuro),
    # solo muestra los que están acá

    id: int
    nombre: str
    email: str
    created_at: Optional[datetime] = None
    # Optional → puede ser None (no siempre viene de la DB)

    class Config:
        from_attributes = True
        # Le dice a Pydantic que puede leer los datos
        # de un objeto SQLAlchemy (no solo de un dict)
        # Sin esto, la conversión User → JSON fallaría