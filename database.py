"""
╔══════════════════════════════════════════════════════════════╗
║                        database.py                           ║
║   Configura la conexion a la base de datos.                  ║
║   Todos los demas archivos importan desde aca.               ║
╚══════════════════════════════════════════════════════════════╝
"""
 
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
 
# Lee la URL de conexion desde las variables de entorno.
# En Render, DATABASE_URL es inyectada automaticamente al arrancar el contenedor.
# En desarrollo local, no existe esa variable → usa SQLite como fallback.
# Formato SQLite:     sqlite:///./database.db  (archivo en el disco local)
# Formato PostgreSQL: postgresql://user:pass@host/dbname
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./database.db"
)
 
# SQLite necesita check_same_thread=False porque FastAPI puede atender
# multiples requests en paralelo (threads distintos), y SQLite por defecto
# solo permite un thread a la vez.
# PostgreSQL no tiene esta limitacion → connect_args vacio.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
 
# El engine es el "motor": sabe como hablar con la base de datos.
# Traduce los comandos de Python/SQLAlchemy a SQL.
# Se crea una sola vez al arrancar la app.
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)
 
# SessionLocal es una fabrica de sesiones.
# Una sesion es una "conversacion" con la DB: agrupa operaciones
# que se ejecutan juntas y pueden confirmarse o revertirse.
# autocommit=False → los cambios no se guardan solos, hay que llamar a db.commit()
# autoflush=False  → los cambios no se envian a la DB hasta el commit
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
# Base es la clase madre de todos los modelos.
# Cuando User hereda de Base, SQLAlchemy sabe que User representa una tabla.
Base = declarative_base()
 
 
def get_db():
    """
    Generador que abre una sesion de DB al inicio de cada request
    y la cierra al terminar, incluso si hubo un error.
 
    FastAPI llama a esta funcion automaticamente cuando un endpoint
    declara: db: Session = Depends(get_db)
 
    El yield pausa la funcion y entrega la sesion al endpoint.
    Cuando el endpoint termina, la ejecucion vuelve al finally
    y la sesion se cierra.
    """
    db = SessionLocal()  # abrir sesion
    try:
        yield db         # entregar sesion al endpoint
    finally:
        db.close()       # cerrar siempre, aunque haya excepcion