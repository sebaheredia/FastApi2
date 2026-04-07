from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    # Esta clase representa la tabla "users" en SQLite
    # Cada instancia de User = una fila en la tabla
    # Cada atributo Column = una columna

    __tablename__ = "users"
    # Este es el nombre real de la tabla en la DB
    # SQLAlchemy crea: CREATE TABLE users (...)

    id = Column(Integer, primary_key=True, index=True)
    # Integer    → número entero
    # primary_key=True → es la clave primaria, identifica
    #                    unívocamente cada fila
    # index=True → crea un índice para búsquedas rápidas
    # SQLite asigna el valor automáticamente (1, 2, 3...)

    nombre = Column(String, nullable=False)
    # String     → texto
    # nullable=False → no puede estar vacío (obligatorio)

    email = Column(String, unique=True, index=True, nullable=False)
    # unique=True → no puede haber dos filas con el mismo email
    #               SQLite devuelve error si intentás insertar
    #               un email duplicado

    created_at = Column(DateTime, server_default=func.now())
    # DateTime       → fecha y hora
    # server_default=func.now() → SQLite pone la fecha y hora
    #                             actual automáticamente al insertar
    #                             No tenés que pasarla vos