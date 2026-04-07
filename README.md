# FastApi2 — API REST con CI/CD y Base de Datos

Proyecto de ejemplo de una API REST construida con **FastAPI** (Python), con integración y despliegue continuo (CI/CD) usando **GitHub Actions**, **GHCR** y **Render**.

---

## Índice

1. [¿Qué es esta API?](#1-qué-es-esta-api)
2. [Qué es el backend y cómo se interactúa con él](#2-qué-es-el-backend-y-cómo-se-interactúa-con-él)
3. [Estructura del repositorio](#3-estructura-del-repositorio)
4. [La base de datos](#4-la-base-de-datos)
5. [Los tres archivos clave de la DB](#5-los-tres-archivos-clave-de-la-db)
6. [Cómo interactúan database, models y schemas](#6-cómo-interactúan-database-models-y-schemas)
7. [La aplicación Python — main.py](#7-la-aplicación-python--mainpy)
8. [Tests automáticos](#8-tests-automáticos)
9. [Dependencias](#9-dependencias)
10. [Docker y el problema de persistencia](#10-docker-y-el-problema-de-persistencia)
11. [CI/CD con GitHub Actions](#11-cicd-con-github-actions)
12. [GHCR — Dónde se guardan las imágenes](#12-ghcr--dónde-se-guardan-las-imágenes)
13. [Despliegue en Render](#13-despliegue-en-render)
14. [Flujo completo de trabajo](#14-flujo-completo-de-trabajo)
15. [Cómo probar el servicio desplegado](#15-cómo-probar-el-servicio-desplegado)
16. [Cómo correr el proyecto localmente](#16-cómo-correr-el-proyecto-localmente)

---

## 1. ¿Qué es esta API?

Una **API REST** es un servicio que responde a peticiones HTTP. No tiene pantallas ni formularios — es puro backend. Los clientes (navegadores, aplicaciones móviles, Postman, otros servicios) le mandan datos en formato JSON y reciben respuestas en JSON.

Esta API expone los siguientes endpoints:

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/ping` | Verificación de que el servidor está activo |
| GET | `/hello/{name}` | Saludo personalizado |
| POST | `/sum` | Suma dos números |
| POST | `/users` | Crear un usuario |
| GET | `/users` | Listar todos los usuarios |
| GET | `/users/{id}` | Obtener un usuario por ID |
| DELETE | `/users/{id}` | Borrar un usuario |

---

## 2. Qué es el backend y cómo se interactúa con él

### FastAPI no tiene pantallas

Esta es la confusión más común. FastAPI es solo el backend — no muestra formularios ni le pregunta nada al usuario. No hay campo de texto "escribí tu nombre acá".

```
Lo que se imagina:              Lo que es realmente:
──────────────────              ────────────────────────────────────
[Pantalla de registro]          [Postman / curl / frontend / app]
  Nombre: ____                              │
  Email:  ____          ──JSON──►      [FastAPI]
  [Registrar]                               │
                                            ▼
                                       [Base de datos]
```

El que muestra la pantalla y recoge los datos del usuario es **otro programa** (un frontend en React, una app móvil, Postman para pruebas). Ese programa arma el JSON y se lo manda a FastAPI.

### ¿Qué es JSON?

JSON es el formato en que viajan los datos. Es texto plano con estructura de clave-valor:

```json
{
    "nombre": "Seba",
    "email": "seba@gmail.com"
}
```

Cuando alguien quiere crear un usuario, manda ese JSON en el cuerpo del request HTTP POST a `/users`. FastAPI lo recibe, lo valida y lo guarda en la base de datos.

### Cómo interactuar con la API sin un frontend

FastAPI genera automáticamente una interfaz web en `/docs` (Swagger UI) que permite probar todos los endpoints desde el navegador:

```
https://fastapi2-production.onrender.com/docs
```

También se puede usar curl desde la terminal:

```bash
# Crear un usuario
curl -X POST "https://fastapi2-production.onrender.com/users" \
     -H "Content-Type: application/json" \
     -d '{"nombre": "Seba", "email": "seba@gmail.com"}'

# Listar usuarios
curl https://fastapi2-production.onrender.com/users

# Obtener usuario con ID 1
curl https://fastapi2-production.onrender.com/users/1

# Borrar usuario con ID 1
curl -X DELETE https://fastapi2-production.onrender.com/users/1
```

---

## 3. Estructura del repositorio

```
FastApi2/
├── main.py          # Endpoints de la API
├── database.py      # Conexión a la base de datos
├── models.py        # Definición de las tablas (SQLAlchemy)
├── schemas.py       # Validación de datos entrada/salida (Pydantic)
├── test_main.py     # Tests automáticos
├── requirements.txt # Dependencias Python
├── Dockerfile       # Instrucciones para construir la imagen Docker
└── .github/
    └── workflows/
        └── ci.yml   # Pipeline de CI/CD
```

---

## 4. La base de datos

### ¿Qué base de datos se usa?

**SQLite** para desarrollo local y tests. Es una base de datos que vive en un único archivo (`database.db`) en el disco. No requiere instalar ningún servidor — Python la maneja directamente.

**PostgreSQL** para producción en Render. Es una base de datos que corre en un servidor separado, fuera del contenedor Docker.

### ¿Dónde está físicamente la tabla de usuarios?

Esta es una pregunta crítica. La respuesta depende del entorno:

| Entorno | Dónde vive la DB | Qué pasa si se reinicia |
|---|---|---|
| **Local (sin Docker)** | Archivo `database.db` en tu carpeta | Persiste — los datos no se pierden |
| **Local (con Docker)** | Archivo `/app/database.db` dentro del contenedor | Se pierde al reiniciar el contenedor |
| **Tests** | Memoria RAM (`sqlite:///:memory:`) | Se borra al terminar los tests (intencional) |
| **Producción (Render)** | PostgreSQL en servidor externo | Persiste — independiente del contenedor |

### El problema con SQLite dentro de Docker

Cuando Render redesplega la aplicación (por ejemplo, después de un push a main), destruye el contenedor viejo y crea uno nuevo completamente limpio. El archivo `database.db` que estaba adentro del contenedor viejo se pierde para siempre — todos los usuarios registrados desaparecen.

```
Push a main
    │
    ▼
Render destruye el contenedor viejo
    │  ← database.db desaparece con el contenedor
    ▼
Render crea contenedor nuevo
    │  ← database.db está vacía
    ▼
Todos los usuarios perdidos ❌
```

### La solución: base de datos externa

La base de datos tiene que vivir fuera del contenedor, en un servidor separado. Así el contenedor puede ser destruido y recreado sin tocar los datos:

```
Contenedor Docker          Servidor PostgreSQL (Render)
─────────────────          ──────────────────────────────
main.py                    tabla users
database.py   ────────►    id | nombre | email | created_at
models.py                  1  | Seba   | s@g.com | 2026-04-07
schemas.py                 2  | Ana    | a@g.com | 2026-04-07

Redespliegue:
Contenedor nuevo ────────► mismos datos ✅
```

---

## 5. Los tres archivos clave de la DB

### `database.py` — La conexión

Define cómo conectarse a la base de datos y crea la fábrica de sesiones.

```python
DATABASE_URL = "sqlite:///./database.db"
# Formato: tipo://ruta
# sqlite:///  → tipo de DB (SQLite)
# ./database.db → archivo en la carpeta actual

engine = create_engine(DATABASE_URL, ...)
# El engine es el "motor" — traduce Python a SQL
# Sabe cómo hablar con SQLite (o PostgreSQL, MySQL, etc)

SessionLocal = sessionmaker(...)
# Fábrica de sesiones
# Una sesión es una "conversación" con la DB
# Cada request HTTP abre su propia sesión

Base = declarative_base()
# Clase madre de todos los modelos
# Los modelos que hereden de Base se convierten en tablas

def get_db():
    db = SessionLocal()   # abrir sesión
    try:
        yield db          # darle la sesión al endpoint
    finally:
        db.close()        # cerrar sesión siempre (aunque haya error)
```

### `models.py` — Las tablas

Define la estructura de las tablas en la base de datos. Cada clase es una tabla, cada atributo Column es una columna.

```python
class User(Base):
    __tablename__ = "users"   # nombre real de la tabla en SQL

    id = Column(Integer, primary_key=True)  # autoincremental: 1, 2, 3...
    nombre = Column(String, nullable=False)  # texto, obligatorio
    email = Column(String, unique=True)      # texto, único por fila
    created_at = Column(DateTime, server_default=func.now())  # fecha automática
```

SQLAlchemy genera automáticamente este SQL:
```sql
CREATE TABLE users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT    NOT NULL,
    email      TEXT    NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### `schemas.py` — La validación

Define qué datos entran y salen de la API. Son clases de Pydantic — no tocan la base de datos, solo validan y dan forma a los datos JSON.

```python
class UserCreate(BaseModel):
    # Lo que debe mandar el cliente para crear un usuario
    nombre: str   # obligatorio
    email: str    # obligatorio
    # Si falta alguno → FastAPI devuelve 422 automáticamente

class UserResponse(BaseModel):
    # Lo que devuelve la API al mostrar un usuario
    id: int
    nombre: str
    email: str
    created_at: Optional[datetime] = None
    # Si el modelo tuviera un campo "password", no aparecería acá
    # UserResponse actúa como filtro de seguridad
```

---

## 6. Cómo interactúan database, models y schemas

El flujo completo de un `POST /users`:

```
1. Cliente manda JSON:
   {"nombre": "Seba", "email": "seba@gmail.com"}
            │
            ▼
2. Pydantic valida con UserCreate:
   ¿tiene nombre? ✅   ¿tiene email? ✅
   Si falta algo → 422 Unprocessable Entity
            │
            ▼
3. FastAPI llama a create_user(user, db)
   user = UserCreate(nombre="Seba", email="seba@gmail.com")
   db   = sesión de SQLite abierta por get_db()
            │
            ▼
4. SQLAlchemy consulta si el email ya existe:
   SELECT * FROM users WHERE email = "seba@gmail.com" LIMIT 1
   Si existe → 400 Bad Request "El email ya está registrado"
            │
            ▼
5. SQLAlchemy crea la fila nueva:
   INSERT INTO users (nombre, email) VALUES ("Seba", "seba@gmail.com")
            │
            ▼
6. db.refresh() lee el objeto completo desde la DB:
   User(id=1, nombre="Seba", email="seba@gmail.com", created_at=...)
            │
            ▼
7. Pydantic convierte User → JSON usando UserResponse:
   {"id": 1, "nombre": "Seba", "email": "seba@gmail.com", "created_at": "..."}
            │
            ▼
8. FastAPI devuelve el JSON con status 201 Created
```

### La diferencia entre Model y Schema

```
Model (SQLAlchemy)              Schema (Pydantic)
──────────────────              ─────────────────
Habla con la DB                 Habla con el cliente
Define la tabla                 Define el JSON
Representa una fila             Representa un mensaje

User                            UserCreate
├── id (generado por DB)        ├── nombre
├── nombre                      └── email
├── email
└── created_at (generado)       UserResponse
                                ├── id
                                ├── nombre
                                ├── email
                                └── created_at
```

---

## 7. La aplicación Python — main.py

### Los decoradores `@app.post`, `@app.get`, etc.

FastAPI usa decoradores para registrar funciones como manejadores de requests. Cuando llega una petición, FastAPI busca qué función está registrada para esa URL y método, y la ejecuta automáticamente.

```python
@app.post("/users")       # método HTTP + URL
def create_user(...):     # función que se ejecuta cuando llega ese request
    ...
```

Los métodos HTTP indican la intención:

| Método | Intención | Ejemplo |
|---|---|---|
| GET | Leer datos | Ver lista de usuarios |
| POST | Crear un recurso | Registrar un usuario nuevo |
| PUT | Actualizar un recurso | Cambiar el email de un usuario |
| DELETE | Borrar un recurso | Eliminar un usuario |

### Los argumentos de los endpoints

FastAPI inyecta los argumentos automáticamente — nunca los pasás vos:

```python
def create_user(
    user: schemas.UserCreate,      # viene del JSON del request
    db: Session = Depends(get_db)  # viene de get_db() — la sesión de DB
):
```

### Los códigos HTTP de respuesta

| Código | Significado |
|---|---|
| 200 | OK — respuesta exitosa |
| 201 | Created — recurso creado |
| 400 | Bad Request — el cliente mandó algo incorrecto |
| 404 | Not Found — el recurso no existe |
| 422 | Unprocessable Entity — datos inválidos (Pydantic) |
| 500 | Internal Server Error — bug en el servidor |

---

## 8. Tests automáticos

Los tests usan una base de datos en memoria (`sqlite:///:memory:`) que se crea al empezar los tests y se destruye al terminar. Esto garantiza que los tests no tocan la base de datos real y son siempre reproducibles.

```python
# La DB de tests reemplaza a la DB real mediante override de dependencia
app.dependency_overrides[get_db] = override_get_db
```

Para correr los tests:
```bash
pytest test_main.py -v
```

---

## 9. Dependencias

```
fastapi          # El framework de la API
uvicorn          # El servidor que corre FastAPI
httpx            # Cliente HTTP para el TestClient
pytest           # Framework de tests
sqlalchemy       # ORM — traduce Python a SQL
python-multipart # Necesario para parsear formularios
```

---

## 10. Docker y el problema de persistencia

### `Dockerfile`

```dockerfile
FROM python:3.13-slim    # imagen base de Python
WORKDIR /app             # directorio de trabajo dentro del contenedor
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### El problema: los datos no persisten en el contenedor

SQLite guarda los datos en un archivo dentro del contenedor. Cuando el contenedor se destruye (por un redespliegue), el archivo desaparece.

**No es necesario dockerizar cada vez que se agrega un usuario.** El problema es más fundamental: aunque no redesplegaras nunca, si el contenedor se reinicia por cualquier razón (error, actualización de Render, etc.), los datos se pierden.

### La solución para producción: PostgreSQL externo

Cambiar la `DATABASE_URL` para apuntar a un servidor PostgreSQL que vive fuera del contenedor:

```python
# Desarrollo local (SQLite):
DATABASE_URL = "sqlite:///./database.db"

# Producción (PostgreSQL en Render):
DATABASE_URL = "postgresql://usuario:password@host/nombre_db"
```

El código de `models.py`, `schemas.py` y los endpoints no cambia — SQLAlchemy abstrae las diferencias entre motores de base de datos.

---

## 11. CI/CD con GitHub Actions

El pipeline tiene 4 jobs al hacer push a `main` o `develop`:

```
[test] → [docker] → [deploy-staging]    (solo en develop)
                  → [deploy-production]  (solo en main)
```

### Secrets requeridos en GitHub

| Secret | Descripción |
|---|---|
| `RENDER_API_KEY` | Token de Render para usar su API |
| `RENDER_STAGING_SERVICE_ID` | ID del servicio staging en Render |
| `RENDER_PRODUCTION_SERVICE_ID` | ID del servicio producción en Render |
| `GHCR_TOKEN` | Token de GitHub con permiso `read:packages` |

---

## 12. GHCR — Dónde se guardan las imágenes

Las imágenes Docker se publican en GitHub Container Registry:

```
ghcr.io/sebaheredia/fastapi2:main      ← producción
ghcr.io/sebaheredia/fastapi2:develop   ← staging
```

Ver imágenes publicadas:
```
https://github.com/sebaheredia/FastApi2/pkgs/container/fastapi2
```

---

## 13. Despliegue en Render

Render descarga la imagen ya construida de GHCR y la corre directamente — no vuelve a buildear Docker.

| Servicio | Rama | URL |
|---|---|---|
| `fastapi2-staging` | `develop` | https://fastapi2-staging.onrender.com |
| `fastapi2-production` | `main` | https://fastapi2-production.onrender.com |

Los servicios son **públicos** — accesibles desde cualquier máquina en el mundo.

El plan free de Render apaga el servicio tras 15 minutos de inactividad. El primer request puede tardar hasta 60 segundos.

---

## 14. Flujo completo de trabajo

```
Desarrollador hace cambios
        │
        ▼
git push origin develop
        │
        ▼
GitHub Actions:
[test] pytest → [docker] build + push :develop → [deploy-staging]
        │
        ▼
Render descarga imagen :develop de GHCR y la corre
        │
        ▼
Verificar en https://fastapi2-staging.onrender.com/docs
        │
        ▼
git merge develop → main && git push origin main
        │
        ▼
GitHub Actions:
[test] pytest → [docker] build + push :main → [deploy-production]
        │
        ▼
Render descarga imagen :main de GHCR y la corre
        │
        ▼
Verificar en https://fastapi2-production.onrender.com/docs
```

---

## 15. Cómo probar el servicio desplegado

### Desde el navegador

```
https://fastapi2-production.onrender.com/docs
```

### Desde la terminal

```bash
# Crear un usuario
curl -X POST "https://fastapi2-production.onrender.com/users" \
     -H "Content-Type: application/json" \
     -d '{"nombre": "Seba", "email": "seba@gmail.com"}'

# Listar todos los usuarios
curl https://fastapi2-production.onrender.com/users

# Obtener usuario con ID 1
curl https://fastapi2-production.onrender.com/users/1

# Borrar usuario con ID 1
curl -X DELETE https://fastapi2-production.onrender.com/users/1

# Endpoints originales
curl https://fastapi2-production.onrender.com/ping
curl https://fastapi2-production.onrender.com/hello/Seba
curl -X POST "https://fastapi2-production.onrender.com/sum?a=5&b=3"
```

---

## 16. Cómo correr el proyecto localmente

### Sin Docker (recomendado para desarrollo)

```bash
git clone https://github.com/sebaheredia/FastApi2.git
cd FastApi2
pip install -r requirements.txt
uvicorn main:app --reload
# http://localhost:8000/docs

pytest test_main.py -v
```

El archivo `database.db` se crea automáticamente en la carpeta del proyecto. Los datos persisten entre reinicios porque viven en tu disco, fuera de cualquier contenedor.

### Con Docker

```bash
docker build -t fastapi2 .
docker run -p 8000:8000 fastapi2
# http://localhost:8000/docs
```

Con Docker los datos se pierden al detener el contenedor porque `database.db` vive dentro del contenedor. Para desarrollo con Docker y datos persistentes se usaría un volumen:

```bash
docker run -p 8000:8000 -v $(pwd)/data:/app/data fastapi2
# monta la carpeta ./data de tu máquina en /app/data del contenedor
```

---

## Contacto

ADAIP (Área de Desarrollos Avanzados de Imágenes y Percepción)
