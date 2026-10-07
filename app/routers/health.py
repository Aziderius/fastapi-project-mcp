# Rutas de comprobación del estado de la API.
# Sin prefijo: las rutas quedan exactamente como /hello-world y /healthz.
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependencies import get_db

router = APIRouter(tags=["health"])


@router.get("/hello-world")
async def hello_world():
    """Devuelve un saludo simple para comprobar que la API responde."""
    return {"message": "Hello World"}


@router.get("/healthz")
async def healthz(db: AsyncSession = Depends(get_db)):
    """Comprueba la conexión con PostgreSQL ejecutando SELECT 1."""
    try:
        await db.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError):
        # La base de datos no responde: devolvemos 503 (servicio no disponible).
        # OSError: asyncpg no envuelve los fallos de conexión (servidor apagado,
        # host inexistente) en errores de SQLAlchemy.
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )
    return {"status": "ok", "database": "ok"}
