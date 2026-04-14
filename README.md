# FastApi2 — API REST con CI/CD, Docker y Base de Datos

Proyecto de ejemplo de una API REST construida con **FastAPI** (Python), con integración y despliegue continuo (CI/CD) usando **GitHub Actions**, **GHCR** y **Render**, con base de datos **PostgreSQL** persistente.

---

## Índice

- [FastApi2 — API REST con CI/CD, Docker y Base de Datos](#fastapi2--api-rest-con-cicd-docker-y-base-de-datos)
  - [Índice](#índice)
  - [1. ¿Qué es esta API?](#1-qué-es-esta-api)
  - [2. Qué es el backend y cómo se interactúa con él](#2-qué-es-el-backend-y-cómo-se-interactúa-con-él)
    - [FastAPI no tiene pantallas](#fastapi-no-tiene-pantallas)
    - [¿Qué es JSON?](#qué-es-json)
    - [Cómo interactuar sin un frontend](#cómo-interactuar-sin-un-frontend)
  - [3. Estructura del repositorio](#3-estructura-del-repositorio)
  - [4. Los archivos de la base de datos](#4-los-archivos-de-la-base-de-datos)
    - [`database.py` — La conexión](#databasepy--la-conexión)
    - [`models.py` — Las tablas](#modelspy--las-tablas)
    - [`schemas.py` — La validación](#schemaspy--la-validación)
  - [5. Cómo interactúan database, models y schemas](#5-cómo-interactúan-database-models-y-schemas)
    - [La diferencia entre Model y Schema](#la-diferencia-entre-model-y-schema)
  - [6. La aplicación — main.py](#6-la-aplicación--mainpy)
    - [Los decoradores `@app.post`, `@app.get`](#los-decoradores-apppost-appget)
    - [Los métodos HTTP](#los-métodos-http)
    - [Los códigos HTTP de respuesta](#los-códigos-http-de-respuesta)
  - [7. Tests automáticos](#7-tests-automáticos)
    - [`conftest.py` — Configuración de tests](#conftestpy--configuración-de-tests)
    - [`test_main.py` — Los tests](#test_mainpy--los-tests)
  - [8. Docker](#8-docker)
    - [`Dockerfile`](#dockerfile)
    - [Por qué psycopg2-binary es crítico](#por-qué-psycopg2-binary-es-crítico)
  - [9. CI/CD con GitHub Actions](#9-cicd-con-github-actions)
    - [Job 1 — test](#job-1--test)
    - [Job 2 — docker](#job-2--docker)
    - [Jobs 3 y 4 — deploy](#jobs-3-y-4--deploy)
    - [Secrets requeridos en GitHub](#secrets-requeridos-en-github)
  - [10. GHCR — Dónde se guardan las imágenes Docker](#10-ghcr--dónde-se-guardan-las-imágenes-docker)
  - [11. Despliegue en Render](#11-despliegue-en-render)
  - [12. Base de datos PostgreSQL](#12-base-de-datos-postgresql)
    - [¿Por qué no SQLite en producción?](#por-qué-no-sqlite-en-producción)
    - [El servicio PostgreSQL en Render](#el-servicio-postgresql-en-render)
    - [Dónde están físicamente los datos](#dónde-están-físicamente-los-datos)
  - [13. Cómo se conecta Docker con PostgreSQL](#13-cómo-se-conecta-docker-con-postgresql)
    - [URL interna vs externa](#url-interna-vs-externa)
  - [14. SQLite vs PostgreSQL](#14-sqlite-vs-postgresql)
  - [15. Flujo completo de trabajo](#15-flujo-completo-de-trabajo)
  - [16. Cómo probar el servicio desplegado](#16-cómo-probar-el-servicio-desplegado)
    - [Desde el navegador](#desde-el-navegador)
    - [Verificar qué DB está usando](#verificar-qué-db-está-usando)
    - [Desde la terminal](#desde-la-terminal)
    - [Ver los datos en PostgreSQL (desde psql)](#ver-los-datos-en-postgresql-desde-psql)
  - [17. Cómo correr el proyecto localmente](#17-cómo-correr-el-proyecto-localmente)
    - [Sin Docker](#sin-docker)
    - [Con Docker](#con-docker)
    - [Con Docker y PostgreSQL local](#con-docker-y-postgresql-local)
  - [Contacto](#contacto)

---

## 1. ¿Qué es esta API?

Hola. Una **API REST** es un servicio que responde a peticiones HTTP. No tiene pantallas ni formularios — es puro backend. Los clientes (navegadores, aplicaciones móviles, Postman, otros servicios) le mandan datos en formato JSON y reciben respuestas en JSON.

Esta API expone los siguientes endpoints:

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/ping` | Verificación de que el servidor está activo |
| GET | `/hello/{name}` | Saludo personalizado |
| POST | `/sum` | Suma dos números |
| GET | `/db-info` | Muestra a qué base de datos está conectada la app |
| POST | `/users` | Crear un usuario |
| GET | `/users` | Listar todos los usuarios |
| GET | `/users/{id}` | Obtener un usuario por ID |
| DELETE | `/users/{id}` | Borrar un usuario |

Los servicios desplegados son públicos — accesibles desde cualquier máquina en el mundo:

| Entorno | URL |
|---|---|
| **Staging** | https://fastapi2-staging-docker.onrender.com |
| **Producción** | https://fastapi2-production.onrender.com |

---

## 2. Qué es el backend y cómo se interactúa con él

### FastAPI no tiene pantallas

FastAPI es solo el backend — no muestra formularios ni le pregunta nada al usuario. El que muestra la pantalla y recoge los datos es **otro programa** (un frontend, una app móvil, Postman).

```
Lo que se imagina:              Lo que es realmente:
──────────────────              ────────────────────────────────────
[Pantalla de registro]          [Postman / curl / frontend / app]
  Nombre: ____                              │
  Email:  ____          ──JSON──►      [FastAPI]
  [Registrar]                               │
                                            ▼
                                       [PostgreSQL]
```

### ¿Qué es JSON?

JSON es el formato en que viajan los datos entre el cliente y la API:

```json
{
    "nombre": "Seba",
    "email": "seba@gmail.com"
}
```

### Cómo interactuar sin un frontend

FastAPI genera automáticamente una interfaz en `/docs` (Swagger UI):

```
https://fastapi2-staging-docker.onrender.com/docs
```

También desde la terminal con curl:

```bash
# Crear un usuario
curl -X POST "https://fastapi2-staging-docker.onrender.com/users" \
     -H "Content-Type: application/json" \
     -d '{"nombre": "Seba", "email": "seba@gmail.com"}'

# Listar usuarios
curl https://fastapi2-staging-docker.onrender.com/users
```

---

## 3. Estructura del repositorio

```
FastApi2/
├── main.py          # Endpoints de la API
├── database.py      # Conexión a la base de datos
├── models.py        # Definición de las tablas (SQLAlchemy)
├── schemas.py       # Validación de datos entrada/salida (Pydantic)
├── conftest.py      # Configuración de tests (pytest fixtures)
├── test_main.py     # Tests automáticos
├── requirements.txt # Dependencias Python
├── Dockerfile       # Instrucciones para construir la imagen Docker
└── .github/
    └── workflows/
        └── ci.yml   # Pipeline de CI/CD
```

---

## 4. Los archivos de la base de datos

### `database.py` — La conexión

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Lee la URL de conexión desde las variables de entorno
# Si no existe (desarrollo local) usa SQLite como fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# SQLite necesita check_same_thread=False
# PostgreSQL no necesita ningún argumento especial
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# El engine es el "motor" que traduce Python a SQL
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Fábrica de sesiones — cada request abre su propia sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase madre de todos los modelos
Base = declarative_base()

def get_db():
    """Abre una sesión por request y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `models.py` — Las tablas

Define la estructura de las tablas. Cada clase es una tabla, cada atributo Column es una columna:

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)  # autoincremental: 1, 2, 3...
    nombre = Column(String, nullable=False)  # texto, obligatorio
    email = Column(String, unique=True)      # texto, único por fila
    created_at = Column(DateTime, server_default=func.now())  # fecha automática
```

SQLAlchemy genera automáticamente este SQL:
```sql
CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    nombre     TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `schemas.py` — La validación

Define qué datos entran y salen de la API. Son clases de Pydantic — validan el JSON sin tocar la base de datos:

```python
class UserCreate(BaseModel):
    nombre: str   # obligatorio
    email: str    # obligatorio

class UserResponse(BaseModel):
    id: int
    nombre: str
    email: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # permite convertir objetos SQLAlchemy a JSON
```

---

## 5. Cómo interactúan database, models y schemas

El flujo completo de un `POST /users`:

```
1. Cliente manda JSON:
   {"nombre": "Seba", "email": "seba@gmail.com"}
            │
            ▼
2. Pydantic valida con UserCreate
   Si falta algo → 422 automáticamente
            │
            ▼
3. SQLAlchemy consulta si el email ya existe:
   SELECT * FROM users WHERE email = "seba@gmail.com"
   Si existe → 400 "El email ya está registrado"
            │
            ▼
4. SQLAlchemy inserta la fila nueva:
   INSERT INTO users (nombre, email) VALUES ("Seba", "seba@gmail.com")
            │
            ▼
5. db.refresh() lee el objeto completo con id y created_at
            │
            ▼
6. Pydantic convierte User → JSON usando UserResponse
   {"id": 1, "nombre": "Seba", "email": "seba@gmail.com", "created_at": "..."}
            │
            ▼
7. FastAPI devuelve el JSON con status 201 Created
```

### La diferencia entre Model y Schema

```
Model (SQLAlchemy)         Schema (Pydantic)
──────────────────         ─────────────────
Habla con la DB            Habla con el cliente
Define la tabla            Define el JSON
Representa una fila        Representa un mensaje
```

---

## 6. La aplicación — main.py

### Los decoradores `@app.post`, `@app.get`

FastAPI usa decoradores para registrar funciones como manejadores de requests. Cuando llega una petición, FastAPI busca qué función está registrada y la ejecuta automáticamente:

```python
@app.post("/users")    # método HTTP + URL
def create_user(...):  # FastAPI la llama automáticamente, vos nunca la llamás
    ...
```

### Los métodos HTTP

| Método | Intención |
|---|---|
| GET | Leer datos |
| POST | Crear un recurso |
| PUT | Actualizar un recurso |
| DELETE | Borrar un recurso |

### Los códigos HTTP de respuesta

| Código | Significado |
|---|---|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Datos inválidos (Pydantic) |
| 500 | Error interno del servidor |

---

## 7. Tests automáticos

Los tests usan dos archivos:

### `conftest.py` — Configuración de tests

Pytest lo detecta automáticamente antes de correr cualquier test. Crea una base de datos SQLite en un archivo temporal (`test_database.db`), configura el cliente de test y lo limpia al terminar:

```python
# Usa SQLite en archivo temporal (no en memoria) para compartir
# la misma DB entre todas las conexiones durante los tests
TEST_DATABASE_URL = "sqlite:///./test_database.db"

# Reemplaza get_db() con una versión que usa la DB de test
app.dependency_overrides[get_db] = override_get_db

# El fixture "client" es lo que reciben los tests como argumento
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
```

### `test_main.py` — Los tests

Cada función de test recibe `client` — pytest lo inyecta automáticamente desde `conftest.py`:

```bash
pytest test_main.py -v
```

---

## 8. Docker

### `Dockerfile`

```dockerfile
FROM python:3.13-slim      # imagen base liviana de Python
WORKDIR /app               # directorio de trabajo dentro del contenedor
COPY requirements.txt .    # copiar deps primero para aprovechar cache
RUN pip install --no-cache-dir -r requirements.txt  # instalar deps
COPY . .                   # copiar el código
EXPOSE 8000                # documentar el puerto (informativo)
CMD ["sh", "-c",
  # Crear tablas ANTES de arrancar el servidor
  "python -c 'from database import engine; import models; models.Base.metadata.create_all(bind=engine)'"
  # Solo si create_all tuvo éxito, arrancar uvicorn
  " && uvicorn main:app --host 0.0.0.0 --port $PORT"]
  # $PORT es inyectado por Render dinámicamente
```

### Por qué psycopg2-binary es crítico

`psycopg2-binary` es el driver que permite a SQLAlchemy hablar con PostgreSQL. Sin él, la app no puede conectarse aunque `DATABASE_URL` esté correctamente configurada:

```
requirements.txt sin psycopg2-binary:
GitHub Actions buildea imagen → psycopg2 NO está en la imagen
Render descarga imagen → app intenta conectarse a PostgreSQL
import psycopg2 → ModuleNotFoundError ❌
app cae al fallback → usa SQLite dentro del contenedor

requirements.txt con psycopg2-binary:
GitHub Actions buildea imagen → psycopg2 SÍ está en la imagen
Render descarga imagen → app se conecta a PostgreSQL ✅
datos persisten en PostgreSQL
```

---

## 9. CI/CD con GitHub Actions

El pipeline tiene 4 jobs al hacer push a `main` o `develop`:

```
[test] → [docker] → [deploy-staging]    (solo en develop)
                  → [deploy-production]  (solo en main)
```

### Job 1 — test
Instala Python, instala dependencias y corre los tests con pytest. Si alguno falla, el pipeline se detiene.

### Job 2 — docker
Construye la imagen Docker y la publica en GHCR:
- Login a GHCR con el token automático de GitHub Actions
- Configura `docker/setup-buildx-action` (necesario para cache)
- Genera el tag según la rama (`main` → `:main`, `develop` → `:develop`)
- Construye la imagen con todas las dependencias incluyendo `psycopg2-binary`
- La sube a `ghcr.io/sebaheredia/fastapi2:<rama>`

### Jobs 3 y 4 — deploy
Llama a la API de Render con dos pasos:
1. **PATCH /image** — le dice a Render qué imagen de GHCR usar
2. **POST /deploys** — le dice a Render que despliege ahora

### Secrets requeridos en GitHub

| Secret | Descripción |
|---|---|
| `RENDER_API_KEY` | Token de Render → Account Settings → API Keys |
| `RENDER_STAGING_SERVICE_ID` | ID del servicio staging → srv-xxx |
| `RENDER_PRODUCTION_SERVICE_ID` | ID del servicio producción → srv-xxx |
| `GHCR_TOKEN` | Token GitHub con permiso `read:packages` |

---

## 10. GHCR — Dónde se guardan las imágenes Docker

Las imágenes se publican en GitHub Container Registry:

```
ghcr.io/sebaheredia/fastapi2:main      ← producción
ghcr.io/sebaheredia/fastapi2:develop   ← staging
```

Cada imagen tiene todas las dependencias incluidas (`psycopg2-binary`, SQLAlchemy, FastAPI, etc). Render solo descarga y corre — no instala nada por su cuenta.

---

## 11. Despliegue en Render

Render descarga la imagen ya construida de GHCR y la corre directamente.

```
Enfoque tradicional (lo que NO hacemos):
Render clona repo → Render buildea Docker → corre
(trabajo duplicado, posibles diferencias con lo testeado)

Este proyecto:
GitHub Actions buildea → sube a GHCR → Render descarga → corre
(la imagen que corre es exactamente la que fue testeada)
```

| Servicio | Runtime | Rama | URL |
|---|---|---|---|
| `fastapi2-staging-docker` | Image (GHCR) | `develop` | https://fastapi2-staging-docker.onrender.com |
| `fastapi2-production` | Image (GHCR) | `main` | https://fastapi2-production.onrender.com |

---

## 12. Base de datos PostgreSQL

### ¿Por qué no SQLite en producción?

SQLite guarda los datos en un archivo dentro del contenedor Docker. Cuando Render redesplega (destruye el contenedor viejo y crea uno nuevo), ese archivo desaparece — todos los datos se pierden.

```
SQLite en Docker:
Deploy nuevo → contenedor viejo destruido → database.db desaparece → datos perdidos ❌

PostgreSQL externo:
Deploy nuevo → contenedor viejo destruido → PostgreSQL intacto → datos persisten ✅
```

### El servicio PostgreSQL en Render

| Campo | Valor |
|---|---|
| **Nombre** | `fastapi2-db` |
| **Plan** | Free |
| **Región** | Oregon (US West) — misma que los servicios web |

### Dónde están físicamente los datos

```
Contenedor Docker (app)          Servidor PostgreSQL (Render)
───────────────────────          ────────────────────────────
main.py                          tabla users:
database.py   ────────►          id | nombre | email | created_at
models.py                         1 | Seba   | s@g.c | 2026-04-07
schemas.py                        2 | Isa    | i@g.c | 2026-04-07

Redespliegue:
Contenedor nuevo ────────►       mismos datos ✅
```

---

## 13. Cómo se conecta Docker con PostgreSQL

La conexión se hace a través de la variable de entorno `DATABASE_URL`. Render la inyecta automáticamente dentro del contenedor al arrancarlo:

```
Render UI: DATABASE_URL = postgresql://usuario:pass@host/db
        │
        ▼
Render arranca el contenedor y hace internamente:
export DATABASE_URL="postgresql://..."
        │
        ▼
Python lee: os.getenv("DATABASE_URL")
        │
        ▼
SQLAlchemy crea el engine con esa URL
        │
        ▼
psycopg2 (driver) establece la conexión TCP a PostgreSQL
        │
        ▼
Los endpoints pueden hacer queries: INSERT, SELECT, DELETE
```

No hay código especial entre Docker y PostgreSQL — es simplemente una variable de entorno con la URL de conexión. `os.getenv()` es todo lo que se necesita en el código.

### URL interna vs externa

| Tipo | Formato | Cuándo usar |
|---|---|---|
| **Internal** | `postgresql://user:pass@dpg-xxx-a/db` | Desde servicios dentro de Render |
| **External** | `postgresql://user:pass@dpg-xxx-a.oregon-postgres.render.com/db` | Desde fuera de Render (psql local, DBeaver) |

En `DATABASE_URL` del servicio web se usa la **Internal** porque la app corre dentro de Render.

---

## 14. SQLite vs PostgreSQL

| | SQLite | PostgreSQL |
|---|---|---|
| **Dónde vive** | Archivo en disco | Servidor separado |
| **En Docker** | Se pierde al reiniciar | Nunca se pierde |
| **Conexiones** | Una a la vez | Muchas simultáneas |
| **Driver Python** | Incluido en Python | Requiere `psycopg2-binary` |
| **Para qué** | Desarrollo local y tests | Producción |

---

## 15. Flujo completo de trabajo

```
Desarrollador hace cambios
        │
        ▼
git push origin develop
        │
        ▼
GitHub Actions:
[test] pytest → [docker] build imagen con psycopg2 → push :develop a GHCR
        │
        ▼
Render API: actualizar imagen → triggerear deploy
        │
        ▼
Render descarga imagen :develop de GHCR
Render arranca contenedor inyectando DATABASE_URL
CMD crea tablas en PostgreSQL → uvicorn arranca
        │
        ▼
Verificar en https://fastapi2-staging-docker.onrender.com/docs
        │
        ▼
git merge develop → main && git push origin main
        │
        ▼
Mismo proceso → imagen :main → deploy producción
```

---

## 16. Cómo probar el servicio desplegado

### Desde el navegador

```
https://fastapi2-staging-docker.onrender.com/docs
```

### Verificar qué DB está usando

```bash
curl https://fastapi2-staging-docker.onrender.com/db-info
# Debe devolver la URL de PostgreSQL, no sqlite
```

### Desde la terminal

```bash
# Crear usuario
curl -X POST "https://fastapi2-staging-docker.onrender.com/users" \
     -H "Content-Type: application/json" \
     -d '{"nombre": "Seba", "email": "seba@gmail.com"}'

# Listar usuarios
curl https://fastapi2-staging-docker.onrender.com/users

# Obtener usuario
curl https://fastapi2-staging-docker.onrender.com/users/1

# Borrar usuario
curl -X DELETE https://fastapi2-staging-docker.onrender.com/users/1
```

### Ver los datos en PostgreSQL (desde psql)

```bash
psql "postgresql://fastapi2_db_user:PASSWORD@dpg-xxx.oregon-postgres.render.com/fastapi2_db"

# Dentro de psql:
\dt                  # listar tablas
SELECT * FROM users; # ver todos los usuarios
```

---

## 17. Cómo correr el proyecto localmente

### Sin Docker

```bash
git clone https://github.com/sebaheredia/FastApi2.git
cd FastApi2
pip install -r requirements.txt
uvicorn main:app --reload
# http://localhost:8000/docs
# Usa SQLite automáticamente (database.db se crea solo)

pytest test_main.py -v
```

### Con Docker

```bash
docker build -t fastapi2 .
docker run -p 8000:8000 fastapi2
# http://localhost:8000/docs
# Datos se pierden al detener el contenedor (SQLite dentro del Docker)
```

### Con Docker y PostgreSQL local

```bash
# Crear un archivo .env (no subir a GitHub)
echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi2" > .env

docker run -p 8000:8000 --env-file .env fastapi2
```

---

## Contacto

ADAIP (Área de Desarrollos Avanzados de Imágenes y Percepción)
