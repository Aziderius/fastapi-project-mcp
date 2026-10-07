# MEMORY.md — API FastAPI + PostgreSQL

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Estructura por capas en `app/`. Acceso a datos **async**: `create_async_engine` + `AsyncSession` con `asyncpg`.
- Endpoints: `/hello-world`, `/healthz`, `GET/POST /categories`, `GET /categories/{id}`, `GET /products`, `GET /products/{id}`.
- Migración a async verificada (2026-10-07): las 11 respuestas idénticas byte a byte a las de la versión síncrona, en 3.14 y 3.12.10.
- `POST /categories` probado: 409 contra la base de datos real; 201 dentro de una transacción deshecha.
- Modelos `Category` y `Product`; `Product.category` es `relationship` de un solo sentido con `lazy="raise"`.
- Tablas creadas a mano: `categories` (6 filas) y `products` (23 filas; price NUMERIC(10,2), category_id FK, created_at NOT NULL).
- Configuración desde `.env` con las cinco `DB_*`. Sin tests, migraciones ni autenticación.

## Aprendizajes y errores a evitar

- Sin `.env` la app no arranca (`Field required`); en Windows puede quedar como `.env.txt` (ya ignorado por `.env.*`).
- Repo git creado (sin commits). `.gitignore` cubre `.env`, `.env.*`, `.venv/`, `__pycache__/`, `.claude/settings.local.json` y `desktop.ini`/`Thumbs.db`; `.claude/commands` y `.claude/skills` sí se suben.
- Verificar solo con lecturas o transacciones deshechas: no dejar datos de prueba. Los 409 y los rollbacks consumen ids de la secuencia (huecos normales).
- Para probar fallos de conexión sin tocar `.env`: variables de entorno solo en el proceso de prueba (`DB_PORT=1`, `DB_HOST=host.invalid`).
- asyncpg: puerto cerrado → `ConnectionRefusedError`, host inexistente → `socket.gaierror` (ambos `OSError`, sin envolver); contraseña mala → `DBAPIError`.
- En async, cualquier carga implícita falla con `MissingGreenlet`: todo con `await` y relaciones con `joinedload`.
- El usuario suele tener `uvicorn --reload` en el puerto 8000: probar siempre en el 8001.
- Para leer el esquema real de una tabla: consulta de solo lectura a `information_schema.columns`.
- Los nombres de producto tienen mayúsculas ("Smartphone"): no se normalizan.
- Con `python -X dev`, al apagar sale un `ResourceWarning` (pool sin cerrar); en modo normal no sale nada.

## Decisiones (y por qué)

- Async: decisión del usuario para aprender el enfoque profesional. Sin cambios en la API.
- `SQLAlchemy[asyncio]` en requirements: SQLAlchemy 2.1 solo instala `greenlet` con ese extra.
- `expire_on_commit=False`: tras el commit, leer atributos caducados sería IO implícita (prohibida en async).
- `/healthz` captura `SQLAlchemyError` y `OSError`: si no, un PostgreSQL apagado daría 500 en vez de 503.
- Sin `lifespan`/`engine.dispose()`: no se pidió y en modo normal no hay avisos (propuesto aparte).
- Variables `DB_*` por separado y URL con `URL.create`: la contraseña no necesita codificarse.
- Nunca `create_all`: las tablas ya existen y los modelos solo las describen.
- Nombre de categoría con `strip` + minúsculas; duplicado → 409 (`IntegrityError`); id inexistente → 404 (`db.get`).
- `price` como `Decimal` → texto en JSON; categoría anidada (`id`, `name`) además de `category_id`.
- `joinedload` + `lazy="raise"`: una sola consulta y el N+1 no puede colarse.
- Python mínimo 3.12; `AsyncGenerator[AsyncSession, None]` mantiene el `None` (forma corta desde 3.13).
- `health.py` sin prefijo.

## Próximos pasos

- Paginación en `GET /products` (principal deuda de escalabilidad).
- `POST /products` (rutas fijas antes que `/{product_id}`).
- Opcional: `timeout` de conexión de asyncpg (por defecto 60 s si el host no responde).
- `CategoryCreate.description` guarda `""` tal cual en vez de `null`.
- La sección "Estructura del proyecto" del README está desactualizada.
