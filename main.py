from fastapi import FastAPI

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

@app.get("/")
def root():
    return {"message": "Bienvenido a FastAPI"}
