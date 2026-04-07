from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./database.db"
# sqlite:///   → el tipo de base de datos (SQLite)
# ./database.db → el archivo donde se guardan los datos
#                 se crea solo si no existe
#                 es un archivo común, podés abrirlo con
#                 cualquier visor de SQLite

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    # check_same_thread=False es necesario porque FastAPI
    # puede atender varios requests al mismo tiempo (threads)
    # y SQLite por defecto solo permite un thread a la vez
)
# El engine es el "motor" — sabe cómo hablar con SQLite
# Traduce los comandos de Python a SQL

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# SessionLocal es una fábrica de sesiones
# Una sesión es como una "conversación" con la base de datos
# Cada request HTTP abre su propia sesión y la cierra al terminar
# autocommit=False → los cambios no se guardan hasta que
#                    vos hagas db.commit() explícitamente
# autoflush=False  → los cambios no se envían a la DB
#                    automáticamente antes de cada query

Base = declarative_base()
# Base es la clase madre de todos los modelos
# Cuando un modelo hereda de Base, SQLAlchemy sabe
# que ese modelo representa una tabla en la DB

def get_db():
    # Esta función abre una sesión y la cierra al terminar
    # El yield es como un return pero que "pausa" la función
    # FastAPI ejecuta lo que está antes del yield (abrir sesión)
    # luego ejecuta el endpoint
    # luego ejecuta lo que está después del yield (cerrar sesión)
    db = SessionLocal()  # abrir sesión
    try:
        yield db         # pausar y darle la sesión al endpoint
    finally:
        db.close()       # cerrar sesión (siempre, aunque haya error)