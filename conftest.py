import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
# Base    → la clase madre de los modelos, necesaria para crear las tablas
# get_db  → la dependencia real que vamos a reemplazar durante los tests


# URL de la base de datos de test
# sqlite:///:memory: significa que la DB vive en RAM
# no crea ningún archivo en disco
# se destruye automáticamente al terminar los tests
TEST_DATABASE_URL = "sqlite:///:memory:"


# @pytest.fixture indica que esta función es una fixture
# scope="session" → se ejecuta UNA SOLA VEZ para toda la corrida de tests
# no se repite por cada test individual
@pytest.fixture(scope="session")
def engine_test():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
        # check_same_thread=False → necesario para SQLite con múltiples threads
    )

    # Importar models ACÁ es crítico
    # Base necesita conocer todos los modelos (User, etc.)
    # ANTES de ejecutar create_all
    # Si no se importa, Base no sabe que existe la tabla users
    # y create_all no crea nada
    import models

    # Crea todas las tablas definidas en models.py
    # en la base de datos en memoria
    # Equivale a ejecutar: CREATE TABLE users (...)
    Base.metadata.create_all(bind=engine)

    # yield pausa la función y entrega el engine a quien lo pidió
    # todo lo que está ANTES del yield = setup (preparación)
    # todo lo que está DESPUÉS del yield = teardown (limpieza)
    yield engine

    # Esto se ejecuta al terminar TODOS los tests
    # Borra todas las tablas de la DB en memoria
    # En este caso no es estrictamente necesario porque la DB
    # en memoria se destruye sola, pero es buena práctica
    Base.metadata.drop_all(bind=engine)


# scope="function" → se ejecuta UNA VEZ POR CADA TEST
# engine_test como argumento → pytest inyecta la fixture anterior automáticamente
@pytest.fixture(scope="function")
def db_session(engine_test):
    # Crea una fábrica de sesiones conectada al engine de test
    TestingSessionLocal = sessionmaker(
        autocommit=False,  # los cambios no se guardan solos
        autoflush=False,   # no se envían a la DB hasta el commit
        bind=engine_test   # conectada a la DB en memoria
    )

    # Abre una sesión nueva para este test
    db = TestingSessionLocal()

    # Entrega la sesión al test
    yield db

    # Al terminar el test, cierra la sesión
    # Esto libera la conexión a la DB
    db.close()


# scope="function" → una vez por test
# db_session como argumento → pytest inyecta la fixture anterior
@pytest.fixture(scope="function")
def client(db_session):
    # Importar la app ACÁ, no al principio del archivo
    # Así nos aseguramos que las tablas ya existen en la DB
    # antes de que la app arranque
    from main import app

    # Esta función reemplaza a get_db() durante los tests
    # En lugar de abrir una conexión nueva a la DB real,
    # devuelve la sesión de test que ya tenemos abierta
    def override_get_db():
        try:
            yield db_session  # devuelve la sesión de test
        finally:
            pass  # no cerramos acá, db_session.close() lo hace arriba

    # Registra el reemplazo en FastAPI
    # Cuando un endpoint pida Depends(get_db),
    # FastAPI llamará a override_get_db() en cambio
    # → los endpoints trabajan con la DB de test sin saberlo
    app.dependency_overrides[get_db] = override_get_db

    # Crea el cliente de test
    # TestClient simula peticiones HTTP sin levantar un servidor real
    # el "with" garantiza que el cliente se cierra correctamente al salir
    with TestClient(app) as c:
        yield c  # entrega el cliente al test

    # Al terminar el test, limpia el override
    # Así el próximo test empieza con la app en estado limpio
    app.dependency_overrides.clear()