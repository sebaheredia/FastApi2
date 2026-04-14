"""
╔══════════════════════════════════════════════════════════════╗
║                         main.py                              ║
║   Punto de entrada de la API REST. Define todos los          ║
║   endpoints que el frontend puede llamar via HTTP.           ║
╚══════════════════════════════════════════════════════════════╝
"""
 
# ─── Importaciones ────────────────────────────────────────────
 
from fastapi import FastAPI, Depends, HTTPException
# FastAPI    → el framework que crea la API
# Depends    → sistema de inyeccion de dependencias
#              permite que FastAPI llame a get_db() automaticamente
#              antes de ejecutar cada endpoint
# HTTPException → para devolver errores HTTP con codigo y mensaje
 
from fastapi.middleware.cors import CORSMiddleware
# Middleware que permite requests desde otros dominios
# Sin esto el navegador bloquea las llamadas del frontend al backend
# porque estan en dominios distintos (onrender.com vs onrender.com/otro)
 
from sqlalchemy.orm import Session
# Tipo de dato para tipar el parametro db en los endpoints
# Le dice a Python (y al lector) que db es una sesion de base de datos
 
from typing import List
# Para indicar que un endpoint devuelve una LISTA de elementos
# en lugar de un solo elemento
 
import os
# Para leer variables de entorno con os.environ.get()
 
import models   # define la tabla users en la DB (ver models.py)
import schemas  # define la forma del JSON de entrada y salida (ver schemas.py)
from database import engine, get_db
# engine  → la conexion a la base de datos
# get_db  → funcion que abre y cierra sesiones de DB por request
 

def add_categoria(user):
    if user.edad < 18:
        categoria = "menor"
    elif user.edad < 65:
        categoria = "adulto"
    else:
        categoria = "mayor"

    return {
        **user.__dict__,
        "categoria": categoria
    }
 
# ─── Creacion de la app ───────────────────────────────────────
 
app = FastAPI()
# Crea la aplicacion web
# Esta variable "app" es el punto de entrada que busca uvicorn
# cuando se ejecuta: uvicorn main:app
 
 
# ─── CORS ─────────────────────────────────────────────────────
 
# IMPORTANTE: el middleware debe agregarse ANTES de definir
# los endpoints. Si se pone despues, no se aplica correctamente.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # permite requests desde cualquier dominio
                           # en produccion se podria restringir a
                           # solo el dominio del frontend
    allow_methods=["*"],   # permite GET, POST, DELETE, PUT, etc
    allow_headers=["*"],   # permite cualquier header HTTP
)
# NOTA: add_middleware es una llamada de funcion normal, NO un decorador.
# No lleva @ al principio. Es un error comun confundirlo con @app.get()
 
 
# ─── Endpoints de diagnostico ─────────────────────────────────
 
@app.get("/ping")
def ping():
    # Endpoint de health check: verifica que el servidor esta vivo
    # Es lo primero que se testea cuando se despliega el servicio
    return {"ping": "pong"}
 
 
@app.get("/hello/{name}")
def hello(name: str):
    # {name} es un parametro de ruta: se lee directamente de la URL
    # Si alguien llama GET /hello/Seba → name = "Seba"
    # FastAPI lo convierte automaticamente al tipo declarado (str)
    return {"message": f"Hola, {name}!"}
 
 
@app.post("/sum")
def sum_numbers(a: float, b: float):
    # a y b son query parameters: vienen en la URL como /sum?a=5&b=3
    # FastAPI los convierte automaticamente a float
    return {"result": a + b}
 
 
@app.get("/db-info")
def db_info():
    # Endpoint de diagnostico: muestra a que base de datos esta conectada la app
    # Util para verificar en produccion si esta usando PostgreSQL o SQLite
    # DATABASE_URL viene de database.py (importado indirectamente via get_db)
    from database import DATABASE_URL
    return {"database_url": DATABASE_URL}
 
 
@app.get("/config")
def config():
    # Muestra configuracion del entorno actual
    # os.environ.get("ENVIRONMENT", "unknown") lee la variable de entorno
    # ENVIRONMENT. Si no existe, devuelve "unknown" como valor por defecto.
    # Render inyecta esta variable al arrancar el contenedor
    return {
        "allowed_origins": "*",
        "environment": os.environ.get("ENVIRONMENT", "unknown")
    }
 
 
# ─── Endpoints de usuarios ────────────────────────────────────
 
@app.post(
    "/users",
    response_model=schemas.UserResponse,  # forma del JSON que devuelve
    status_code=201                        # 201 = Created (recurso creado)
)
def create_user(
    user: schemas.UserCreate,       # datos que manda el cliente en JSON
                                    # FastAPI los valida con Pydantic automaticamente
                                    # si falta nombre o email → 422 automatico
    db: Session = Depends(get_db)   # FastAPI llama a get_db() antes de ejecutar
                                    # esto y pasa la sesion de DB como argumento
):
    # Verificar si el email ya existe en la base de datos
    # db.query(models.User)           → SELECT * FROM users
    # .filter(models.User.email == user.email) → WHERE email = ?
    # .first()                        → LIMIT 1 (devuelve None si no hay resultado)
    existing = db.query(models.User).filter(models.User.email == user.email).first()
 
    if existing:
        # HTTPException interrumpe la funcion y devuelve un error HTTP
        # 400 Bad Request = el cliente mando datos incorrectos
        raise HTTPException(status_code=400, detail="El email ya está registrado")
 
    # Crear el objeto User (todavia NO esta en la DB, solo en memoria)
    db_user = models.User(
    nombre=user.nombre,
    email=user.email,
    edad=user.edad
    )
 
    db.add(db_user)     # marcar para insertar (todavia no ejecuta el INSERT)
    db.commit()         # ejecutar el INSERT en la DB y confirmar la transaccion
    db.refresh(db_user) # releer el objeto desde la DB para obtener el id
                        # y created_at generados automaticamente por PostgreSQL
                        # sin refresh, db_user.id seria None
    
    # FastAPI convierte db_user a JSON usando el schema UserResponse
    # solo incluye los campos definidos en UserResponse
    

    return add_categoria(db_user)
 
 
@app.get("/users", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    # List[schemas.UserResponse] → devuelve una LISTA de usuarios
    # db.query(models.User).all() → SELECT * FROM users (sin filtros)
    # puede devolver lista vacia [] si no hay usuarios
    return [add_categoria(u) for u in db.query(models.User).all()] 
 
@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,                  # parametro de ruta, convertido a int automaticamente
                                    # si alguien pone /users/abc → error 422
    db: Session = Depends(get_db)
):
    # SELECT * FROM users WHERE id = user_id LIMIT 1
    user = db.query(models.User).filter(models.User.id == user_id).first()
 
    if not user:
        # 404 Not Found = el recurso que buscan no existe
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
 
    return add_categoria(user)
 
 
@app.delete("/users/{user_id}", response_model=schemas.UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
 
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
 
    db.delete(user)  # marcar para eliminar (DELETE FROM users WHERE id = ?)
    db.commit()      # ejecutar el DELETE en la DB
 
    # devuelve el usuario que se acaba de borrar
    # asi el cliente sabe exactamente que se elimino
    return add_categoria(user)