# CLAUDE.md — API FastAPI + PostgreSQL

API REST en fase inicial construida con FastAPI, SQLAlchemy 2.0 y PostgreSQL. La mantiene una persona que está aprendiendo FastAPI, así que el objetivo es una base simple, limpia y fácil de leer, que crecerá poco a poco con productos y categorías.

Los principios del proyecto están en `docs/constitution.md`. Este archivo recoge las reglas operativas; si chocan, manda la constitución.

## Stack y estructura

- Python 3.12 o superior (la instalación local es 3.14, pero el código debe funcionar en 3.12).
- FastAPI + Uvicorn.
- SQLAlchemy 2.0 en modo **async** (`SQLAlchemy[asyncio]`, que instala `greenlet`) con `asyncpg` como driver.
- PostgreSQL en local, sin Docker.
- `pydantic-settings` para leer la configuración desde `.env`.
- Dependencias directas fijadas en `requirements.txt`.

Arquitectura por capas dentro de `app/`:

- `core/config.py`: clase `Settings` que lee `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` y `DB_NAME`, y construye `settings.database_url` con `sqlalchemy.URL.create`.
- `core/security.py`: marcador de posición para la autenticación futura. No tiene código.
- `database/database.py`: crea `engine` (`create_async_engine`) y `SessionLocal` (`async_sessionmaker` con `expire_on_commit=False`) al importarse.
- `database/dependencies.py`: `get_db()`, la `AsyncSession` por petición que se inyecta con `Depends(get_db)`.
- `models/models.py`: clase `Base` (`DeclarativeBase`) y los modelos. Contiene `Category` y `Product`, que reflejan las tablas `categories` y `products` existentes. `Product.category_id` es `ForeignKey` y `Product.category` es una `relationship` de un solo sentido con `lazy="raise"`.
- `schemas/`: modelos Pydantic de entrada y salida, un archivo por recurso. `category.py` tiene `CategoryCreate` (normaliza el nombre), `CategoryRead` y `CategorySummary` (`id` y `name`, para anidar); `product.py` tiene `ProductCreate` (números estrictos, nombre y descripción recortados, `MAX_INTEGER` y `MIN_INTEGER`), `ProductUpdate` (subclase vacía de `ProductCreate`: mismas reglas), `product_name_key` (clave para comparar nombres de producto: recorte, NFC y tabla del alfabeto español) y `ProductRead` (`price` es `Decimal` y sale en el JSON como texto; incluye `category`).
- `routers/`: un `APIRouter` por recurso. `health.py` tiene `/hello-world` y `/healthz`. `categories.py` tiene `GET /categories`, `GET /categories/{category_id}` y `POST /categories`. `products.py` tiene `GET /products`, `GET /products/{product_id}`, `POST /products` y `PUT /products/{product_id}` (sustitución completa).
- `main.py`: crea la app y registra los routers. Nada más.

Fuera de `app/`: `docs/constitution.md` (principios del proyecto) y `specs/NNN-*/` (diseño de cada funcionalidad: `spec.md`, `plan.md` y `tasks.md`). La sección de cada endpoint en el `README.md` es el contrato público y se escribe antes del código (principio 2).

## Comandos

Todo se ejecuta desde la raíz del proyecto, en Windows con PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

La API queda en http://127.0.0.1:8000 y la documentación en http://127.0.0.1:8000/docs.

Todavía no hay tests, linter ni herramienta de migraciones configurados.

## Convenciones

- Código simple y legible para alguien que está empezando. Mejor explícito que ingenioso.
- Comentarios, docstrings, mensajes de error y README en **español**.
- Nombres de archivos, variables, funciones y clases en inglés, siguiendo lo que ya existe (`get_db`, `products.py`).
- `main.py` solo crea la app y llama a `include_router`. Nunca define endpoints.
- Cada recurso nuevo tiene su router en `routers/`, su schema en `schemas/` y se registra en `main.py`.
- Los endpoints que usan la base de datos reciben la sesión con `Depends(get_db)`. Nunca crean sesiones a mano.
- Los endpoints son `async def` y usan `await` en todo lo que habla con la base de datos: `execute`, `scalars`, `get`, `commit`, `rollback` y `refresh` (`db.add` no lleva `await`). Nunca dependas de cargas implícitas: en async fallan con `MissingGreenlet`.
- Sintaxis moderna de SQLAlchemy 2.0: `DeclarativeBase`, `Mapped`, `mapped_column`, `select()` y `text()` para SQL crudo.
- Las relaciones se declaran con `lazy="raise"` y se cargan siempre de forma explícita (`joinedload` o `selectinload`) en la consulta, para evitar el problema de N+1 consultas.
- Archivo de referencia para nuevos routers: `app/routers/health.py`.

## Reglas de dominio / trampas conocidas

