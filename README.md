# Practica API

API construida con **FastAPI**, **SQLAlchemy 2.0** y **PostgreSQL**. El acceso a la base de datos es **async** (`AsyncSession` con el driver `asyncpg`).

Esta es la primera versión del proyecto: una base limpia y organizada por capas, preparada para crecer (más adelante se añadirán productos y categorías).

## Requisitos

- Python 3.12 o superior
- PostgreSQL instalado y corriendo en local

## Estructura del proyecto

```
.
├── app/
│   ├── core/
│   │   ├── config.py        # Configuración leída desde el archivo .env
│   │   └── security.py      # Reservado para la futura autenticación
│   ├── database/
│   │   ├── database.py      # Engine y SessionLocal de SQLAlchemy
│   │   └── dependencies.py  # Dependencia get_db() (abre y cierra la sesión)
│   ├── models/
│   │   └── models.py        # Base declarativa de SQLAlchemy (sin modelos todavía)
│   ├── routers/
│   │   ├── categories.py    # Router de categorías (vacío)
│   │   ├── health.py        # Endpoints /hello-world y /healthz
│   │   └── products.py      # Router de productos (vacío)
│   ├── schemas/
│   │   ├── category.py      # Esquemas Pydantic de categorías (vacío)
│   │   └── product.py       # Esquemas Pydantic de productos (vacío)
│   └── main.py              # Crea la app y registra los routers
├── .env                     # Variables de entorno (no se sube a git)
├── .gitignore
├── requirements.txt         # Dependencias con versiones fijadas
└── README.md
```

### Capas

| Carpeta     | Responsabilidad                                                  |
|-------------|------------------------------------------------------------------|
| `core`      | Configuración general y, en el futuro, seguridad.                |
| `database`  | Conexión a PostgreSQL y gestión de sesiones.                     |
| `models`    | Tablas de la base de datos (modelos de SQLAlchemy).              |
| `schemas`   | Validación de los datos que entran y salen de la API (Pydantic). |
| `routers`   | Endpoints de la API, agrupados por tema.                         |

## Puesta en marcha en local

Todos los comandos se ejecutan desde la raíz del proyecto.

### 1. Crear y activar el entorno virtual

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Si PowerShell bloquea la activación, ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 2. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 3. Crear la base de datos

Conéctate a PostgreSQL (por ejemplo con `psql -U postgres`) y crea la base de datos:

```sql
CREATE DATABASE practica;
```

### 4. Configurar las variables de entorno

Crea un archivo llamado `.env` en la raíz del proyecto con este contenido, cambiando los valores por los tuyos:

```
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=practica
```

> En Windows, comprueba que el archivo se llama exactamente `.env` y no `.env.txt` (puedes verlo con `dir -Force`).

| Variable      | Descripción                      | Ejemplo     |
|---------------|----------------------------------|-------------|
| `DB_USER`     | Usuario de PostgreSQL            | `postgres`  |
| `DB_PASSWORD` | Contraseña del usuario           | `postgres`  |
| `DB_HOST`     | Servidor de la base de datos     | `localhost` |
| `DB_PORT`     | Puerto de PostgreSQL             | `5432`      |
| `DB_NAME`     | Nombre de la base de datos       | `practica`  |

La URL de conexión se construye automáticamente a partir de estas variables (en `app/core/config.py`), así que la contraseña puede contener caracteres especiales como `@` o `:` sin codificarlos.

> El archivo `.env` contiene contraseñas y **no se sube a git** (está en `.gitignore`).

### 5. Arrancar el servidor

```bash
uvicorn app.main:app --reload
```

La API queda disponible en http://127.0.0.1:8000. Con `--reload`, el servidor se reinicia automáticamente al guardar cambios en el código.

## Endpoints

| Método | Ruta           | Descripción                                    |
|--------|----------------|------------------------------------------------|
| GET    | `/hello-world` | Devuelve un saludo para comprobar que la API responde. |
| GET    | `/healthz`     | Comprueba la conexión con PostgreSQL (`SELECT 1`). |
| GET    | `/categories`  | Lista todas las categorías, ordenadas por `id`. |
| GET    | `/categories/{category_id}` | Devuelve una categoría por su `id`. |
| POST   | `/categories`  | Crea una categoría nueva. |
| GET    | `/products`    | Lista todos los productos, ordenados por `id`. |
| GET    | `/products/{product_id}` | Devuelve un producto por su `id`. |
| POST   | `/products`    | Crea un producto nuevo en una categoría existente. |

### `GET /hello-world`

```json
{"message": "Hello World"}
```

### `GET /healthz`

Si la base de datos responde → **200 OK**:

```json
{"status": "ok", "database": "ok"}
```

Si la base de datos no responde → **503 Service Unavailable**:

```json
{"status": "error", "database": "unavailable"}
```

### `GET /categories`

**200 OK** con la lista de categorías. Los campos `description` y `created_at` pueden ser `null`.

```json
[
  {"id": 1, "name": "electronics", "description": "Electronic devices, gadgets and accessories", "created_at": "2026-10-06T13:28:14.312797"}
]
```

