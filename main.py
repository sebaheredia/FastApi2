from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import engine, get_db
from fastapi.middleware.cors import CORSMiddleware


# NO hay create_all acá
app = FastAPI()


@app.get("/ping")
def ping():
    return {"ping": "pong"}


@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Hola, {name}!"}


@app.post("/sum")
def sum_numbers(a: float, b: float):
    return {"result": a + b}


@app.post("/users", response_model=schemas.UserResponse, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    db_user = models.User(nombre=user.nombre, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@app.delete("/users/{user_id}", response_model=schemas.UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    return user

@app.get("/db-info")
def db_info():
    from database import DATABASE_URL
    return {"database_url": DATABASE_URL}

@app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción poner la URL del frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/config")
def config():
    import os
    return {
        "allowed_origins": "*",
        "environment": os.environ.get("ENVIRONMENT", "unknown")
    }