- `routers/health.py` **no lleva prefijo**. Las rutas deben quedar exactamente `/hello-world` y `/healthz`.
- `/healthz` ejecuta `SELECT 1` mediante `get_db()`: devuelve 200 `{"status": "ok", "database": "ok"}`, o 503 `{"status": "error", "database": "unavailable"}` si salta un `SQLAlchemyError` o un `OSError` (asyncpg no envuelve los fallos de conexión, como servidor apagado o host inexistente, en errores de SQLAlchemy). No cambies ese contrato.
- Las cinco variables de `DB_*` son obligatorias. Si falta una, la app falla al importar con un error `Field required`, no al recibir una petición.
- La URL de conexión se construye con `URL.create`, así que la contraseña no necesita codificarse. No la sustituyas por un string formateado a mano.
- `engine` se crea al importar `database.py`. Cualquier cambio en la configuración afecta al arranque de toda la app.
- La base de datos indicada en `DB_NAME` debe existir antes de arrancar; la app no la crea.
- No hay migraciones: crear o modificar tablas es una decisión que hay que consultar antes.
- Las tablas `categories` y `products` se crearon a mano con SQL y ya tienen datos. Los modelos deben reflejar exactamente el esquema real. Nunca uses `Base.metadata.create_all` ni alteres tablas.
- Los nombres de categoría se guardan sin espacios en los extremos y en minúsculas. La restricción UNIQUE de PostgreSQL distingue mayúsculas, así que la normalización la hace el schema.
- Códigos de error: un recurso de la ruta que no existe devuelve 404; un id del cuerpo de la petición que no existe (como `category_id` al crear un producto) devuelve 422; un duplicado devuelve 409, tanto si lo detecta PostgreSQL (`IntegrityError` por UNIQUE) como si lo comprueba el endpoint sin UNIQUE detrás (nombre de producto repetido al modificar, comparado con `product_name_key`). Siempre con `detail` en español. Busca por clave primaria con `db.get(Modelo, id)`.
- Para devolver un objeto recién creado con una relación, vuelve a consultarlo con `db.get(..., options=[joinedload(...)], populate_existing=True)`. Sin `populate_existing`, `db.get` devuelve el objeto que ya está en la sesión, ignora el `joinedload` y la respuesta falla por `lazy="raise"`.
- Un id mayor que 2 147 483 647 (máximo de INTEGER) hace que asyncpg lance `DBAPIError` en `db.get`: compruébalo antes de consultar. En `routers/products.py` se hace con `fits_in_integer` (límites `MIN_INTEGER` y `MAX_INTEGER`); `GET /categories/{category_id}` todavía no lo comprueba (pendiente).
- Para bloquear una fila (`db.get(..., with_for_update=True)`) no añadas `joinedload` en esa misma lectura: PostgreSQL rechaza `FOR UPDATE` en el lado nulable de un outer join. Carga la relación después, en la reconsulta con `populate_existing=True`.
- No uses sintaxis o librerías de Python posteriores a 3.12, aunque la instalación local sea más nueva.

## Límites y datos sensibles

- Nunca escribas credenciales ni datos de conexión en el código.
- Nunca leas, muestres ni modifiques el contenido de `.env`. No hay `.env.example`: la configuración vive solo en `.env`. Si cambia `Settings`, actualiza la sección de variables del `README.md` y avisa al usuario de qué variables debe añadir a su `.env`.
- No imprimas ni registres en logs la contraseña ni la URL completa de conexión.
- No ejecutes SQL destructivo (`DROP`, `TRUNCATE`, `DELETE` o `UPDATE` sin `WHERE`) contra la base de datos.
- Siempre: actualizar `MEMORY.md` al terminar cada tarea. 

## Forma de trabajar

- Si el cambio toca más de un archivo, presenta un plan breve antes de escribir código.
- Haz cambios pequeños y enfocados en lo que se ha pedido. No añadas nada que no se haya solicitado.
- Al terminar, explica en español y en pocas líneas qué cambiaste, cómo probarlo y qué decisiones tomaste por tu cuenta.

## Memoria 
- Al empezar, lee `MEMORY.md` para conocer el estado del proyecto y las decisiones tomadas.
- Al terminar una tarea, actualízalo: estado actual, decisiones importantes (con su porqué) y errores a evitar.
- Mantenlo breve (máximo ~50 líneas): resume o elimina lo que ya no aporte. - Si algo se convierte en una regla permanente, propón moverlo a `CLAUDE.md` en lugar de dejarlo en la memoria.
- No guardes nunca datos sensibles (claves, tokens, datos personales). 

✅ **Siempre:**
- Mantener los comentarios en español y el código fácil de leer.
- Registrar en `main.py` cada router nuevo.
- Mantener la tabla de variables del `README.md` sincronizada con `Settings`.
- Verificar el cambio antes de darlo por terminado (ver sección siguiente).

⚠️ **Pregunta antes:**
- Añadir dependencias nuevas o cambiar versiones en `requirements.txt`.
- Crear archivos o carpetas fuera de la estructura descrita.
- Cambiar el formato de las respuestas de la API, sobre todo de `/healthz`.
- Crear modelos o tablas, o introducir una herramienta de migraciones.
- Añadir autenticación, tests, Docker o un linter.
- Modificar `docs/constitution.md`.

🚫 **Nunca:**
- Definir endpoints en `main.py`.
- Añadir un prefijo al router de `health.py`.
- Tocar `.env` o subir secretos al repositorio.
- Ejecutar SQL destructivo contra la base de datos.
- Hacer commit o push sin que el usuario lo pida explícitamente. Aprobar un plan o decir "dale" no cuenta como permiso: los cambios se dejan sin confirmar en el árbol de trabajo.

## Reglas
- Lee `docs/constitution.md` y la spec activa (`specs/NNN-*/`) antes de tocar código.

## Verificación

Antes de dar un cambio por terminado:

1. Arranca el servidor con `uvicorn app.main:app --reload` y comprueba que no hay errores al importar.
2. Prueba los endpoints:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/healthz
```

3. Comprueba que `/healthz` devuelve `{"status": "ok", "database": "ok"}` con PostgreSQL encendido.
4. Abre http://127.0.0.1:8000/docs y confirma que aparecen los endpoints esperados.
5. Si el cambio afecta a la conexión, comprueba también que `/healthz` devuelve 503 con PostgreSQL detenido, o arrancando un servidor de prueba con una variable de entorno solo para ese proceso (por ejemplo `DB_PORT=1`), sin tocar `.env`.
6. Las escrituras (por ejemplo, el 201 de un `POST`) se prueban dentro de una transacción que se deshace al final: no se dejan datos de prueba.
