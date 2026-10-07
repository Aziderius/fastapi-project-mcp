# Conexión async a la base de datos PostgreSQL con SQLAlchemy.
# Crea el "engine" (la conexión) y la fábrica de sesiones SessionLocal.
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

# El engine gestiona las conexiones con PostgreSQL.
# pool_pre_ping comprueba que la conexión sigue viva antes de usarla.
engine = create_async_engine(settings.database_url, pool_pre_ping=True)

# Cada vez que llamemos a SessionLocal() obtendremos una sesión async nueva.
# expire_on_commit=False: tras un commit los objetos conservan sus valores.
# Si caducaran, leerlos (por ejemplo, al convertirlos a JSON) haría una consulta
# implícita, y en async eso no está permitido (error MissingGreenlet).
SessionLocal = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)
