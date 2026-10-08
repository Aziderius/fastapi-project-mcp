# Plan técnico 001: Crear productos

**Spec:** `specs/001-crear-productos/spec.md` (v2) · **Fecha:** 2026-10-07 · **Estado:** pendiente de aprobación

**Dudas de la spec resueltas con el usuario antes de este plan:**
1. La spec de `specs/` y el README conviven: `specs/` contiene el diseño y la sección del README es el contrato público, que se escribe antes del código.
2. Solo se aceptan números reales: el texto, los booleanos y un stock `5.0` se rechazan.
3. Los datos no previstos se ignoran.
4. Si la base de datos no está disponible, se responde 500, como en el resto de operaciones.
5. Los caracteres invisibles o de control se aceptan sin tratamiento.
6. Que un alta fallida haga saltar un identificador es compatible con el principio 5.

## 1. Resumen técnico

Un nuevo `POST /products` en el router de productos recibe un schema `ProductCreate`, que valida y normaliza los datos (números estrictos, recorte de espacios y descripción vacía convertida en nula).

El endpoint comprueba que la categoría existe con `db.get` antes de insertar. Si `commit` falla por una clave foránea (código `23503`), responde con el mismo 422.

Después vuelve a consultar el producto con `joinedload(Product.category)` y `populate_existing=True`, y lo devuelve con 201 usando el `ProductRead` que ya existe. No cambian los modelos, la base de datos ni las dependencias.

## 2. Verificación de la constitución

| Principio | Cómo lo cumple este plan |
|---|---|
| 1. Stack mínimo | Solo se usa lo que ya está en `requirements.txt` (Pydantic, SQLAlchemy, FastAPI). No se añade ninguna dependencia. |
| 2. Spec antes que código | El **primer** cambio es la sección `POST /products` del README. El código se escribe después y debe coincidir con ella. |
| 3. Capas | El schema solo valida. El router hace HTTP y consultas. `models`, `database` y `core` no cambian. Las importaciones solo bajan: el router importa del schema y de los modelos. |
| 4. Verificación | Errores con `Invoke-RestMethod` contra el servidor real. Éxitos con `Invoke-RestMethod` contra un servidor de prueba cuya transacción se deshace al final. Comprobación en `/docs`. Sin pytest. |
| 5. Datos intactos | Sin cambios en el modelo ni en las tablas. Las pruebas no dejan filas, y se confirma al final con los recuentos (23 productos, 6 categorías). No se lee `.env`. |
| 6. Idioma | Los `detail` y los mensajes de validación propios van en español. Los identificadores van en inglés. Los mensajes automáticos de Pydantic siguen en inglés, como ya pasa en otros endpoints. |

**Choque con CLAUDE.md y con la skill, no con la constitución.** Las dos dicen "un recurso que no existe devuelve 404". La spec pide 422 para la categoría inexistente. Lo considero compatible: el recurso pedido es la colección de productos, que sí existe; lo que falla es un dato del cuerpo. Se aclarará en CLAUDE.md (sección 8).

## 3. Contrato de la API

**`POST /products`**. El cuerpo es un objeto JSON. Los datos no previstos (por ejemplo `id` o `created_at`) se ignoran. Si una clave aparece repetida, se usa el último valor.

| Dato | Tipo | Obligatorio | Validación |
|---|---|---|---|
| `name` | texto | sí | Se recortan los espacios en blanco de los extremos, también tabuladores, saltos de línea y espacios no separables. La longitud tras recortar debe estar entre 1 y 150. Se conservan mayúsculas, minúsculas y espacios internos. |
| `description` | texto o `null` | no | Se recorta igual que el nombre. Si queda vacía, se guarda como `null`. La longitud tras recortar es de 255 como máximo. |
| `price` | número | sí | Debe ser un número JSON, no texto ni booleano. Debe ser mayor que 0 y menor que 100 000 000, con 2 decimales significativos como máximo y finito. `19.900` y `1e2` son válidos. |
| `stock` | entero | sí | Debe ser un entero JSON, no texto, booleano ni `5.0`. Rango de 0 a 2 147 483 647. |
| `category_id` | entero | sí | Debe ser un entero JSON. Tiene que existir una categoría con ese id. |

