"""
╔══════════════════════════════════════════════════════════════╗
║                        conftest.py                           ║
║   Configuracion de pytest. Se ejecuta automaticamente        ║
║   antes de cualquier test. Define fixtures reutilizables.    ║
╚══════════════════════════════════════════════════════════════╝
"""
 
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
 
# Usar un archivo SQLite temporal en lugar de la DB real.
# Esto garantiza que los tests no tocan los datos de produccion
# y que cada corrida de tests empieza con una DB limpia.
TEST_DB_FILE = "./test_database.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"
 
# Crear el engine de test apuntando al archivo temporal
engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
 
# Fabrica de sesiones conectada al engine de test
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_test
)
 
# IMPORTANTE: importar models ANTES de create_all
# para que Base conozca la tabla 'users'.
# Sin este import, create_all no crea ninguna tabla.
import models
 
# Crear las tablas en la DB de test.
# Esto debe hacerse ANTES de importar la app,
# porque la app al importarse puede intentar usar las tablas.
Base.metadata.create_all(bind=engine_test)
 
# Importar la app DESPUES de crear las tablas
from main import app
 
 
def override_get_db():
    """
    Reemplaza get_db() durante los tests.
    En lugar de abrir una sesion a la DB real (PostgreSQL o SQLite de produccion),
    abre una sesion al archivo de test.
    Los endpoints no saben que estan usando una DB distinta.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 
# Registrar el reemplazo en FastAPI.
# A partir de aca, cada vez que un endpoint pida Depends(get_db),
# FastAPI llamara a override_get_db() en cambio.
app.dependency_overrides[get_db] = override_get_db
 
 
@pytest.fixture
def client():
    """
    Fixture que crea un TestClient para cada test.
    TestClient simula peticiones HTTP sin levantar un servidor real.
    El 'with' garantiza que el cliente se inicializa y cierra correctamente.
    """
    with TestClient(app) as c:
        yield c  # entrega el cliente al test
 
 
def pytest_sessionfinish(session, exitstatus):
    """
    Hook de pytest que se ejecuta automaticamente cuando terminan TODOS los tests.
    Borra el archivo de DB temporal para no dejar residuos en el disco.
    """
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)