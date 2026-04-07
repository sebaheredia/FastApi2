# Cada función de test recibe "client" como argumento
# pytest busca una fixture llamada "client" en conftest.py
# la ejecuta y la pasa automáticamente al test
# No hay que importar nada ni hacer setup acá


# ─── Tests endpoints originales ──────────────────────────────

def test_ping(client):
    # client.get() simula una petición GET a /ping
    response = client.get("/ping")

    # assert verifica que la condición sea verdadera
    # si falla, el test falla y el pipeline se detiene
    assert response.status_code == 200  # debe responder OK
    assert response.json() == {"ping": "pong"}  # debe devolver este JSON


def test_hello(client):
    response = client.get("/hello/Seba")
    assert response.status_code == 200
    assert response.json() == {"message": "Hola, Seba!"}


def test_sum(client):
    # Los parámetros van en la URL como query params: ?a=2&b=3
    response = client.post("/sum?a=2&b=3")
    assert response.status_code == 200
    assert response.json() == {"result": 5.0}


def test_sum_negativos(client):
    response = client.post("/sum?a=-1&b=1")
    assert response.status_code == 200
    assert response.json() == {"result": 0.0}


# ─── Tests de usuarios ───────────────────────────────────────

def test_crear_usuario(client):
    # json={"nombre": "Seba", "email": "seba@test.com"}
    # arma el cuerpo del request en formato JSON
    # equivale a lo que mandaría un frontend o Postman
    response = client.post("/users", json={"nombre": "Seba", "email": "seba@test.com"})

    assert response.status_code == 201  # 201 = Created (recurso creado)
    data = response.json()
    assert data["nombre"] == "Seba"
    assert data["email"] == "seba@test.com"
    assert "id" in data  # verifica que la DB asignó un ID


def test_email_duplicado(client):
    # Primero crear un usuario con ese email
    client.post("/users", json={"nombre": "Seba", "email": "duplicado@test.com"})

    # Intentar crear otro usuario con el mismo email
    response = client.post("/users", json={"nombre": "Otro", "email": "duplicado@test.com"})

    # Debe fallar con 400 Bad Request
    assert response.status_code == 400
    # El mensaje de error debe mencionar "email"
    assert "email" in response.json()["detail"].lower()


def test_listar_usuarios(client):
    response = client.get("/users")
    assert response.status_code == 200
    # isinstance verifica que el resultado sea una lista
    # puede estar vacía — solo verificamos que sea lista
    assert isinstance(response.json(), list)


def test_obtener_usuario(client):
    # Primero crear un usuario para tener su ID
    created = client.post("/users", json={"nombre": "Ana", "email": "ana@test.com"})
    user_id = created.json()["id"]  # extraer el ID que asignó la DB

    # Buscarlo por ID
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "ana@test.com"


def test_usuario_no_encontrado(client):
    # ID 9999 no existe → debe devolver 404
    response = client.get("/users/9999")
    assert response.status_code == 404


def test_borrar_usuario(client):
    # Crear un usuario
    created = client.post("/users", json={"nombre": "Carlos", "email": "carlos@test.com"})
    user_id = created.json()["id"]

    # Borrarlo
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200  # borrado exitoso

    # Verificar que ya no existe
    # Si lo borramos bien, ahora debe dar 404
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404