**Éxito: 201 Created.** El cuerpo tiene la misma forma que `GET /products/{product_id}`:

```json
{"id": 24, "name": "Teclado", "description": null, "price": "49.90", "stock": 0, "category_id": 1, "category": {"id": 1, "name": "electronics"}, "created_at": "2026-10-07T18:00:00.000000"}
```

**Errores:**

| Código | Cuándo | Cuerpo |
|---|---|---|
| 422 | Falta un dato o es nulo, el tipo es incorrecto, está fuera de rango, la longitud no es válida, o el cuerpo falta, está mal formado o es una lista. | Formato estándar de FastAPI: `{"detail": [{"type", "loc", "msg", "input", ...}]}`, con todos los errores de formato juntos. Los mensajes automáticos van en inglés. El mensaje propio para el precio no numérico es `"El precio debe ser un número"`; Pydantic lo muestra como `"Value error, El precio debe ser un número"`. |
| 422 | Formato correcto, pero `category_id` no corresponde a ninguna categoría (incluidos 0, negativos y números enormes), o la categoría desaparece antes de completar el alta. | `{"detail": "No existe ninguna categoría con el id 999"}` |
| 500 | La base de datos no está disponible o hay un error inesperado. | Respuesta genérica del servidor, igual que el resto de operaciones. |

## 4. Cambios por archivo

1. **`README.md`** (primero, por el principio 2):
   - Una fila `POST /products` en la tabla de endpoints.
   - Una sección `POST /products` con el cuerpo, las validaciones, el 201 de ejemplo y los errores 422 de la tabla anterior.
   - Un ejemplo en "Probar desde la terminal".
2. **`app/schemas/product.py`:**
   - Una constante con el máximo de un INTEGER de PostgreSQL (2 147 483 647), con un comentario que explique de dónde sale. La usan el stock y la comprobación de la categoría.
   - Una clase nueva, `ProductCreate`:
     - **Nombre y descripción:** con recorte de espacios y límites de longitud.
     - **Descripción vacía tras recortar:** un validador posterior la convierte en `None`.
     - **Precio:** `Decimal` con límites (mayor que 0, menor que 100 000 000, 2 decimales). Un validador previo rechaza texto y booleanos con el mensaje en español.
     - **Stock y categoría:** enteros estrictos; el stock, con su rango.
   - Se actualiza el comentario de cabecera del archivo. `ProductRead` no cambia.
3. **`app/routers/products.py`:**
   - Nuevas importaciones: `Category`, `ProductCreate`, `IntegrityError` y `status`.
   - Una función pequeña que construye el `HTTPException` 422 de categoría inexistente, porque se usa en tres sitios.
   - Un endpoint `create_product` (`POST ""`, `status_code=201`, `response_model=ProductRead`) que, en este orden:
     1. Si el id de categoría está fuera del rango de un INTEGER, responde 422 sin consultar.
     2. Si `db.get(Category, id)` devuelve `None`, responde 422.
     3. Crea el producto con los datos del schema y lo añade a la sesión.
     4. Hace `commit`. Si da `IntegrityError`: `rollback`; si el código del error es `23503`, responde 422 de categoría inexistente; si no, relanza el error.
     5. Vuelve a consultar el producto con su categoría y lo devuelve.
   - Se actualiza el comentario de cabecera del archivo.
4. **Sin cambios:** `app/models/models.py`, `app/main.py` (el router ya está registrado), `app/database/`, `app/core/` y `requirements.txt`.
5. **`CLAUDE.md` y `MEMORY.md`:** ver la sección 8.

