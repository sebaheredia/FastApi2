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
from typing import Optional
 
 
class UserCreate(BaseModel):
    """
    Schema de ENTRADA: lo que debe mandar el cliente para crear un usuario.
 
    Si el cliente manda un JSON sin 'nombre' o sin 'email',
    o si manda un numero donde se espera texto,
    FastAPI devuelve 422 Unprocessable Entity automaticamente
    sin llegar a ejecutar el endpoint.
    """
    nombre: str   # obligatorio, debe ser texto
    email: str    # obligatorio, debe ser texto
 
 
class UserResponse(BaseModel):
    """
    Schema de SALIDA: lo que devuelve la API al mostrar un usuario.
 
    Actua como filtro de seguridad: si en el futuro se agrega
    un campo 'password' al modelo User, NO apareceria en la respuesta
    porque no esta definido aca.
 
    Solo se muestran los campos que el cliente necesita ver.
    """
    id: int
    nombre: str
    email: str
    created_at: Optional[datetime] = None
    # Optional → puede ser None. Se usa porque en algunos contextos
    # (como los tests en memoria) el valor puede no estar disponible.
 
    class Config:
        from_attributes = True
        # Sin esto, Pydantic no puede leer un objeto SQLAlchemy.
        # Por defecto Pydantic espera un diccionario.
        # from_attributes=True le permite leer atributos de cualquier objeto.
 