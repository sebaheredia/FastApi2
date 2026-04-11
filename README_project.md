# FastApi2 — Sistema completo de CI/CD

Proyecto de ejemplo de un sistema web completo con **integración y despliegue continuo (CI/CD)**, compuesto por un backend en **FastAPI**, un frontend en **React**, una base de datos **PostgreSQL**, todo dockerizado y desplegado automáticamente en **Render** via **GitHub Actions**.

---

## Índice

1. [Arquitectura general](#1-arquitectura-general)
2. [Repositorios](#2-repositorios)
3. [Backend — FastAPI](#3-backend--fastapi)
4. [Frontend — React](#4-frontend--react)
5. [Base de datos — PostgreSQL](#5-base-de-datos--postgresql)
6. [Docker](#6-docker)
7. [CI/CD con GitHub Actions](#7-cicd-con-github-actions)
8. [GHCR — Registro de imágenes Docker](#8-ghcr--registro-de-imágenes-docker)
9. [Despliegue en Render](#9-despliegue-en-render)
10. [Cómo se conectan las partes](#10-cómo-se-conectan-las-partes)
11. [Secrets de GitHub](#11-secrets-de-github)
12. [Servicios en Render](#12-servicios-en-render)
13. [URLs públicas](#13-urls-públicas)
14. [Flujo completo de trabajo](#14-flujo-completo-de-trabajo)
15. [Cómo correr el proyecto localmente](#15-cómo-correr-el-proyecto-localmente)

---

## 1. Arquitectura general

```
[Usuario]
    │
    ▼
[React — Frontend]          https://fastapi2-frontend-main.onrender.com
    │  hace requests HTTP/JSON
    ▼
[FastAPI — Backend]          https://fastapi2-production-docker.onrender.com
    │  consulta y guarda datos
    ▼
[PostgreSQL — Base de datos] fastapi2-db en Render
```

El frontend NO se conecta directamente a la base de datos. Solo habla con el backend via HTTP. El backend es el único que accede a PostgreSQL.

---

## 2. Repositorios

El proyecto está dividido en dos repositorios independientes, cada uno con su propio pipeline de CI/CD:

| Repo | Tecnología | URL |
|---|---|---|
| `sebaheredia/FastApi2` | FastAPI (Python) | https://github.com/sebaheredia/FastApi2 |
| `sebaheredia/fastapi2-frontend` | React (JavaScript) | https://github.com/sebaheredia/fastapi2-frontend |

---

## 3. Backend — FastAPI

### ¿Qué hace?

Es una API REST que expone endpoints HTTP. No tiene pantallas — devuelve datos en formato JSON. El frontend consume esos endpoints.

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/ping` | Health check |
| GET | `/hello/{name}` | Saludo personalizado |
| POST | `/sum` | Suma dos números |
| GET | `/db-info` | Muestra la DB conectada |
| POST | `/users` | Crear un usuario |
| GET | `/users` | Listar todos los usuarios |
| GET | `/users/{id}` | Obtener usuario por ID |
| DELETE | `/users/{id}` | Borrar un usuario |

### Estructura del repo backend

```
FastApi2/
├── main.py          # Endpoints + configuración CORS
├── database.py      # Conexión a PostgreSQL via DATABASE_URL
├── models.py        # Tabla users (SQLAlchemy)
├── schemas.py       # Validación JSON entrada/salida (Pydantic)
├── conftest.py      # Setup de tests con DB en archivo temporal
├── test_main.py     # Tests automáticos con pytest
├── requirements.txt # Dependencias incluyendo psycopg2-binary
├── Dockerfile       # Multi-stage: crea tablas + arranca uvicorn
└── .github/
    └── workflows/
        └── ci.yml   # Pipeline: test → docker → deploy
```

### CORS

El backend tiene configurado CORS para permitir requests desde el frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Sin CORS el navegador bloquea los requests del frontend al backend porque están en dominios diferentes.

### Conexión a la base de datos

`database.py` lee `DATABASE_URL` del entorno. En Render esa variable se configura apuntando a PostgreSQL. En local usa SQLite como fallback:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")
```

### Por qué psycopg2-binary es crítico

Es el driver que permite a SQLAlchemy conectarse a PostgreSQL. Sin él en `requirements.txt`, la imagen Docker se buildea sin el driver y la app cae silenciosamente a SQLite aunque `DATABASE_URL` esté configurado.

---

## 4. Frontend — React

### ¿Qué hace?

Es la interfaz visual que el usuario ve en el navegador. Muestra la lista de usuarios, permite crear nuevos y borrarlos. Se comunica con el backend via fetch/HTTP.

### Estructura del repo frontend

```
fastapi2-frontend/
├── public/
│   └── index.html          # HTML base
├── src/
│   ├── index.js            # Punto de entrada React
│   ├── App.js              # Componente principal con toda la UI
│   ├── App.css             # Estilos (tema oscuro con tipografía Syne)
│   └── api.js              # Funciones que llaman al backend
├── nginx.conf              # Configuración del servidor web
├── Dockerfile              # Build multi-stage: Node → nginx
└── .github/
    └── workflows/
        └── ci.yml          # Pipeline: docker → deploy
```

### `api.js` — La capa de comunicación

Contiene una función por cada endpoint del backend:

```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export async function getUsers() { ... }       // GET /users
export async function createUser(...) { ... }  // POST /users
export async function deleteUser(id) { ... }   // DELETE /users/{id}
```

`REACT_APP_API_URL` se embebe en el bundle durante el build — no se puede cambiar en runtime. Por eso tiene que estar disponible como variable en tiempo de compilación.

### REACT_APP_API_URL — cómo llega al bundle

```
Secret BACKEND_PRODUCTION_URL en GitHub
        │
        ▼
GitHub Actions lee el secret y lo pasa como build-arg a Docker
        │
        ▼
Dockerfile lo recibe como ARG y lo pasa a npm run build
        │
        ▼
React compila el código con la URL hardcodeada en el JavaScript
        │
        ▼
nginx sirve esos archivos — la URL ya está fija adentro
```

---

## 5. Base de datos — PostgreSQL

### ¿Dónde vive?

En un servidor PostgreSQL en Render, completamente separado de los contenedores Docker. Así los datos persisten aunque el contenedor se destruya y se cree uno nuevo en cada redespliegue.

```
Contenedor Docker (app)          Servidor PostgreSQL (Render)
───────────────────────          ────────────────────────────
se destruye en cada deploy  ←→   nunca se toca en los deploys
```

### La tabla users

SQLAlchemy la crea automáticamente al arrancar el backend (via `create_all` en el Dockerfile):

```sql
CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    nombre     TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### URL interna vs externa

| Tipo | Formato | Cuándo usar |
|---|---|---|
| **Internal** | `postgresql://user:pass@dpg-xxx-a/db` | Desde servicios dentro de Render |
| **External** | `postgresql://user:pass@dpg-xxx.oregon-postgres.render.com/db` | Desde fuera de Render (psql local, DBeaver) |

En `DATABASE_URL` del servicio web se usa la **Internal** porque el backend corre dentro de la red de Render.

### Ver los datos directamente

```bash
psql "postgresql://fastapi2_db_user:PASSWORD@dpg-xxx.oregon-postgres.render.com/fastapi2_db"

\dt                  # listar tablas
SELECT * FROM users; # ver todos los usuarios
```

---

## 6. Docker

### Dockerfile del backend

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["sh", "-c",
  # Crea las tablas en PostgreSQL antes de arrancar
  "python -c 'from database import engine; import models; models.Base.metadata.create_all(bind=engine)'"
  # Solo si create_all tuvo éxito, arranca uvicorn
  " && uvicorn main:app --host 0.0.0.0 --port $PORT"]
```

### Dockerfile del frontend — Multi-stage build

```
Etapa 1 (builder): Node.js
  → instala dependencias (npm install)
  → recibe REACT_APP_API_URL como ARG
  → compila React (npm run build) → archivos estáticos en /build

Etapa 2 (server): nginx
  → copia los archivos de /build
  → los sirve en el puerto 80
```

nginx es mucho más liviano que Node para servir archivos estáticos — la imagen final pesa ~25MB en lugar de ~300MB.

---

## 7. CI/CD con GitHub Actions

### Pipeline del backend

```
push a main o develop
        │
        ▼
[Job 1: test]
pytest corre los tests con SQLite en archivo temporal
Si alguno falla → pipeline se detiene
        │
        ▼
[Job 2: docker]
Login a GHCR → build imagen → push a ghcr.io/sebaheredia/fastapi2:<rama>
        │
        ▼
[Job 3: deploy-staging]    (solo en develop)
PATCH imagen en Render → POST deploy → Render descarga :develop y corre

[Job 3: deploy-production] (solo en main)
PATCH imagen en Render → POST deploy → Render descarga :main y corre
```

### Pipeline del frontend

```
push a main o develop
        │
        ▼
[Job 1: docker]
Determina URL del backend según la rama (main → prod, develop → staging)
Login a GHCR → build imagen con REACT_APP_API_URL embebida
Push a ghcr.io/sebaheredia/fastapi2-frontend:<rama>
        │
        ▼
[Job 2: deploy-staging]    (solo en develop)
[Job 2: deploy-production] (solo en main)
PATCH imagen en Render → POST deploy → Render descarga y corre
```

### ¿Por qué el frontend no tiene job de tests?

React valida el código en el build. Si hay errores de sintaxis o imports rotos, `npm run build` falla y el pipeline se detiene. No se necesita un job de tests separado para este nivel de ejemplo.

---

## 8. GHCR — Registro de imágenes Docker

GitHub Container Registry guarda las imágenes Docker construidas por GitHub Actions:

```
Backend:
ghcr.io/sebaheredia/fastapi2:main      ← producción
ghcr.io/sebaheredia/fastapi2:develop   ← staging

Frontend:
ghcr.io/sebaheredia/fastapi2-frontend:main     ← producción
ghcr.io/sebaheredia/fastapi2-frontend:develop  ← staging
```

Render descarga estas imágenes directamente — no vuelve a buildear nada. La imagen que corre en producción es exactamente la misma que fue testeada en CI.

---

## 9. Despliegue en Render

Render tiene configurados 4 servicios web del tipo **Image** (descarga de GHCR) más 1 base de datos:

| Servicio | Tipo | Imagen | URL |
|---|---|---|---|
| `fastapi2-staging-docker` | Image | `:develop` | https://fastapi2-staging-docker.onrender.com |
| `fastapi2-production-docker` | Image | `:main` | https://fastapi2-production-docker.onrender.com |
| `fastapi2-frontend-staging` | Image | `frontend:develop` | https://fastapi2-frontend-staging.onrender.com |
| `fastapi2-frontend-main` | Image | `frontend:main` | https://fastapi2-frontend-main.onrender.com |
| `fastapi2-db` | PostgreSQL | — | internal |

### Cómo Render redesplega

El workflow de GitHub Actions llama a la API de Render con dos pasos:

```bash
# 1. Le dice a Render qué imagen usar
PATCH /v1/services/{service_id}/image
  body: { image: { url: "ghcr.io/...", credentials: {...} } }

# 2. Le dice a Render que despliege ahora
POST /v1/services/{service_id}/deploys
```

Render descarga la imagen de GHCR y reemplaza el contenedor en ejecución.

### Plan gratuito

El free tier de Render apaga los servicios tras 15 minutos de inactividad. El primer request puede tardar hasta 60 segundos mientras despierta. La base de datos gratuita expira a los 90 días.

---

## 10. Cómo se conectan las partes

```
Usuario abre el navegador
        │
        ▼
https://fastapi2-frontend-main.onrender.com
Render sirve la imagen Docker del frontend
nginx entrega los archivos React al navegador
        │
        ▼
React carga en el navegador del usuario
Hace GET a https://fastapi2-production-docker.onrender.com/users
        │  ← REACT_APP_API_URL embebida en el bundle
        ▼
FastAPI recibe el request
Lee DATABASE_URL del entorno → se conecta a PostgreSQL
Ejecuta SELECT * FROM users
Devuelve JSON al frontend
        │
        ▼
React muestra la lista de usuarios en pantalla
```

---

## 11. Secrets de GitHub

### Repo backend (FastApi2)

| Secret | Descripción |
|---|---|
| `RENDER_API_KEY` | Token de Render → Account Settings → API Keys |
| `RENDER_STAGING_SERVICE_ID` | ID del servicio backend staging |
| `RENDER_PRODUCTION_SERVICE_ID` | ID del servicio backend producción |
| `GHCR_TOKEN` | Token GitHub con permiso `read:packages` |

### Repo frontend (fastapi2-frontend)

| Secret | Descripción |
|---|---|
| `RENDER_API_KEY` | El mismo token de Render |
| `RENDER_FRONTEND_STAGING_SERVICE_ID` | ID del servicio frontend staging |
| `RENDER_FRONTEND_PRODUCTION_SERVICE_ID` | ID del servicio frontend producción |
| `GHCR_TOKEN` | El mismo token GitHub |
| `BACKEND_STAGING_URL` | URL pública del backend staging |
| `BACKEND_PRODUCTION_URL` | URL pública del backend producción |

---

## 12. Servicios en Render

Para crear un servicio que use una imagen de GHCR:

1. Render → **New Web Service → Existing image from a registry**
2. **Image URL**: `ghcr.io/sebaheredia/fastapi2:<rama>`
3. **Credentials**: username `sebaheredia`, password = `GHCR_TOKEN`
4. **Plan**: Free
5. **Region**: Oregon (US West) — misma región que la DB para usar Internal URL

Para el backend agregar variable de entorno:

| Key | Value |
|---|---|
| `DATABASE_URL` | Internal Database URL de `fastapi2-db` |

El frontend no necesita variables de entorno en Render.

---

## 13. URLs públicas

| Servicio | URL |
|---|---|
| **Frontend producción** | https://fastapi2-frontend-main.onrender.com |
| **Backend producción** | https://fastapi2-production-docker.onrender.com |
| **Docs API producción** | https://fastapi2-production-docker.onrender.com/docs |
| **Frontend staging** | https://fastapi2-frontend-staging.onrender.com |
| **Backend staging** | https://fastapi2-staging-docker.onrender.com |

Todos los servicios son públicos — accesibles desde cualquier máquina en el mundo.

---

## 14. Flujo completo de trabajo

```
1. Desarrollar en rama feature
   git checkout -b feature/nueva-funcionalidad

2. Push a develop
   git push origin develop
         │
         ├─► Backend CI: tests → docker :develop → deploy staging backend
         └─► Frontend CI: docker :develop → deploy staging frontend
         │
         ▼
   Verificar en:
   https://fastapi2-frontend-staging.onrender.com

3. Merge develop → main
   git checkout main && git merge develop
   git push origin main
         │
         ├─► Backend CI: tests → docker :main → deploy producción backend
         └─► Frontend CI: docker :main → deploy producción frontend
         │
         ▼
   Verificar en:
   https://fastapi2-frontend-main.onrender.com
```

---

## 15. Cómo correr el proyecto localmente

### Backend

```bash
git clone https://github.com/sebaheredia/FastApi2.git
cd FastApi2
pip install -r requirements.txt
uvicorn main:app --reload
# http://localhost:8000/docs
# Usa SQLite automáticamente (database.db se crea solo)

pytest test_main.py -v
```

### Frontend

```bash
git clone https://github.com/sebaheredia/fastapi2-frontend.git
cd fastapi2-frontend
npm install
npm start
# http://localhost:3000
# El backend debe estar corriendo en localhost:8000
```

### Con Docker (backend)

```bash
docker build -t fastapi2-backend .
docker run -p 8000:8000 fastapi2-backend
```

### Con Docker (frontend)

```bash
docker build \
  --build-arg REACT_APP_API_URL=http://localhost:8000 \
  -t fastapi2-frontend .
docker run -p 3000:80 fastapi2-frontend
# http://localhost:3000
```

---

## Contacto

ADAIP (Área de Desarrollos Avanzados de Imágenes y Percepción)