## 5. Decisiones técnicas

**D1. Detectar la categoría inexistente: comprobación previa y, como respaldo, el error de clave foránea.**
- **Por qué:** la comprobación con `db.get` da el caso normal con un mensaje claro y sin intentar insertar. El respaldo cubre la carrera de RF-7, en la que la categoría desaparece entre la comprobación y el `commit`.
- Para no confundir este caso con otros errores de integridad, se mira el código SQLSTATE del error original (`23503`, violación de clave foránea), que el adaptador de asyncpg en SQLAlchemy expone como `sqlstate`. Cualquier otro `IntegrityError` se relanza y acaba en 500, porque nunca debería ocurrir con datos ya validados.
- **Descartado:** fiarlo todo al error de clave foránea. Cada intento con una categoría inexistente consumiría un identificador, obligaría a interpretar el error en el caso normal y no daría el orden de RF-7. **Descartado también:** convertir cualquier `IntegrityError` en 422, porque ocultaría errores reales.

**D2. Devolver el producto con la categoría: volver a consultarlo con `db.get(Product, id, options=[joinedload(Product.category)], populate_existing=True)`.**
- **Por qué:**
  - `refresh` no carga las relaciones.
  - Con `lazy="raise"`, acceder a `category` sin cargarla falla.
  - **Comprobado:** sin `populate_existing`, `db.get` devuelve el objeto que ya está en la sesión, ignora el `joinedload` y la serialización falla con `InvalidRequestError`. Con `populate_existing=True` se hace un `SELECT` con `JOIN` sobre el mismo objeto y se cargan la categoría, el `id` y el `created_at`.
  - Además, el precio vuelve tal como lo guardó PostgreSQL, con 2 decimales (`1e2` → `"100.00"`). Con eso se cumplen RF-5 y RNF-1, y sobra el `refresh`.
- **Descartado:** asignar al producto la categoría obtenida en la comprobación previa y hacer `refresh`. `refresh` caducaría la relación, y el precio quedaría como `100.0` en lugar de `100.00`.

**D3. Ids fuera del rango de INTEGER: se tratan como inexistentes sin consultar.**
- **Por qué:** **comprobado** que `db.get(Category, 2147483648)` lanza `DBAPIError` (asyncpg rechaza el parámetro) y acabaría en 500. La spec pide "no existe" para cualquier entero.
- **Descartado:** validar el rango en el schema, porque daría un error de formato y no el mensaje "No existe…" que pide la spec.

**D4. Números estrictos con `StrictInt` y un validador previo para el precio.**
- **Por qué:** FastAPI valida el cuerpo en modo Python (después de `request.json()`). **Comprobado:** en modo estricto, un stock `5.0`, `"5"` o `true` se rechaza. El modo estricto de `Decimal` sigue aceptando el precio como texto, y por eso hace falta el validador.
- **Descartado:** `strict=True` en todo el modelo. En modo Python rechazaría el precio enviado como número decimal JSON, porque llega como `float`.

**D5. Validación con las restricciones de Pydantic (`StringConstraints`, `Field`).**
- **Por qué:** **comprobado** que el recorte elimina el espacio no separable y que la longitud se mide después de recortar. `NaN` e `Infinity` dan `finite_number` y `19.900` se convierte en `19.9`. Es el mismo estilo que `CategoryCreate`.
- **Descartado:** validar a mano en el endpoint, porque mezcla capas (principio 3).

**D6. Respuesta 201 con `ProductRead`.**
- **Por qué:** RF-9 y RNF-1 piden la misma forma que la consulta individual.
- **Descartado:** un schema nuevo de respuesta, porque duplicaría `ProductRead`.

## 6. Trazabilidad

