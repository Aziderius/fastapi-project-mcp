# MEMORY.md — API FastAPI + PostgreSQL

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Capas en `app/`, acceso a datos **async** (`AsyncSession` + asyncpg). Sin tests, migraciones ni autenticación.
- Endpoints: `/hello-world`, `/healthz`, `GET/POST /categories`, `GET /categories/{id}`, `GET/POST /products`, `GET/PUT /products/{id}`.
- Spec 001 (`POST /products`): implementada y verificada el 2026-10-07; 2 desviaciones conocidas (nulo como tipo, `NaN` → 500).
- Spec 002 (`PUT /products/{id}`, editar productos): **implementada** y verificada el 2026-10-08 (T-1 a T-9; @reviewer: CUMPLIDA, RF-8 como limitación conocida aceptada). 24 productos / 6 categorías y hash de `/products` iguales antes y después.
- Tablas creadas a mano: `categories` (6 filas) y `products` (24 filas). Las pruebas no dejan datos.
- En JSON el separador decimal es el punto: `500,00` da 422 `json_invalid`.
- Repo público `Aziderius/fastapi-project-mcp` (rama `main`). Cambios sin commit: se hace solo cuando el usuario lo pide.

## Decisiones de la spec 002 (D1–D9)

- D1 `ProductUpdate(ProductCreate)` vacío: mismas validaciones que crear. D9: asignación atributo a atributo (sustitución completa; descripción ausente → `null`).
- D2 `product_name_key`: strip + NFC + `str.maketrans` del alfabeto español (sin `lower`/`casefold`); `Camión` = `CAMION`, `Año` ≠ `Ano`, `ß` ≠ `SS`, `À` ≠ `à`, signo kelvin = `K`.
- D3 409 `Ya existe otro producto con el nombre {nombre}` solo si cambia la clave; comparación en Python sobre los demás productos (sin UNIQUE). Crear sigue admitiendo repetidos.
- D4 `db.get(Product, id, with_for_update=True)` **sin** `joinedload`: comprobado que con `joinedload` PostgreSQL falla ("FOR UPDATE no puede ser aplicado al lado nulable de un outer join").
- D5 categoría inexistente → 422 (comprobación previa + respaldo `IntegrityError` 23503). D6 reconsulta con `joinedload` y `populate_existing=True`.
- D7 `fits_in_integer` (MIN/MAX_INTEGER) en GET, PUT y POST de productos: ids enormes → 404/422, nunca 500.
- D8 orden de errores: JSON mal formado (422 solo) → formato ruta+cuerpo (422 juntos, FastAPI) → 404 → 422 categoría → 409. Comprobado en T-8 (E20–E24).

## Aprendizajes y errores a evitar

- Sin `.env` la app no arranca (`Field required`). Fallos de conexión sin tocar `.env`: variables solo en el proceso de prueba (`DB_PORT=1`).
- Escrituras: servidor en el 8002 con `get_db` sustituido por sesiones `join_transaction_mode="create_savepoint"` sobre una transacción externa que se deshace. El usuario tiene `uvicorn --reload` en el 8000.
- asyncpg: puerto cerrado o host inexistente → `OSError` sin envolver; contraseña mala → `DBAPIError`; id > 2 147 483 647 en `db.get` → `DBAPIError` (500).
- En async, cualquier carga implícita falla (`MissingGreenlet`); `db.get` sin `populate_existing=True` ignora el `joinedload`.
- Pydantic: `StrictInt` rechaza `"5"`, `5.0` y `true`; `Decimal` estricto acepta texto (de ahí el validador del precio). Un nulo sale como error de tipo.
- FastAPI: `NaN`/`Infinity` en un campo previsto → 422 imposible de serializar → 500; en un dato no previsto se ignora (200). Números de > ~4300 cifras: cuerpo → 400, ruta → 422.
- PowerShell: generar scripts de Python desde Bash (`del` en un here-string dispara un bloqueo). `Path.write_text` en Windows escribe CRLF.

## Decisiones generales (y por qué)

- Async para aprender el enfoque profesional; `SQLAlchemy[asyncio]` porque instala `greenlet`. `expire_on_commit=False` para no hacer IO implícita.
- `/healthz` captura `SQLAlchemyError` y `OSError` (PostgreSQL apagado → 503). Nunca `create_all`; `URL.create`; `joinedload` + `lazy="raise"`.
- `docs/constitution.md` manda; la sección del README es el contrato y va antes del código.
- Mensajes automáticos de FastAPI/Pydantic en inglés: el principio 6 solo cubre los `detail` propios.

## Pendientes

- R4 de la spec 002 (Python 3.12): el entorno 3.12 no tiene dependencias; omitido por decisión del usuario el 2026-10-08.
- Spec 001 no tocada (decisión del usuario): describe `NaN`/`Infinity` → 500 solo en precio y stock, pero pasa en cualquier campo previsto del cuerpo.
- `GET /categories/{id}` con ids enormes → 500 (falta `fits_in_integer`).
- Erratas menores de la spec 002 (sin decidir si se corrigen): filas pegadas en la tabla de casos límite (~línea 177 de `spec.md`) y ejemplo `books` en vez de `clothes` (~línea 45 de `plan.md`).
- Decidir: `NaN` → 500 global (un manejador de errores choca con "main.py solo registra routers"); nulo en obligatorio como "ausente".
- Paginación en `GET /products`; `timeout` de asyncpg; `CategoryCreate.description` vacía → `null`; estructura del README desactualizada.
