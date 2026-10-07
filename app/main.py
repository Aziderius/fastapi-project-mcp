# Punto de entrada de la aplicación.
# Crea la app de FastAPI y registra los routers. No define endpoints propios.
from fastapi import FastAPI

from app.routers import categories, health, products

app = FastAPI(title="Practica API", version="0.1.0")

app.include_router(health.router)
app.include_router(products.router)
app.include_router(categories.router)
