# Dependencias de base de datos para los endpoints de FastAPI.
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Abre una sesión async para la petición y la cierra al terminar."""
    # "async with" cierra la sesión automáticamente al salir
    async with SessionLocal() as db:
        yield db
