"""
╔══════════════════════════════════════════════════════════════╗
║                        schemas.py                            ║
║   Define la forma del JSON que entra y sale de la API.       ║
║   Pydantic valida automaticamente los datos.                 ║
║   NO tocan la base de datos — solo validan y serializan.     ║
╚══════════════════════════════════════════════════════════════╝
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional          # ← importar UNA SOLA VEZ, acá arriba


class UserCreate(BaseModel):
    """
    Schema de ENTRADA: lo que debe mandar el cliente para crear un usuario.

    Si el cliente manda un JSON sin 'nombre' o sin 'email',
    o si manda un numero donde se espera texto,
    FastAPI devuelve 422 Unprocessable Entity automaticamente
    sin llegar a ejecutar el endpoint.
    """
    nombre: str            # obligatorio, debe ser texto
    email: str             # obligatorio, debe ser texto
    edad: Optional[int] = None   # opcional; None si no se envía
    # BUG ORIGINAL: tenía "from typing import Optional" DENTRO de la clase,
    # lo que creaba un atributo de clase "Optional" y podía interferir
    # con la validación de Pydantic v2.


class UserResponse(BaseModel):
    """
    Schema de SALIDA: lo que devuelve la API al mostrar un usuario.
    """
    id: int
    nombre: str
    email: str
    edad: Optional[int] = None      # ← era "int" (no Optional): crasheaba con 422
                                    #   cuando edad=None, porque Pydantic intentaba
                                    #   validar None como int en la respuesta.
    categoria: Optional[str] = None # ← era "str" (no Optional): mismo problema.
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True