| RF | Archivos | Pruebas (sección 7) |
|---|---|---|
| RF-1 Alta, id, fecha, visibilidad | `routers/products.py` | S1, S11, S12 |
| RF-2 Datos de entrada, ausentes, cuerpo | `schemas/product.py` (FastAPI para el cuerpo) | E1, E2, E20 a E22, S9, S10 |
| RF-3 Nombre | `schemas/product.py` | S2, S7, S8, E3 a E5 |
| RF-4 Descripción | `schemas/product.py` | S3, S4, E6 |
| RF-5 Precio | `schemas/product.py`, más la reconsulta en `routers/products.py` | S5, S6, E7 a E10 |
| RF-6 Stock | `schemas/product.py` | S1, E11 a E13 |
| RF-7 Categoría y carrera | `routers/products.py`, `schemas/product.py` (tipo) | E14 a E18, F1 |
| RF-8 Nombres repetidos | `routers/products.py` (sin restricción) | S8 |
| RF-9 Forma de la respuesta | `routers/products.py` (`response_model=ProductRead`) | S1, S11 |
| RF-10 Sin efectos parciales | `routers/products.py` (`rollback`) | F1, R3 |
| RNF-1 a RNF-5 | todos los anteriores | S11, R1, R2, R3 |

## 7. Plan de verificación

**Preparación.** Servidores de prueba en los puertos 8001 y 8002, porque el del usuario usa el 8000. Esta función de PowerShell envía un JSON literal y muestra el código y el cuerpo:

```powershell
function Send-Product([string]$json, [int]$port = 8001) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($json)
  try {
    $r = Invoke-WebRequest -Method Post -Uri "http://127.0.0.1:$port/products" -ContentType "application/json; charset=utf-8" -Body $bytes -UseBasicParsing
    "$($r.StatusCode) -> $($r.Content)"
  } catch {
    "$([int]$_.Exception.Response.StatusCode) -> $($_.ErrorDetails.Message)"
  }
}
$ok = '"price": 10, "stock": 1, "category_id": 1'
```

Uso `Invoke-WebRequest` (de la misma familia que `Invoke-RestMethod`, viene con PowerShell) solo para poder leer el código 201. En Windows PowerShell 5.1, `Invoke-RestMethod` no lo expone.

**Errores (E), contra el servidor real en el 8001.** No guardan nada. Todos deben dar 422.

| Id | Comando | Esperado |
|---|---|---|
| E1 | `Send-Product '{"price": 10, "stock": 1, "category_id": 1}'` | `name` ausente |
| E2 | `Send-Product "{`"name`": null, $ok}"` | `name` ausente o nulo |
| E3 | `Send-Product "{`"name`": `"   `", $ok}"` | `string_too_short` |
| E4 | `Send-Product "{`"name`": `"$('a'*151)`", $ok}"` | `string_too_long` |
| E5 | `Send-Product "{`"name`": 123, $ok}"` | `string_type` |
| E6 | `Send-Product "{`"name`": `"X`", `"description`": `"$('d'*256)`", $ok}"` | `string_too_long` |
| E7 | `Send-Product '{"name": "X", "price": 0, "stock": 1, "category_id": 1}'`, y lo mismo con `-0`, `-5` y `100000000` | `greater_than` / `less_than` |
| E8 | Lo mismo con `"price": 0.001` y `"price": 19.999` | `decimal_max_places` |
| E9 | Lo mismo con `"price": "19.90"` y `"price": true` | `Value error, El precio debe ser un número` |
| E10 | Lo mismo con `"price": NaN` y `"price": Infinity` | `finite_number` |
| E11 | `Send-Product '{"name": "X", "price": 10, "stock": -1, "category_id": 1}'`, y lo mismo con `2147483648` | `greater_than_equal` / `less_than_equal` |
| E12 | Lo mismo con `"stock": 1.5` y `"stock": 5.0` | `int_type` |
| E13 | Lo mismo con `"stock": "5"` y `"stock": true` | `int_type` |
| E14 | `Send-Product '{"name": "X", "price": 10, "stock": 1, "category_id": 1.5}'`, y lo mismo con `null` y `"1"` | `int_type` o ausente |
| E15 | Lo mismo con `"category_id": 999` | `{"detail": "No existe ninguna categoría con el id 999"}` |
| E16 | Lo mismo con `0` y `-3` | El mismo mensaje con 0 y -3 |
| E17 | Lo mismo con `2147483648` y `100000000000000000000` | El mismo mensaje, y **no** 500 |
| E18 | `Send-Product '{"name": "X", "price": 0, "stock": 1, "category_id": 999}'` | Solo el error del precio |
| E19 | `Send-Product '{"name": "X", "price": 0, "stock": -1, "category_id": 1}'` | Errores de precio **y** de stock juntos |
| E20 | `Send-Product ''` | Cuerpo ausente |
| E21 | `Send-Product '{"name": "X",'` | `json_invalid` |
| E22 | `Send-Product '[1, 2]'` | `model_attributes_type` (no es un objeto) |

