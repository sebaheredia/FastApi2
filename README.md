# MyApp — Ejemplo de CI/CD con FastAPI y Render

API REST simple sin base de datos, con pipeline de integración y entrega continua.

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/ping` | Health check |
| GET | `/hello/{name}` | Saludo personalizado |
| POST | `/sum?a=2&b=3` | Suma dos números |

## Flujo CI/CD

```
push a develop ──► tests ──► deploy a Staging
push a main    ──► tests ──► deploy a Producción
```

Si los tests fallan, el deploy no se ejecuta.

## Correr localmente

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Correr los tests

```bash
pytest test_main.py -v
```

## Secrets requeridos en GitHub

| Secret | Descripción |
|--------|-------------|
| `RENDER_STAGING_DEPLOY_HOOK` | Deploy hook del servicio staging en Render |
| `RENDER_PRODUCTION_DEPLOY_HOOK` | Deploy hook del servicio producción en Render |

## Configurar en Render

Crear dos Web Services en Render:
- **Staging**: rama `develop`, comando `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Producción**: rama `main`, comando `uvicorn main:app --host 0.0.0.0 --port $PORT`
