"""
╔══════════════════════════════════════════════════════════════╗
║                         models.py                            ║
║   Define la estructura de las tablas en la base de datos.    ║
║   Cada clase = una tabla. Cada Column = una columna.         ║
╚══════════════════════════════════════════════════════════════╝
"""
 
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base
 
 
class User(Base):
    """
    Representa la tabla 'users' en la base de datos.
    Cada instancia de User = una fila en la tabla.
    """
 
    __tablename__ = "users"
    # Nombre real de la tabla en SQL.
    # SQLAlchemy genera: CREATE TABLE users (...)
 
    id = Column(
        Integer,
        primary_key=True,  # clave primaria: identifica univocamente cada fila
        index=True         # crea un indice para que las busquedas por id sean rapidas
    )
    # SQLAlchemy + PostgreSQL asignan el valor automaticamente (1, 2, 3...)
    # No hay que pasarlo al crear un User
 
    nombre = Column(
        String,
        nullable=False     # no puede estar vacio: es obligatorio
    )
 
    email = Column(
        String,
        unique=True,       # no puede haber dos filas con el mismo email
                           # la DB devuelve error si se intenta insertar un duplicado
        index=True,        # indice para busquedas rapidas por email
        nullable=False
    )
 
    created_at = Column(
        DateTime,
        server_default=func.now()
        # server_default → la DB asigna el valor automaticamente al insertar
        # func.now()     → la fecha y hora actual del servidor de DB
        # No hay que pasarla al crear un User
    )

    edad = Column(Integer)