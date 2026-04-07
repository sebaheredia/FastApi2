from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import engine, get_db


# lifespan reemplaza al create_all suelto
# Solo se ejecuta cuando uvicorn levanta el servidor real
# Durante los tests NO se ejecuta — pytest lo evita
# Así conftest.py puede crear las tablas en la DB correcta primero
@asynccontextmanager
async def lifespan(app):
    # Todo lo que está antes del yield corre al ARRANCAR el servidor
    models.Base.metadata.create_all(bind=engine)
    yield
    # Todo lo que está después del yield corre al APAGAR el servidor
    # (vacío por ahora)


# Se le pasa lifespan a FastAPI para que lo use al arrancar
app = FastAPI(lifespan=lifespan)


# ─── Endpoints originales ─────────────────────────────────────────────────────

@app.get("/ping")
def ping():
    return {"ping": "pong"}


@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Hola, {name}!"}


@app.post("/sum")
def sum_numbers(a: float, b: float):
    return {"result": a + b}


# ─── Endpoints de usuarios ────────────────────────────────────────────────────


# ¿Qué es un decorador como @app.post(...)?
# ─────────────────────────────────────────
# En Python, una función puede ser "decorada" con @algo, lo que significa
# que esa función se registra o modifica de alguna forma antes de usarse.
#
# @app.post("/users") le dice a FastAPI:
#   "cuando alguien haga una petición HTTP POST a la URL /users,
#    ejecutá la función que viene justo abajo"
#
# FastAPI NO necesita que vos llames a create_user() directamente.
# FastAPI registra la función internamente y la llama automáticamente
# cuando llega la petición correcta.
#
# Es como registrar un manejador de eventos:
# "cuando pase X, ejecutar Y"


@app.post(
    "/users",                              # URL a la que responde este endpoint
                                           # HTTP POST = se usa para CREAR recursos
                                           # (GET = leer, POST = crear,
                                           #  PUT = actualizar, DELETE = borrar)

    response_model=schemas.UserResponse,   # Le dice a FastAPI qué forma tiene la
                                           # respuesta que va a devolver.
                                           # FastAPI usa esto para:
                                           # 1) validar que la respuesta es correcta
                                           # 2) filtrar campos que no deben mostrarse
                                           # 3) generar la documentación automática
                                           # UserResponse está definido en schemas.py
                                           # y dice: devolver id, nombre, email, created_at

    status_code=201                        # Código HTTP que se devuelve al crear algo.
                                           # 200 = OK (respuesta normal)
                                           # 201 = Created (recurso creado exitosamente)
                                           # 400 = Bad Request (el cliente mandó algo mal)
                                           # 404 = Not Found (no existe lo que buscan)
                                           # 500 = Internal Server Error (bug en el servidor)
)
def create_user(
    user: schemas.UserCreate,              # Argumento 1: los datos que mandó el cliente
                                           # FastAPI lee el cuerpo del request (JSON)
                                           # y lo convierte automáticamente a un objeto
                                           # UserCreate (definido en schemas.py)
                                           # Si el JSON no tiene la forma correcta,
                                           # FastAPI devuelve 422 automáticamente
                                           # sin que vos hagas nada

    db: Session = Depends(get_db)          # Argumento 2: la sesión de base de datos
                                           # Depends(get_db) es el sistema de inyección
                                           # de dependencias de FastAPI:
                                           # "antes de ejecutar esta función,
                                           #  ejecutá get_db() y pasame el resultado
                                           #  como el argumento db"
                                           # get_db() está en database.py y abre
                                           # una conexión a SQLite
                                           # FastAPI la cierra automáticamente
                                           # al terminar el request
):
    """Crear un nuevo usuario. Falla con 400 si el email ya existe."""

    # db.query(models.User) → SELECT * FROM users
    # .filter(...)          → WHERE email = user.email
    # .first()              → LIMIT 1 (devuelve el primero o None si no hay)
    # Si existing no es None, significa que el email ya está en la DB
    existing = db.query(models.User).filter(models.User.email == user.email).first()

    if existing:
        # HTTPException interrumpe la función y devuelve una respuesta de error
        # status_code=400 → Bad Request (el cliente mandó un email ya usado)
        # detail → mensaje de error que verá el cliente en el JSON de respuesta
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    # Crear un objeto User (el modelo de SQLAlchemy definido en models.py)
    # Este objeto representa una fila nueva en la tabla "users"
    # Todavía NO está en la base de datos
    db_user = models.User(nombre=user.nombre, email=user.email)

    # db.add() → le dice a SQLAlchemy "quiero insertar este objeto en la DB"
    # Todavía NO ejecuta el INSERT — lo marca como pendiente
    db.add(db_user)

    # db.commit() → ejecuta el INSERT en la DB y confirma la transacción
    # Si algo falla antes del commit, los cambios no se guardan (rollback automático)
    db.commit()

    # db.refresh() → vuelve a leer el objeto desde la DB
    # Necesario para obtener valores que la DB genera automáticamente,
    # como el id (autoincremental) y created_at (generado por el servidor)
    # Sin refresh, db_user.id sería None
    db.refresh(db_user)

    # Devolver el objeto usuario
    # FastAPI lo convierte automáticamente a JSON usando el response_model
    # Solo incluye los campos definidos en UserResponse: id, nombre, email, created_at
    return db_user


@app.get("/users", response_model=List[schemas.UserResponse])
# List[schemas.UserResponse] → la respuesta es una LISTA de usuarios
# List viene de typing y significa "lista de elementos del tipo indicado"
def list_users(db: Session = Depends(get_db)):
    """Listar todos los usuarios."""

    # db.query(models.User).all() → SELECT * FROM users
    # Devuelve una lista de objetos User (puede ser lista vacía)
    return db.query(models.User).all()


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
# {user_id} en la URL es un parámetro de ruta
# FastAPI lo captura y lo pasa como argumento a la función
# Ejemplo: GET /users/42 → user_id = 42
def get_user(
    user_id: int,                          # FastAPI convierte automáticamente el
                                           # texto de la URL al tipo indicado (int)
                                           # Si alguien pone /users/abc → error 422
    db: Session = Depends(get_db)
):
    """Obtener un usuario por ID. Falla con 404 si no existe."""

    # SELECT * FROM users WHERE id = user_id LIMIT 1
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        # 404 = Not Found: el recurso que buscan no existe
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return user


@app.delete("/users/{user_id}", response_model=schemas.UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Borrar un usuario por ID. Falla con 404 si no existe."""

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # db.delete() → marca el objeto para eliminar (DELETE FROM users WHERE id = ...)
    db.delete(user)

    # commit() → ejecuta el DELETE en la DB
    db.commit()

    # Devolvemos el usuario que se acaba de borrar
    # (así el cliente sabe qué se eliminó)
    return user