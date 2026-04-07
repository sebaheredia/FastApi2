def test_ping(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}


def test_hello(client):
    response = client.get("/hello/Seba")
    assert response.status_code == 200
    assert response.json() == {"message": "Hola, Seba!"}


def test_sum(client):
    response = client.post("/sum?a=2&b=3")
    assert response.status_code == 200
    assert response.json() == {"result": 5.0}


def test_sum_negativos(client):
    response = client.post("/sum?a=-1&b=1")
    assert response.status_code == 200
    assert response.json() == {"result": 0.0}


def test_crear_usuario(client):
    response = client.post("/users", json={"nombre": "Seba", "email": "seba@test.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Seba"
    assert data["email"] == "seba@test.com"
    assert "id" in data


def test_email_duplicado(client):
    client.post("/users", json={"nombre": "Seba", "email": "duplicado@test.com"})
    response = client.post("/users", json={"nombre": "Otro", "email": "duplicado@test.com"})
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_listar_usuarios(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_obtener_usuario(client):
    created = client.post("/users", json={"nombre": "Ana", "email": "ana@test.com"})
    user_id = created.json()["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "ana@test.com"


def test_usuario_no_encontrado(client):
    response = client.get("/users/9999")
    assert response.status_code == 404


def test_borrar_usuario(client):
    created = client.post("/users", json={"nombre": "Carlos", "email": "carlos@test.com"})
    user_id = created.json()["id"]
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404