# FastApi2 — API REST con CI/CD

Proyecto de ejemplo de una API REST construida con **FastAPI** (Python), con integración y despliegue continuo (CI/CD) usando **GitHub Actions** y **Render**.

---

## Índice

1. [¿Qué es esta API?](#1-qué-es-esta-api)
2. [Estructura del repositorio](#2-estructura-del-repositorio)
3. [La aplicación Python](#3-la-aplicación-python)
4. [Tests automáticos](#4-tests-automáticos)
5. [Dependencias](#5-dependencias)
6. [Docker](#6-docker)
7. [CI/CD con GitHub Actions](#7-cicd-con-github-actions)
8. [Despliegue en Render](#8-despliegue-en-render)
9. [Flujo completo de trabajo](#9-flujo-completo-de-trabajo)
10. [Cómo correr el proyecto localmente](#10-cómo-correr-el-proyecto-localmente)

---

## 1. ¿Qué es esta API?

Una **API REST** es un servicio que responde a peticiones HTTP. Los clientes (navegadores, aplicaciones móviles, otros servicios) hacen peticiones a una URL y la API devuelve datos, generalmente en formato JSON.

Esta API expone tres endpoints de ejemplo:

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Mensaje de bienvenida |
| GET | `/ping` | Verificación de que el servidor está activo |
| GET | `/hello/{name}` | Saludo personalizado |
| POST | `/sum` | Suma dos números |

**GET** se usa para leer o consultar datos. **POST** se usa para enviar datos al servidor para que los procese.

La documentación interactiva de la API está disponible automáticamente en `/docs`.

---

## 2. Estructura del repositorio

```
FastApi2/
├── main.py                          # Código principal de la API
├── test_main.py                     # Tests automáticos
├── requirements.txt                 # Dependencias Python
├── runtime.txt                      # Versión de Python para Render
├── Dockerfile                       # Instrucciones para construir la imagen Docker
└── .github/
    └── workflows/
        └── ci.yml                   # Pipeline de CI/CD (GitHub Actions)
```

---

## 3. La aplicación Python

### `main.py`

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Bienvenido a FastAPI"}

@app.get("/ping")
def ping():
    return {"ping": "pong"}

@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Hola, {name}!"}

@app.post("/sum")
def sum_numbers(a: float, b: float):
    return {"result": a + b}
```

**FastAPI** es un framework de Python para construir APIs de forma rápida y con validación automática de datos. Cada función decorada con `@app.get(...)` o `@app.post(...)` define un **endpoint** — una ruta de la API que responde a un tipo de petición HTTP.

- `@app.get("/ping")` — cuando alguien hace GET a `/ping`, se ejecuta la función `ping()` y devuelve `{"ping": "pong"}`.
- `@app.get("/hello/{name}")` — `{name}` es un **parámetro de ruta**: si alguien pide `/hello/Seba`, la función recibe `name="Seba"` y devuelve `{"message": "Hola, Seba!"}`.
- `@app.post("/sum")` — recibe dos parámetros `a` y `b` como query params (`/sum?a=5&b=3`) y devuelve la suma.

FastAPI genera automáticamente una interfaz web de documentación interactiva en `/docs` (Swagger UI) donde se puede probar cada endpoint desde el navegador.

---

## 4. Tests automáticos

### `test_main.py`

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

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
```

Los tests usan **pytest** junto con el `TestClient` de FastAPI, que simula peticiones HTTP reales sin necesitar un servidor corriendo.

Cada función `test_*` es un test independiente:
- Hace una petición a la API (GET o POST).
- Verifica con `assert` que la respuesta es la esperada: código HTTP correcto y datos correctos.

Si algún `assert` falla, pytest reporta el test como fallido y el pipeline de CI/CD se detiene — el código no se deploya.

Para correr los tests manualmente:
```bash
pytest test_main.py -v
```

---

## 5. Dependencias

### `requirements.txt`

```
fastapi
uvicorn
httpx
pytest
```

| Paquete | Para qué sirve |
|---|---|
| `fastapi` | El framework de la API |
| `uvicorn` | El servidor ASGI que corre la aplicación FastAPI |
| `httpx` | Cliente HTTP que usa el TestClient internamente |
| `pytest` | Framework para correr los tests |

### `runtime.txt`

```
python-3.13.0
```

Le indica a Render qué versión de Python usar al crear el entorno del servidor.

---

## 6. Docker

### ¿Qué es Docker?

**Docker** es una herramienta que empaqueta una aplicación junto con todo lo que necesita para funcionar (Python, dependencias, código) dentro de un **contenedor**. Un contenedor es un entorno aislado y reproducible: corre exactamente igual en tu máquina, en el servidor de CI y en producción, sin importar el sistema operativo del host.

### `Dockerfile`

```dockerfile
# Imagen base oficial de Python liviana
FROM python:3.13-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar e instalar dependencias primero (aprovecha cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Puerto que expone el contenedor
EXPOSE 8000

# Comando para levantar la API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

El `Dockerfile` es una receta con instrucciones paso a paso para construir la imagen:

1. **`FROM python:3.13-slim`** — parte de una imagen oficial de Python liviana (sin herramientas innecesarias).
2. **`WORKDIR /app`** — define `/app` como el directorio de trabajo dentro del contenedor, todos los comandos siguientes se ejecutan ahí.
3. **`COPY requirements.txt .`** y **`RUN pip install`** — copia e instala las dependencias. Se hace antes de copiar el código para aprovechar el **cache de capas de Docker**: si el código cambia pero `requirements.txt` no, Docker reutiliza esta capa y no reinstala todo desde cero.
4. **`COPY . .`** — copia todo el código del proyecto al contenedor.
5. **`EXPOSE 8000`** — documenta que el contenedor escucha en el puerto 8000.
6. **`CMD`** — el comando que se ejecuta cuando el contenedor arranca: levanta uvicorn con la app FastAPI.

### ¿Dónde se guarda la imagen Docker?

La imagen construida se publica en **GHCR (GitHub Container Registry)** — el registro de imágenes Docker de GitHub. Es gratuito para repositorios públicos y está integrado con GitHub Actions.

La URL de la imagen sigue este formato:
```
ghcr.io/<usuario>/<repositorio>:<tag>
```

Por ejemplo:
```
ghcr.io/sebaheredia/fastapi2:main      ← imagen de producción
ghcr.io/sebaheredia/fastapi2:develop   ← imagen de staging
```

El tag corresponde al nombre de la rama desde la que se construyó. Esto permite tener versiones separadas de la imagen para cada entorno.

### ¿Por qué publicar la imagen en GHCR?

Publicar la imagen tiene varias ventajas:

- **Trazabilidad**: cada imagen está asociada a un commit específico, podés saber exactamente qué código está corriendo en cada entorno.
- **Rollback**: si algo falla en producción, podés volver a la imagen anterior en segundos.
- **Consistencia**: Render descarga y corre exactamente la misma imagen que fue testeada en CI.
- **Cache**: los builds siguientes son más rápidos porque Docker reutiliza las capas que no cambiaron.

### Correr con Docker localmente

```bash
# Construir la imagen
docker build -t fastapi2 .

# Correr el contenedor
docker run -p 8000:8000 fastapi2

# La API queda disponible en http://localhost:8000
```

---

## 7. CI/CD con GitHub Actions

### ¿Qué es CI/CD?

- **CI (Integración Continua)**: cada vez que se sube código, se corre una batería de tests automáticamente para verificar que nada está roto.
- **CD (Despliegue Continuo)**: si los tests pasan, el código se deploya automáticamente al servidor correspondiente.

El objetivo es detectar errores rápido y garantizar que lo que llega a producción siempre funciona.

### `ci.yml`

El pipeline se activa en cada `git push` a las ramas `main` o `develop` y tiene 4 jobs que se ejecutan en secuencia:

```
[Job 1] test ──► [Job 2] docker ──► [Job 3] deploy-staging  (solo en develop)
                                ──► [Job 4] deploy-production (solo en main)
```

---

### Job 1: Correr tests

```yaml
test:
  name: Correr tests
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.13"
    - run: pip install -r requirements.txt
    - run: pytest test_main.py -v
```

Este job corre en una VM Ubuntu limpia y ejecuta los 4 tests de pytest. Si alguno falla, los jobs siguientes no se ejecutan y el pipeline se detiene.

---

### Job 2: Build y push de la imagen Docker

```yaml
docker:
  name: Build y push Docker
  runs-on: ubuntu-latest
  needs: test
  permissions:
    contents: read
    packages: write
```

Solo corre si el Job 1 (tests) fue exitoso. Realiza tres pasos:

**Login a GHCR**: se autentica en GitHub Container Registry usando el token automático de GitHub Actions.
```yaml
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

**Extraer metadata**: genera automáticamente el tag de la imagen basándose en el nombre de la rama (`main` o `develop`).
```yaml
- uses: docker/metadata-action@v5
  with:
    images: ghcr.io/${{ github.repository }}
    tags: |
      type=ref,event=branch
```

**Build y push**: construye la imagen Docker usando el `Dockerfile` del repo y la publica en GHCR con el tag generado.
```yaml
- uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ steps.meta.outputs.tags }}
```

El permiso `packages: write` es necesario para que el token de GitHub Actions pueda escribir en GHCR.

---

### Job 3: Deploy a Staging

```yaml
deploy-staging:
  needs: docker
  if: github.ref == 'refs/heads/develop'
```

- Solo corre si el push fue a la rama **`develop`**.
- `needs: docker` garantiza que la imagen fue construida y publicada antes de deployar.
- Hace un POST al deploy hook de Render (staging) para triggerear el redespliegue.

---

### Job 4: Deploy a Producción

```yaml
deploy-production:
  needs: docker
  if: github.ref == 'refs/heads/main'
```

- Solo corre si el push fue a la rama **`main`**.
- Idéntico al de staging pero apunta al servicio de producción.

---

### Secrets de GitHub

Los deploy hooks son URLs sensibles. Por eso se guardan como **secrets** en GitHub (Settings → Secrets and variables → Actions) y se referencian en el YAML como `${{ secrets.NOMBRE }}`. GitHub los inyecta en tiempo de ejecución sin exponerlos en los logs.

| Secret | Usado por |
|---|---|
| `RENDER_STAGING_DEPLOY_HOOK` | Deploy a Staging (rama `develop`) |
| `RENDER_PRODUCTION_DEPLOY_HOOK` | Deploy a Producción (rama `main`) |

---

### Resumen del flujo de ramas

| Push a | Tests | Build Docker | Staging | Producción |
|---|---|---|---|---|
| `develop` | ✅ Corre | ✅ Tag `develop` en GHCR | ✅ Se deploya | ⊘ Se saltea |
| `main` | ✅ Corre | ✅ Tag `main` en GHCR | ⊘ Se saltea | ✅ Se deploya |

---

## 8. Despliegue en Render

**Render** es una plataforma de hosting en la nube (PaaS — Platform as a Service). Se encarga de toda la infraestructura: servidores, redes, SSL, escalado.

### ¿Qué hace Render cuando recibe el deploy hook?

1. Recibe el POST del deploy hook y responde `202 Accepted`.
2. Clona el repositorio desde GitHub (la rama configurada).
3. Construye la imagen Docker usando el `Dockerfile` del repo.
4. Reemplaza el contenedor en ejecución por el nuevo.
5. Expone el servicio en una URL pública con HTTPS automático.

### Los dos servicios

| Servicio | Rama | URL |
|---|---|---|
| `fastapi2-staging` | `develop` | `https://fastapi2-staging.onrender.com` |
| `fastapi2-production` | `main` | `https://fastapi2-production.onrender.com` |

### Configuración del servicio en Render

Al crear cada Web Service en Render se configura:

| Campo | Valor |
|---|---|
| **Runtime** | Docker |
| **Branch** | `main` o `develop` según el entorno |
| **Region** | Oregon (US West) |
| **Instance Type** | Free |

### Deploy Hook

Es una URL única por servicio que al recibir un POST triggearea un nuevo deploy. Se obtiene en Render → tu servicio → Settings → Deploy Hook.

### Plan gratuito

El plan free de Render tiene una limitación: el servicio se **apaga automáticamente** después de 15 minutos de inactividad. La primera petición después de ese período puede demorar 50 segundos o más mientras el servidor vuelve a levantarse. Esto es normal en el plan gratuito y no afecta el funcionamiento.

---

## 9. Flujo completo de trabajo

```
Desarrollador hace cambios en el código
          │
          ▼
    git push origin develop
          │
          ▼
  GitHub Actions se activa
          │
          ▼
  [Job 1] Corre los 4 tests con pytest
          │
     ¿Tests OK?
    /           \
  NO             SÍ
  │               │
  ▼               ▼
Falla.     [Job 2] Construye imagen Docker
No deploya.        │ La publica en GHCR con tag "develop"
                   │
                   ▼
           [Job 3] POST al deploy hook de Staging
                   │
                   ▼
            Render descarga el código,
            construye el contenedor
            y despliega en Staging
                   │
                   ▼
         Se verifica en Staging:
         https://fastapi2-staging.onrender.com
                   │
                   ▼
         git merge develop → main
         git push origin main
                   │
                   ▼
  GitHub Actions se activa nuevamente
          │
          ▼
  [Job 1] Tests  →  [Job 2] Build imagen tag "main"
          │
          ▼
  [Job 4] POST al deploy hook de Producción
          │
          ▼
   Render despliega en Producción:
   https://fastapi2-production.onrender.com
```

---

## 10. Cómo correr el proyecto localmente

### Sin Docker

```bash
# Clonar el repositorio
git clone https://github.com/sebaheredia/FastApi2.git
cd FastApi2

# Instalar dependencias
pip install -r requirements.txt

# Correr la API
uvicorn main:app --reload

# La API queda disponible en:
# http://localhost:8000
# http://localhost:8000/docs  ← documentación interactiva

# Correr los tests
pytest test_main.py -v
```

### Con Docker

```bash
# Construir la imagen
docker build -t fastapi2 .

# Correr el contenedor
docker run -p 8000:8000 fastapi2

# La API queda disponible en http://localhost:8000
```

El flag `--reload` (solo sin Docker) hace que uvicorn reinicie automáticamente cada vez que guardás un cambio en el código, útil durante el desarrollo.

---

## Contacto

ADAIP (Área de Desarrollos Avanzados de Imágenes y Percepción)