**Éxitos (S), contra un servidor de prueba en el 8002 cuya transacción se deshace al final** (principio 4). Es un script temporal fuera del repositorio:
- Arranca la app con `uvicorn`.
- Sustituye `get_db` mediante `app.dependency_overrides` por sesiones unidas a una única conexión con una transacción externa (`join_transaction_mode="create_savepoint"`).
- Al detenerse, hace `rollback`.

Todos los casos deben dar 201:

| Id | Comando | Esperado |
|---|---|---|
| S1 | `Send-Product '{"name": "Teclado", "price": 49.9, "stock": 0, "category_id": 1}' 8002` | `"price": "49.90"`, `stock` 0, `"category": {"id": 1, "name": "electronics"}`, `description` null, con `id` y `created_at` |
| S2 | `Send-Product "{`"name`": `"\t  Teclado  \n`", $ok}" 8002` | `"name": "Teclado"` |
| S3 | `Send-Product "{`"name`": `"X`", `"description`": `"   `", $ok}" 8002` | `"description": null` |
| S4 | `Send-Product "{`"name`": `"X`", `"description`": `"  hola  `", $ok}" 8002`, y con 300 espacios | `"hola"` / `null` |
| S5 | `Send-Product '{"name": "X", "price": 0.01, "stock": 1, "category_id": 1}' 8002`, y con `99999999.99` | `"0.01"` / `"99999999.99"` |
| S6 | Lo mismo con `"price": 19.900` y `"price": 1e2` | `"19.90"` / `"100.00"` |
| S7 | `Send-Product "{`"name`": `"  $('a'*150)  `", $ok}" 8002`, y el nombre `"Teclado 🎹"` | Se crean (150 caracteres; el emoji cuenta como uno) |
| S8 | Enviar S1 dos veces | Dos `id` distintos (nombres repetidos permitidos) |
| S9 | `Send-Product '{"id": 5, "created_at": "2000-01-01", "name": "X", "price": 10, "stock": 1, "category_id": 1}' 8002` | `id` y `created_at` asignados por el sistema |
| S10 | `Send-Product '{"name": "A", "name": "B", "price": 10, "stock": 1, "category_id": 1}' 8002` | `"name": "B"` |
| S11 | `Invoke-RestMethod http://127.0.0.1:8002/products/<id de S1>` | Idéntico a la respuesta de S1 |
| S12 | `(Invoke-RestMethod http://127.0.0.1:8002/products).id` | Incluye los nuevos ids al final, en orden |

**Fallo concurrente (F), con un script en una transacción que se deshace:**
- **F1:** se simula que `db.get(Category, …)` encuentra una categoría con id 999999, que no existe en la base de datos. El `commit` falla con `23503` y la respuesta debe ser 422 con el mensaje de categoría inexistente, sin crear el producto.

