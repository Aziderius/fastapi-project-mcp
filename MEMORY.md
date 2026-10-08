# MEMORY.md — API FastAPI + PostgreSQL

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Capas en `app/`, acceso a datos **async** (`AsyncSession` + asyncpg). Sin tests, migraciones ni autenticación.
- Endpoints: `/hello-world`, `/healthz`, `GET/POST /categories`, `GET /categories/{id}`, `GET/POST /products`, `GET /products/{id}`.
- `POST /products` (spec 001) implementado y verificado el 2026-10-07: 22 casos de error, 12 de éxito (en transacción deshecha), carrera de clave foránea, regresión 11/11 y Python 3.12. Las 9 tareas de `specs/001-crear-productos/tasks.md` están hechas y la spec está en estado "implementada", con las dudas resueltas y 2 desviaciones conocidas (nulo como tipo, `NaN` → 500).
- Tablas creadas a mano: `categories` (6 filas) y `products` (24 filas: las 23 originales y una creada por el usuario desde `/docs` el 2026-10-07). Las pruebas no dejan datos.
- En JSON el separador decimal es el punto: `500,00` da 422 `json_invalid` (el usuario tropezó con esto).
- Repo público `Aziderius/fastapi-project-mcp` (rama `main`). Cambios sin commit: se hace solo cuando el usuario lo pide.

## Aprendizajes y errores a evitar

- Sin `.env` la app no arranca (`Field required`). `.gitignore` cubre `.env`, `.env.*`, `.venv/`, `__pycache__/` y `.claude/settings.local.json`.
- Verificar con lecturas o transacciones deshechas. Las escrituras de `POST` se prueban con un servidor (puerto 8002) que sustituye `get_db` por sesiones con `join_transaction_mode="create_savepoint"` sobre una transacción externa que se deshace.
- El usuario suele tener `uvicorn --reload` en el 8000: probar en el 8001 o el 8002.
- Fallos de conexión sin tocar `.env`: variables de entorno solo en el proceso de prueba (`DB_PORT=1`).
- asyncpg: puerto cerrado o host inexistente → `OSError` sin envolver; contraseña mala → `DBAPIError`.
- asyncpg: `db.get` con un id mayor que 2 147 483 647 lanza `DBAPIError` (500). `POST /products` lo evita; los GET por id **todavía no**.
- En async, cualquier carga implícita falla (`MissingGreenlet`); con `lazy="raise"`, `db.get` sin `populate_existing=True` reutiliza el objeto de la sesión e ignora el `joinedload`.
- Pydantic: `StrictInt` rechaza `"5"`, `5.0` y `true`; `Decimal` en modo estricto **acepta** texto, de ahí el validador del precio. Un nulo se informa como error de tipo, no como `missing`.
- FastAPI: un `NaN`/`Infinity` en el cuerpo se rechaza, pero la respuesta 422 no se puede serializar → 500 (en todos los endpoints con cuerpo).
- PowerShell: escribir scripts de Python con `del` dentro de un here-string dispara un bloqueo de seguridad (`del` es alias de `Remove-Item`); generarlos desde Bash.

## Decisiones (y por qué)

- Async para aprender el enfoque profesional; `SQLAlchemy[asyncio]` porque SQLAlchemy 2.1 solo instala `greenlet` con ese extra.
- `expire_on_commit=False`: tras el commit, leer atributos caducados sería IO implícita.
- `/healthz` captura `SQLAlchemyError` y `OSError` (PostgreSQL apagado → 503, no 500).
- Nunca `create_all`; variables `DB_*` con `URL.create`; `joinedload` + `lazy="raise"` contra el N+1.
- `docs/constitution.md` manda. `specs/NNN-*/` contiene el diseño; la sección del README es el contrato y va antes del código.
- `POST /products`: categoría inexistente → 422 (es un dato del cuerpo, no la ruta); comprobación previa con `db.get` y, como respaldo, `IntegrityError` con `sqlstate == "23503"`. Otros errores de integridad → 500.
- Se vuelve a consultar el producto creado con `populate_existing=True`: trae la categoría y el precio con 2 decimales (`1e2` → `"100.00"`).
- Números estrictos (sin texto ni booleanos), datos extra ignorados, nombres repetidos permitidos, base de datos caída → 500.
- Los mensajes automáticos de FastAPI/Pydantic siguen en inglés: el principio 6 solo cubre los `detail` propios.

## Próximos pasos

- Decidir: `NaN`/`Infinity` → 500 (solución global con un manejador de errores, que choca con "main.py solo registra routers").
- Decidir: GET por id con ids enormes → 500 en lugar de 404 (defecto desde la migración a async).
- Decidir: un nulo en un obligatorio debe informarse como "ausente" según la spec (RF-2), y hoy sale como error de tipo.
- Agentes SDD (`.claude/agents/`) corregidos el 2026-10-07: skill `fastapi-project` (antes mal escrita como `fastapi-proyecto`), escrituras verificadas en transacción deshecha (nunca registros reales), servidor del usuario en el 8000, `curl.exe -i` y nunca commit.
- Paginación en `GET /products`; `timeout` de conexión de asyncpg; `CategoryCreate.description` vacía → `null`; estructura del README desactualizada.
