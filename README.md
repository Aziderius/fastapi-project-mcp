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
| PUT    | `/products/{product_id}` | Modifica un producto existente sustituyendo todos sus datos editables. |

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
- Si no existe → **404 Not Found**, también con 0, negativos e ids enormes que no caben en un entero de PostgreSQL (por ejemplo `99999999999999999999` o `-99999999999999999999`), nunca 500:

```json
{"detail": "No existe ningún producto con el id 999"}
```

- El `{id}` del mensaje es el número tal como se ha interpretado (`/products/05` → `id 5`).
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

### `PUT /products/{product_id}`

Modifica un producto existente con **sustitución completa**: todos los datos editables (`name`, `description`, `price`, `stock` y `category_id`) se reemplazan a la vez por los enviados. Lo que no se envía no conserva su valor anterior: si es obligatorio, es un error; si es `description`, queda `null` (aunque antes tuviera descripción).

`product_id` se interpreta igual que en `GET /products/{product_id}`: `05` → 5, `-0` → 0 y, como en la consulta, también `1.0` → 1, `5_0` → 50 y ` 5 ` (con espacios) → 5.

Cuerpo de la petición (mismo formato que en `POST /products`; `description` es opcional):

```json
{"name": "Smartphone", "price": 649.9, "stock": 10, "category_id": 2}
```

- Cada campo sigue **exactamente las mismas reglas** que en la tabla de `POST /products` (recortes, longitudes, precio y stock como números de verdad, límites), con los mismos mensajes.
- `description` ausente, `null`, `""` o solo espacios → se guarda `null`.
- Los campos que no aparecen en la tabla (`id`, `created_at`, `category`…) se ignoran sea cual sea su valor: el `id` y la fecha de alta del producto nunca cambian.
- Si un campo aparece repetido en el cuerpo, se usa el último valor.

Modificado → **200 OK** (no 201) con el producto completo, con la misma forma que `GET /products/{product_id}`: la categoría nueva si ha cambiado, y el `id` y el `created_at` originales. El nombre se guarda tal como se envía, una vez recortado:

```json
{"id": 1, "name": "Smartphone", "description": null, "price": "649.90", "stock": 10, "category_id": 2, "category": {"id": 2, "name": "clothes"}, "created_at": "2026-10-06T13:28:21.054510"}
```

Si los datos enviados (ya normalizados) son los que tiene guardados el producto, la respuesta es la misma: **200 OK** con el producto sin cambios.

**Errores**, en este orden de prioridad (si se dan varios, solo se informa del primero de la lista; ninguno modifica nada):

| Orden | Código | Cuándo | Cuerpo de la respuesta |
|-------|--------|--------|------------------------|
| 1 | **422** | El cuerpo JSON está mal formado (por ejemplo `{"price": 500,00}`). | Solo el error `json_invalid`, aunque `product_id` tampoco sea válido. |
| 2 | **422** | `product_id` no es un número entero (`abc`, `1.5`) y/o algún campo del cuerpo no cumple las reglas, o el cuerpo falta o no es un objeto (una lista, un texto). | La lista de errores de validación de FastAPI con **todos** los errores de la ruta y del cuerpo juntos (mensajes automáticos en inglés; el de un precio que no es un número es `"El precio debe ser un número"`). |
| 3 | **404** | El producto no existe (incluidos 0, negativos e ids enormes como `99999999999999999999`). | `{"detail": "No existe ningún producto con el id 999"}` |
| 4 | **422** | La categoría no existe (incluidos 0, negativos e ids enormes). | `{"detail": "No existe ninguna categoría con el id 999"}` |
| 5 | **409** | El nombre cambia y es equivalente al de **otro** producto (de cualquier categoría). | `{"detail": "Ya existe otro producto con el nombre TECLADO"}` (el nombre enviado, ya recortado) |
| — | **500** | La base de datos no está disponible o hay un error inesperado. | Respuesta genérica del servidor. |

Por ejemplo: un producto inexistente con un precio negativo da el 422 del precio (no el 404); un producto inexistente con una categoría inexistente da el 404; una categoría inexistente con un nombre repetido da el 422 de la categoría. El `{id}` de los mensajes es el número interpretado (`/products/05` → `id 5`).

**Nombres repetidos.** Al modificar, el nombre nuevo no puede ser equivalente al de otro producto. Dos nombres son equivalentes si coinciden tras quitar los espacios de los extremos y comparando así, letra a letra:

- No se distinguen mayúsculas de minúsculas en las letras del alfabeto español (A–Z, Ñ, á, é, í, ó, ú y ü), ni las vocales con tilde o diéresis de la vocal sin marca: `Camión` y `CAMION` son equivalentes, igual que `pingüino` y `PINGUINO`.
- Una misma letra escrita de dos formas internas (la `ó` como un solo carácter o como `o` + tilde) cuenta como la misma letra. También los signos que Unicode declara equivalentes a una letra: `Kelvin` escrito con el signo kelvin (U+212A) en lugar de la `K` es equivalente a `Kelvin` con la letra `K` (igual el signo ohmio, U+2126, con la letra griega `Ω` y el signo ångström, U+212B, con `Å`).
- Todo lo demás se compara tal cual: `Año` y `Ano` **no** son equivalentes (la ñ es otra letra); `Straße` y `STRASSE` tampoco (`ß` no equivale a `SS`); `À` y `à` tampoco (otras letras con marca, como `à`, `ç` u `ö`, no se igualan ni entre mayúscula y minúscula ni a la letra sin marca); los espacios internos cuentan (`Teclado  mecánico` ≠ `Teclado mecánico`).

Cambiar solo las mayúsculas, las tildes o los espacios de los extremos del **propio** nombre (`teclado` → `Teclado`, `Camion` → `Camión`) no es un cambio de nombre: se acepta sin comprobar repetidos (aunque otros productos se llamen igual) y se guarda el nombre enviado. Crear productos (`POST /products`) sigue permitiendo nombres repetidos.

**Limitaciones y desviaciones conocidas:**

- Un campo obligatorio enviado como `null` se rechaza con **422**, pero el error lo señala como tipo incorrecto, no como ausente.
- `NaN`, `Infinity`, `-Infinity` o `1e400` en un campo de la tabla (`name`, `description`, `price`, `stock` o `category_id`) dan **500** en lugar de 422 (como en `POST /products`), y el producto no se modifica. En un dato que no está en la tabla, el valor se ignora como cualquier otro dato no previsto y la respuesta puede ser **200** (o **500**); en ningún caso se guarda un valor no finito.
- Los ids enormes se garantizan hasta 4 000 cifras. A partir de unas 4 300 cifras, un número en el cuerpo hace que no se pueda leer y la respuesta es **400** `{"detail": "There was an error parsing the body"}`; en `product_id`, la respuesta es un **422** de formato en lugar del 404. El producto no cambia.
- Modificaciones simultáneas (no verificado): si llegan dos a la vez sobre el mismo producto, se aplican una detrás de otra y queda la última completa, nunca una mezcla. Dos productos distintos renombrados a la vez con nombres equivalentes pueden terminar ambos con éxito.
- Si la categoría nueva se borra justo durante la modificación, se espera el mismo 422 de categoría inexistente (no verificado).

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

Modificar un producto (ojo: **cambia de verdad** los datos guardados y no se puede deshacer; envía todos los campos, porque los que falten se pierden o dan error) desde PowerShell:

```powershell
Invoke-RestMethod -Method Put -Uri http://127.0.0.1:8000/products/1 -ContentType "application/json" -Body '{"name": "Smartphone", "price": 649.9, "stock": 10, "category_id": 2}'
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