**Regresión y cierre (R):**
- **R1:** el servidor arranca sin errores. `/docs` y `/openapi.json` muestran `POST /products` con el cuerpo `ProductCreate` y la respuesta 201 `ProductRead`.
- **R2:**
  - Las 11 respuestas de referencia guardadas antes de la migración a async siguen idénticas byte a byte: `/hello-world`, `/healthz`, categorías, productos, 404, 409 y 422.
  - Además se ejecuta `Invoke-RestMethod http://127.0.0.1:8001/healthz`.
  - Y `Send-Product "{`"name`": `"X`", $ok}"` con un servidor arrancado con `DB_PORT=1` solo para ese proceso, que debe dar 500.
- **R3:** después de detener el servidor del 8002, las consultas de solo lectura devuelven 23 productos y 6 categorías. No queda ningún dato de prueba.
- **R4:** se repiten R1, E15, E17 y S1 con Python 3.12, en el entorno de pruebas fuera del proyecto.

## 8. Riesgos y documentación

**Qué podría romperse:**
- **Rutas de `/products`:** se añade `POST ""` junto a `GET ""` y `GET /{product_id}`. No hay conflicto entre ellas. R2 comprueba que los GET siguen igual.
- **Dos formatos de 422:** el cuerpo de un 422 puede ser una lista (errores de formato de FastAPI) o un texto (categoría inexistente). Los clientes deben aceptar los dos, igual que hoy aceptan el 404 y el 409 con texto.
- **Identificadores que se saltan:** cada alta que falla en el `commit`, y cada prueba deshecha, consume un identificador. Está aceptado (duda 6).
- **`IntegrityError` distintos de `23503`:** dan 500. Con los datos ya validados no deberían ocurrir.

**Defecto existente fuera de este cambio.** Desde la migración a async, `GET /categories/{id}` y `GET /products/{id}` con un id mayor que 2 147 483 647 responden **500** en lugar de **404**, porque asyncpg rechaza el parámetro. Lo he comprobado con `db.get`. El README promete 404, así que según el principio 2 es un defecto. Este plan no lo corrige porque la spec 001 no lo pide. Hay que decidir si se trata aparte.

**[REVISAR SPEC]:**
1. La sección 9 de la spec sigue mostrando como abiertas las 6 dudas que ya están resueltas. Faltan en la spec:
   - Los datos no previstos se ignoran.
   - Se rechazan el texto, los booleanos y el `5.0`.
   - Error 500 si la base de datos no responde.
   - Se aceptan los caracteres invisibles.
2. La definición de "error de datos inválidos" de la spec dice que indica "cada dato incorrecto". El error de categoría inexistente es un mensaje único en español que no señala el campo de forma estructurada (aunque incluye el id).
3. La spec no menciona el mensaje propio del precio no numérico. Al ser un mensaje que escribe el proyecto, va en español por el principio 6, y aparece mezclado con el prefijo inglés `Value error,` de Pydantic.

**Documentación que hay que actualizar:**
- **README.md:** fila y sección `POST /products` **antes del código**, y un ejemplo con `curl`. La sección "Estructura del proyecto" sigue desactualizada, y está fuera de alcance.
- **CLAUDE.md:**
  - `products.py` con `POST /products`, y `product.py` con `ProductCreate`.
  - Aclarar los papeles: `specs/NNN-*/` contiene el diseño (spec y plan) y la sección del README es el contrato público, que se escribe antes del código.
  - Matizar la regla de códigos: "un recurso de la ruta que no existe → 404; un id del cuerpo que no existe → 422".
  - Añadir la trampa de `populate_existing=True` al volver a consultar un objeto que ya está en la sesión.
- **MEMORY.md:**
  - Estado: `POST /products` implementado y verificado.
  - Decisiones D1 a D4, con su porqué.
  - Aprendizajes: el `db.get` de asyncpg con ids fuera de rango y el modo estricto de `Decimal`.
  - Próximos pasos: el defecto de ids enormes en los GET.
