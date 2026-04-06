# FastApi2 — API REST con CI/CD

Proyecto de ejemplo de una API REST construida con **FastAPI** (Python), con integración y despliegue continuo (CI/CD) usando **GitHub Actions** y **Render**.

---

## Índice

1. [¿Qué es esta API?](#1-qué-es-esta-api)
2. [Estructura del repositorio](#2-estructura-del-repositorio)
3. [La aplicación Python](#3-la-aplicación-python)
4. [Tests automáticos](#4-tests-automáticos)
5. [Dependencias](#5-dependencias)
6. [CI/CD con GitHub Actions](#6-cicd-con-github-actions)
7. [Despliegue en Render](#7-despliegue-en-render)
8. [Flujo completo de trabajo](#8-flujo-completo-de-trabajo)
9. [Cómo correr el proyecto localmente](#9-cómo-correr-el-proyecto-localmente)

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

## 6. CI/CD con GitHub Actions

### ¿Qué es CI/CD?

- **CI (Integración Continua)**: cada vez que se sube código, se corre una batería de tests automáticamente para verificar que nada está roto.
- **CD (Despliegue Continuo)**: si los tests pasan, el código se deploya automáticamente al servidor correspondiente.

El objetivo es detectar errores rápido y garantizar que lo que llega a producción siempre funciona.

### `ci.yml`

```yaml
name: CI/CD

on:
  push:
    branches:
      - main
      - develop
```

El pipeline se activa en cada `git push` a las ramas `main` o `develop`.

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

Este job:
1. Clona el repositorio en una máquina virtual Ubuntu limpia.
2. Instala Python 3.13.
3. Instala las dependencias.
4. Corre todos los tests con pytest.

Si algún test falla, los jobs siguientes no se ejecutan.

---

### Job 2: Deploy a Staging

```yaml
deploy-staging:
  needs: test
  if: github.ref == 'refs/heads/develop'
  steps:
    - run: |
        curl -X POST "${{ secrets.RENDER_STAGING_DEPLOY_HOOK }}" ...
```

- Solo corre si el push fue a la rama **`develop`**.
- `needs: test` garantiza que los tests pasaron antes de deployar.
- Hace una petición POST a la URL del deploy hook de Render (guardada como secret en GitHub).
- Si Render responde 200/201/202, el job es exitoso.

---

### Job 3: Deploy a Producción

```yaml
deploy-production:
  needs: test
  if: github.ref == 'refs/heads/main'
  steps:
    - run: |
        curl -X POST "${{ secrets.RENDER_PRODUCTION_DEPLOY_HOOK }}" ...
```

- Solo corre si el push fue a la rama **`main`**.
- Idéntico al de staging pero apunta al servicio de producción.

---

### Secrets de GitHub

Los deploy hooks son URLs sensibles (quien las tenga puede triggerear un deploy). Por eso se guardan como **secrets** en GitHub (Settings → Secrets and variables → Actions) y se referencian en el YAML como `${{ secrets.NOMBRE }}`. GitHub los inyecta en tiempo de ejecución sin exponerlos en los logs.

| Secret | Usado por |
|---|---|
| `RENDER_STAGING_DEPLOY_HOOK` | Deploy a Staging (rama `develop`) |
| `RENDER_PRODUCTION_DEPLOY_HOOK` | Deploy a Producción (rama `main`) |

---

### Resumen del flujo de ramas

| Push a | Tests | Staging | Producción |
|---|---|---|---|
| `develop` | ✅ Corre | ✅ Se deploya | ⊘ Se saltea |
| `main` | ✅ Corre | ⊘ Se saltea | ✅ Se deploya |

---

## 7. Despliegue en Render

**Render** es una plataforma de hosting en la nube (PaaS — Platform as a Service). Se encarga de toda la infraestructura: servidores, redes, SSL, escalado. Vos solo subís el código.

### ¿Qué hace Render cuando recibe el deploy hook?

1. Clona el repositorio desde GitHub (la rama configurada).
2. Instala las dependencias: `pip install -r requirements.txt`.
3. Levanta el servidor con el comando de inicio: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. Expone el servicio en una URL pública con HTTPS.

### Los dos servicios

| Servicio | Rama | URL |
|---|---|---|
| `fastapi2-staging` | `develop` | `https://fastapi2-staging.onrender.com` |
| `fastapi2-production` | `main` | `https://fastapi2-production.onrender.com` |

### Deploy Hook

Es una URL única por servicio que al recibir un POST triggearea un nuevo deploy. Render responde con `202 Accepted` si la solicitud fue recibida correctamente y procesa el deploy en segundo plano.

### Plan gratuito

El plan free de Render tiene una limitación: el servicio se **apaga automáticamente** después de 15 minutos de inactividad. La primera petición después de ese período puede demorar 50 segundos o más mientras el servidor vuelve a levantarse. Esto es normal en el plan gratuito y no afecta el funcionamiento.

---

## 8. Flujo completo de trabajo

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
Falla.     [Job 2] POST al deploy hook de Staging
No deploya.        │
                   ▼
            Render deploya en Staging
                   │
                   ▼
         Se verifica en Staging
                   │
                   ▼
         git merge develop → main
         git push origin main
                   │
                   ▼
         [Job 3] POST al deploy hook de Producción
                   │
                   ▼
          Render deploya en Producción
```

---

## 9. Cómo correr el proyecto localmente

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

El flag `--reload` hace que uvicorn reinicie automáticamente cada vez que guardás un cambio en el código, útil durante el desarrollo.

---

## Contacto

ADAIP (Área de Desarrollos Avanzados de Imágenes y Percepción)