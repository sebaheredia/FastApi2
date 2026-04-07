from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import get_db, Base
import models  # ← importar models ANTES de create_all
               # para que Base conozca todas las tablas

# Base de datos en memoria solo para tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# Crear las tablas ANTES de importar la app
Base.metadata.create_all(bind=engine_test)

# Recién ahora importar la app
from main import app

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ─── Tests endpoints originales ──────────────────────────────

def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}

def test_hello():
    response = client.get("/hello/Seba")
    assert response.status_code == 200
    assert response.json() == {"message": "Hola, Seba!"}

def test_sum():
    response = client.post("/sum?a=2&b=3")
    assert response.status_code == 200
    assert response.json() == {"result": 5.0}

def test_sum_negativos():
    response = client.post("/sum?a=-1&b=1")
    assert response.status_code == 200
    assert response.json() == {"result": 0.0}


# ─── Tests de usuarios ───────────────────────────────────────

def test_crear_usuario():
    response = client.post("/users", json={"nombre": "Seba", "email": "seba@test.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Seba"
    assert data["email"] == "seba@test.com"
    assert "id" in data

def test_email_duplicado():
    client.post("/users", json={"nombre": "Seba", "email": "duplicado@test.com"})
    response = client.post("/users", json={"nombre": "Otro", "email": "duplicado@test.com"})
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()

def test_listar_usuarios():
    response = client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_obtener_usuario():
    created = client.post("/users", json={"nombre": "Ana", "email": "ana@test.com"})
    user_id = created.json()["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "ana@test.com"

def test_usuario_no_encontrado():
    response = client.get("/users/9999")
    assert response.status_code == 404

def test_borrar_usuario():
    created = client.post("/users", json={"nombre": "Carlos", "email": "carlos@test.com"})
    user_id = created.json()["id"]
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404