### `GET /categories/{category_id}`

- Si existe → **200 OK** con la categoría (misma forma que en el listado).
- Si no existe → **404 Not Found**:

```json
{"detail": "No existe ninguna categoría con el id 999"}
```

- Si `category_id` no es un número entero → **422**.

### `POST /categories`

Cuerpo de la petición (`description` es opcional):

```json
{"name": "Garden", "description": "Productos de jardín"}
```

- El nombre se guarda sin espacios en los extremos y en minúsculas (`" Garden "` → `garden`).
- Creada → **201 Created** con la categoría (incluye `id` y `created_at`).
- El nombre ya existe → **409 Conflict**: `{"detail": "Ya existe una categoría con el nombre 'garden'"}`.
- Nombre vacío o de más de 50 caracteres, o `description` de más de 255 → **422**.

### `GET /products`

**200 OK** con la lista de productos (`[]` si la tabla está vacía). `description` puede ser `null`.

- `price` se devuelve como texto (`"19.99"`) para conservar los decimales exactos.
- `category_id` es el `id` de la categoría del producto y `category` incluye su `id` y su `name`.

```json
[
  {"id": 1, "name": "Smartphone", "description": "Latest generation smartphone with high-resolution display", "price": "699.99", "stock": 15, "category_id": 1, "category": {"id": 1, "name": "electronics"}, "created_at": "2026-10-06T13:28:21.054510"}
]
```

### `GET /products/{product_id}`

- Si existe → **200 OK** con el producto (misma forma que en el listado).
- Si no existe → **404 Not Found**:

```json
{"detail": "No existe ningún producto con el id 999"}
```

- Si `product_id` no es un número entero → **422**.

### `POST /products`

Cuerpo de la petición (`description` es opcional):

```json
{"name": "Teclado", "description": "Teclado mecánico", "price": 49.9, "stock": 0, "category_id": 1}
```

| Campo | Reglas |
|-------|--------|
| `name` | Obligatorio. Se quitan los espacios en blanco de los extremos (también tabuladores y saltos de línea) y se respetan las mayúsculas. Entre 1 y 150 caracteres. |
| `description` | Opcional. Se recortan los extremos igual que el nombre; si queda vacía se guarda como `null`. Máximo 255 caracteres. |
| `price` | Obligatorio. Número (no texto), mayor que 0 y menor que 100 000 000, con 2 decimales como máximo. |
| `stock` | Obligatorio. Número entero (no texto ni `5.0`), de 0 a 2 147 483 647. |
| `category_id` | Obligatorio. Número entero con el `id` de una categoría existente. |

- Los campos que no aparecen en la tabla (por ejemplo `id` o `created_at`) se ignoran. Se pueden repetir nombres de producto.
- Creado → **201 Created** con el producto completo, con la misma forma que `GET /products/{product_id}`:

```json
{"id": 24, "name": "Teclado", "description": "Teclado mecánico", "price": "49.90", "stock": 0, "category_id": 1, "category": {"id": 1, "name": "electronics"}, "created_at": "2026-10-07T18:00:00.000000"}
```

- Algún campo falta o no cumple las reglas, o el cuerpo está mal formado → **422** con la lista de errores de validación de FastAPI (los mensajes automáticos van en inglés; el de un precio que no es un número es `"El precio debe ser un número"`).
- La categoría no existe → **422**:

```json
{"detail": "No existe ninguna categoría con el id 999"}
```

- Limitación conocida: si un número del cuerpo llega como `NaN` o `Infinity` (no es JSON estándar), la validación lo rechaza, pero FastAPI no puede escribir ese valor en la respuesta de error y devuelve **500**. Pasa en todos los endpoints con cuerpo, también en `POST /categories`.

### Probar desde la terminal

```bash
curl http://127.0.0.1:8000/hello-world
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/categories
curl http://127.0.0.1:8000/categories/1
curl http://127.0.0.1:8000/products
curl http://127.0.0.1:8000/products/1
```

Crear un producto (ojo: lo guarda de verdad en la base de datos) desde PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/products -ContentType "application/json" -Body '{"name": "Teclado", "price": 49.9, "stock": 0, "category_id": 1}'
```

## Documentación interactiva

FastAPI genera la documentación automáticamente:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Problemas frecuentes

- **`/healthz` devuelve 503**: revisa que PostgreSQL esté arrancado, que la base de datos exista y que los valores de `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` y `DB_NAME` sean correctos.
- **Error de validación al arrancar (`Field required`)**: falta el archivo `.env` o alguna de las variables `DB_*` dentro de él. El mensaje indica cuál falta.
- **`ModuleNotFoundError: No module named 'app'`**: ejecuta `uvicorn` desde la raíz del proyecto, no desde dentro de `app/`.
- **`MissingGreenlet` (o `greenlet_spawn has not been called`)**: el código ha intentado leer de la base de datos sin `await`, por ejemplo al acceder a una relación que no se cargó con `joinedload`. En modo async toda consulta debe ser explícita y con `await`.
- **`No module named 'greenlet'` o `'asyncpg'`**: reinstala las dependencias con `pip install -r requirements.txt`.
