# Plan técnico 002: Editar productos

**Spec:** `specs/002-editar-productos/spec.md` (aprobada el 2026-10-08; dudas 17 y 18 resueltas el mismo día) · **Fecha:** 2026-10-08 · **Estado:** aprobado por el usuario el 2026-10-08

## 1. Resumen técnico

Un nuevo `PUT /products/{product_id}` en el router de productos recibe un schema `ProductUpdate`, que hereda sin cambios todas las validaciones de `ProductCreate`, y responde 200 con el `ProductRead` que ya existe.

El endpoint comprueba, en este orden: producto (404, bloqueando la fila con `SELECT ... FOR UPDATE`), categoría (422, con el mismo respaldo por `IntegrityError` 23503 que el `POST`) y, solo si el nombre cambia, nombre repetido (409, comparando en Python con una función de la biblioteca estándar: `unicodedata` NFC más una tabla de equivalencias del alfabeto español).

Los ids fuera del rango de INTEGER se tratan como inexistentes sin consultar, también en `GET /products/{product_id}` (RF-10). Tras el `commit`, el producto se vuelve a consultar con `joinedload` y `populate_existing=True`. No cambian los modelos, la base de datos ni las dependencias.

## 2. Verificación de la constitución

| Principio | Cómo lo cumple este plan |
|---|---|
| 1. Stack mínimo | Solo FastAPI, Pydantic, SQLAlchemy y la biblioteca estándar (`unicodedata`, `str.translate`). Ninguna dependencia ni extensión de PostgreSQL nueva. |
| 2. Spec antes que código | El **primer** cambio es el README: sección `PUT /products/{product_id}` y corrección de `GET /products/{product_id}`. El código se escribe después y debe coincidir. |
| 3. Capas | El schema valida y define la clave de comparación de nombres (normalización de datos); el router hace HTTP y consultas. `models`, `database`, `core` y `main.py` no cambian. Las importaciones solo bajan. |
| 4. Verificación | Errores de formato con `curl.exe -i` contra el servidor del usuario (8000); casos que llegan a la base de datos, primero en un servidor de prueba (8002) cuya transacción se deshace. `/docs`. Sin pytest. |
| 5. Datos intactos | Sin ALTER, `create_all` ni migraciones. Los datos de preparación (productos y una categoría temporal) se crean dentro de la transacción que se deshace; al final se comparan recuentos (24/6) y el listado completo con una instantánea previa. |
| 6. Idioma | Los `detail` propios en español; los mensajes automáticos de FastAPI/Pydantic siguen en inglés (RNF-3). Identificadores en inglés. |

## 3. Contrato de la API

### `PUT /products/{product_id}`

**Ruta.** `product_id` es un entero, interpretado igual que en `GET /products/{product_id}` (mismo tipo `int` en la ruta: `05` → 5, `-0` → 0, `1.0` → 1, `5_0` → 50, ` 5 ` → 5).

**Cuerpo.** Objeto JSON, sustitución completa. Mismas reglas que `POST /products`:

| Dato | Tipo | Obligatorio | Validación |
|---|---|---|---|
| `name` | texto | sí | Recorte de espacios en blanco de los extremos; 1 a 150 caracteres tras recortar. Se guarda tal cual (mayúsculas y tildes incluidas). |
| `description` | texto o `null` | no | Recorte igual; vacía, `null` o ausente → se guarda `null` (aunque antes tuviera descripción). Máximo 255. |
| `price` | número | sí | No texto ni booleano. > 0, < 100 000 000, 2 decimales significativos como máximo. |
| `stock` | entero | sí | No texto, booleano ni `5.0`. De 0 a 2 147 483 647. |
| `category_id` | entero | sí | Entero JSON. Debe existir la categoría. |

Los datos no previstos (`id`, `created_at`, `category`, …) se ignoran sea cual sea su valor. Clave repetida → último valor.

**Éxito: 200 OK** con el producto completo, misma forma que `GET /products/{product_id}` (categoría nueva si ha cambiado, `id` y `created_at` originales):

```json
{"id": 1, "name": "Smartphone", "description": null, "price": "649.90", "stock": 10, "category_id": 2, "category": {"id": 2, "name": "books"}, "created_at": "2026-10-06T13:28:21.054510"}
```

**Errores, en orden de prioridad (RF-11):**

| Orden | Código | Cuándo | Cuerpo |
|---|---|---|---|
| 1 | 422 | Cuerpo JSON mal formado. | Solo `json_invalid` (FastAPI lo lanza antes de validar la ruta). |
| 2 | 422 | `product_id` no es entero y/o algún dato del cuerpo tiene formato inválido, o el cuerpo falta o no es un objeto. | Lista estándar de FastAPI con **todos** los errores de ruta y cuerpo juntos. Precio no numérico: `"Value error, El precio debe ser un número"`. |
| 3 | 404 | Producto inexistente (incluidos 0, negativos y fuera de rango de INTEGER). | `{"detail": "No existe ningún producto con el id 999"}` |
| 4 | 422 | Categoría inexistente (incluidos 0, negativos, fuera de rango) o borrada antes del `commit`. | `{"detail": "No existe ninguna categoría con el id 999"}` |
| 5 | 409 | El nombre cambia y es equivalente al de otro producto. | `{"detail": "Ya existe otro producto con el nombre TECLADO"}` (nombre recibido ya recortado) |
| — | 500 | Base de datos no disponible o error inesperado. | Respuesta genérica. |

Desviaciones heredadas (spec, "Desviaciones conocidas aceptadas"): `NaN`/`Infinity`/`1e400` en cualquier dato del cuerpo → posible 500 sin cambios; número de más de ~4 300 cifras en el cuerpo → 400 `There was an error parsing the body`; en la ruta → 422 de formato; nulo en obligatorio → error de tipo.

### `GET /products/{product_id}` (corrección RF-10)

Igual que hoy, salvo que un id fuera del rango de INTEGER (`99999999999999999999`, `-99999999999999999999`) responde 404 `No existe ningún producto con el id {id}` en lugar de 500.

## 4. Cambios por archivo

1. **`README.md`** (primero, principio 2):
   - Fila `PUT /products/{product_id}` en la tabla de endpoints.
   - Sección `PUT /products/{product_id}` con el contrato de la sección 3: sustitución completa, tabla de campos (remitiendo a la de `POST /products`), 200 de ejemplo, errores en su orden, regla de nombres equivalentes con ejemplos (`Camión`/`CAMION` duplicado; `Año`/`Ano`, `Straße`/`STRASSE`, `À`/`à` distintos), que cambiar solo mayúsculas o tildes del propio nombre no es un cambio, y las limitaciones conocidas (`NaN`, números de más de 4 000 cifras, simultaneidad).
   - En `GET /products/{product_id}`: "Si no existe (incluidos ids enormes) → 404".
   - Ejemplo de `PUT` en "Probar desde la terminal", con el aviso de que modifica datos reales.
2. **`app/schemas/product.py`:**
   - Constante `MIN_INTEGER` (−2 147 483 648) junto a `MAX_INTEGER`, con comentario.
   - Clase `ProductUpdate`, subclase de `ProductCreate` sin campos ni validadores nuevos, con un docstring que explique que la modificación valida exactamente igual que la creación.
   - Una tabla de traducción del alfabeto español construida con `str.maketrans` (A–Z → a–z; Á É Í Ó Ú Ü y á é í ó ú ü → vocal sin marca en minúscula; Ñ → ñ), con un comentario que liste lo que **no** se iguala (`ß`, `à`, `ç`, `ö`, mayúsculas de otras letras).
   - Una función `product_name_key(name)` que devuelve la clave de comparación: recorta los extremos con `strip()`, normaliza a NFC con `unicodedata.normalize` y aplica la tabla con `translate`. Docstring con ejemplos.
   - Se actualiza el comentario de cabecera.
3. **`app/routers/products.py`:**
   - Nuevas importaciones: `ProductUpdate`, `product_name_key`, `MIN_INTEGER`.
   - Función pequeña `fits_in_integer(value)` que dice si un id cabe en INTEGER. La usan `get_product`, `update_product` (producto y categoría) y `create_product` (sustituye su comprobación en línea; mismo resultado observable).
   - Función pequeña `product_not_found(product_id)` que construye el 404 (la usan `get_product` y `update_product`).
   - `get_product`: si el id no cabe en INTEGER, 404 sin consultar (RF-10). El resto no cambia.
   - Nuevo endpoint `update_product` (`PUT "/{product_id}"`, `response_model=ProductRead`, 200 por defecto) que, en este orden:
     1. Si `product_id` no cabe en INTEGER → 404.
     2. `db.get(Product, product_id, with_for_update=True)` (sin `joinedload`); si es `None` → 404.
     3. Si `category_id` no cabe en INTEGER o `db.get(Category, …)` es `None` → 422 (`category_not_found`, ya existe).
     4. Si `product_name_key(nombre recibido) != product_name_key(nombre guardado)`: consulta los nombres de los demás productos (`select(Product.name).where(Product.id != product_id)`) y, si alguno tiene la misma clave → 409.
     5. Asigna los cinco datos editables desde el schema (descripción ausente → `None`).
     6. `commit`. Si `IntegrityError`: `rollback`; si `sqlstate == "23503"` → 422 de categoría; si no, relanza (500).
     7. Vuelve a consultar con `joinedload(Product.category)` y `populate_existing=True` y lo devuelve.
   - Comentario de cabecera: "listar, consultar uno, crear y modificar".
4. **Sin cambios:** `app/models/models.py`, `app/main.py` (el router ya está registrado), `app/routers/health.py`, `app/routers/categories.py`, `app/schemas/category.py`, `app/database/`, `app/core/`, `requirements.txt`.
5. **`CLAUDE.md`, `MEMORY.md`, spec 001:** ver la sección 8 (no se cambian en este plan).

## 5. Decisiones técnicas

**D1. Schema `ProductUpdate` como subclase vacía de `ProductCreate`.**
- **Por qué:** RNF-1 exige validaciones y mensajes idénticos; heredar garantiza que no diverjan (Pydantic v2 hereda los `field_validator`). En `/docs` el cuerpo aparece como `ProductUpdate`, más claro para quien aprende.
- **Descartado:** reutilizar `ProductCreate` tal cual (funciona igual, pero `/docs` mostraría "ProductCreate" como cuerpo de un `PUT`); y una base común `ProductBase` (reestructura un schema ya verificado sin necesidad).

**D2. Clave de comparación de nombres en Python con la biblioteca estándar: `strip()` + `unicodedata.normalize("NFC")` + `str.translate` con una tabla explícita del alfabeto español.**
- **Por qué:** cumple exactamente la definición aprobada. NFC une las dos formas internas de una letra (`o` + tilde combinante → `ó`; `n` + virgulilla combinante → `ñ`) y, como acepta la spec (duda 18), convierte el signo kelvin en `K`, el ohmio en `Ω` y el ångström en `Å`; el comentario de la función lo indica. La tabla explícita solo iguala lo que pide la spec: mayúsculas de A–Z, Ñ y vocales con tilde o ü, y quita la tilde y la diéresis de á é í ó ú ü. Todo lo demás se compara tal cual: `ß` ≠ `ss`, `À` ≠ `à`, `ö` ≠ `o`, letras de ancho completo y de otros alfabetos distintas. Un carácter siempre da un carácter, así que no aparecen equivalencias "una letra = varias".
- **Descartado:** `str.lower()`/`casefold()` (igualan `À`/`à`, y `casefold` convierte `ß` en `ss`), `NFKC` (igualaría ancho completo y ligaduras) y quitar todas las marcas con `NFD` (igualaría `ñ`/`n` y `ç`/`c`).

**D3. Comparación en Python sobre los nombres de los demás productos, solo cuando el nombre cambia.**
- **Por qué:** una sola definición de equivalencia, legible y comprobable, sin depender de la versión de PostgreSQL ni de la codificación de la base de datos. Se leen solo los nombres (no los productos completos) y solo si hay cambio de nombre. Con 24 productos el coste es despreciable.
- **Descartado:** comparar en SQL con `normalize(...)` y `translate(...)` (sin extensiones). Duplicaría la regla en dos lenguajes, `btrim` no recorta los mismos espacios en blanco que `str.strip()` y `normalize` depende de la versión y de que la base de datos sea UTF-8. También descartado `unaccent` (extensión no instalada) y un UNIQUE o índice (alteraría tablas y no se permiten repetidos al crear).

**D4. Bloquear la fila del producto con `db.get(Product, id, with_for_update=True)`.**
- **Por qué (RF-8):** el ORM solo envía en el `UPDATE` las columnas que cambian respecto a lo que leyó. Sin bloqueo, dos modificaciones simultáneas que leen el mismo estado podrían escribir columnas distintas y dejar una mezcla. Con `FOR UPDATE`, la segunda espera a que termine la primera y lee sus valores, así que su `UPDATE` deja todos los datos de la última. El bloqueo dura solo hasta el `commit` o el cierre de la sesión.
- Sin `joinedload` en esta lectura: en PostgreSQL, `FOR UPDATE` no se puede aplicar al lado opcional de un `LEFT OUTER JOIN` (que es el que usa `joinedload` por defecto), y la categoría no hace falta hasta la respuesta (se carga en la reconsulta, D6). **A comprobar en la implementación:** que la combinación falla y que la lectura sin `joinedload` funciona.
- **Descartado:** un `update()` explícito con las cinco columnas sin bloqueo (evita la mezcla, pero el orden de errores obliga a leer antes el producto igualmente y complica el código para quien aprende); y versiones o `ETag` (fuera de alcance).

**D5. Categoría inexistente: comprobación previa y respaldo por `IntegrityError` 23503 (igual que el `POST`).**
- **Por qué:** mismo mensaje y mismo comportamiento que la spec 001; el respaldo cubre el borrado entre la comprobación y el `commit` (RF-4, limitación no verificada). Otros `IntegrityError` se relanzan → 500. La clave foránea es NO ACTION, así que la categoría **actual** no puede borrarse mientras el producto le pertenezca.
- **Descartado:** convertir cualquier `IntegrityError` en 422 (ocultaría errores reales).

**D6. Respuesta: reconsulta con `db.get(..., options=[joinedload(Product.category)], populate_existing=True)`.**
- **Por qué:** `refresh` no carga relaciones y `lazy="raise"` falla si la categoría no está cargada; sin `populate_existing`, `db.get` devuelve el objeto de la sesión e ignora el `joinedload`. Además el precio vuelve con 2 decimales tal como lo guarda PostgreSQL (`1e2` → `"100.00"`) y, si la categoría ha cambiado, la relación se carga con la nueva.
- **Descartado:** asignar a mano `product.category` con la categoría consultada (el precio quedaría sin normalizar y se dependería del estado de la sesión).

**D7. Ids fuera de rango de INTEGER: función `fits_in_integer` con los límites exactos (−2 147 483 648 a 2 147 483 647), usada en `GET`, `PUT` y `POST`.**
- **Por qué:** asyncpg lanza `DBAPIError` (500) con ids fuera de rango; un id fuera de rango no puede existir, así que se responde "no existe" sin consultar (RF-5, RF-10, RF-4). La comprobación ya aparecía en el `POST`; con tres usos, la skill pide extraerla en lugar de repetirla. Con los límites exactos, `-2147483648` también se consulta (antes se descartaba sin consultar en el `POST`; la respuesta es la misma, 422, porque no existe esa categoría).
- **Descartado:** repetir la comprobación en línea en cada endpoint; y validar el rango en el schema o con `Path(ge=..., le=...)` (daría 422 de formato en lugar del 404/422 "No existe…").

**D8. Orden de errores: se apoya en el comportamiento de FastAPI para los dos primeros niveles.**
- **Por qué:** FastAPI intenta leer el JSON antes de validar nada y, si está mal formado, responde solo con `json_invalid` (RF-11, primer punto). Después valida ruta y cuerpo juntos y devuelve todos los errores en una lista (segundo punto). El endpoint añade 404 → 422 → 409 en ese orden. **A comprobar en la implementación** con los casos E20 a E24.
- **Descartado:** validar la ruta o el cuerpo a mano dentro del endpoint (duplica lo que ya hace FastAPI y mezcla capas).

**D9. Sustitución de datos asignando atributo a atributo desde el schema.**
- **Por qué:** explícito y legible; la descripción ausente llega como `None` desde el schema, así que se borra (RF-2). Si los datos coinciden con los guardados, el ORM no envía `UPDATE` y la respuesta es la misma (RF-7).
- **Descartado:** un bucle sobre `model_dump()` con `setattr` (más corto, menos claro para quien aprende).

## 6. Trazabilidad

| RF | Archivos | Pruebas (sección 7) |
|---|---|---|
| RF-1 Modificación, visibilidad, posición | `routers/products.py` | S1, S2, S3 |
| RF-2 Datos de entrada, descripción nula, cuerpo, repetidos | `schemas/product.py` (`ProductUpdate`), FastAPI | E1 a E3, E21, E22, S4, S5, S12 |
| RF-3 Validaciones idénticas, precio exacto | `schemas/product.py` (herencia) | E4 a E13, S6, S7 |
| RF-4 Cambio de categoría, inexistente, borrada | `routers/products.py`, `schemas/product.py` (tipo) | S1, E14, E15, V1 a V3, V5 |
| RF-5 Producto inexistente, formas del id | `routers/products.py` (`fits_in_integer`, ruta `int`) | E16 a E19, V4, L1, L2 |
| RF-6 Datos fijos y no previstos | `schemas/product.py` (Pydantic ignora extras) | S1, S8, S9 |
| RF-7 Respuesta, sin cambios, datos no conformes | `routers/products.py` (reconsulta) | S1, S10, S11 |
| RF-8 Simultáneas | `routers/products.py` (`with_for_update`) | No verificado (limitación conocida); revisión de código |
| RF-9 Sin efectos parciales | `routers/products.py` (errores antes del `commit`, `rollback`) | Instantánea C1 a C3, V1 a V5 |
| RF-10 GET con ids enormes | `routers/products.py` (`get_product`) | G1 a G3 |
| RF-11 Orden de errores | FastAPI + orden del endpoint | E20, E23, E24, V4, V5, N12 |
| RF-12 Nombres repetidos | `schemas/product.py` (`product_name_key`), `routers/products.py` | N1 a N13 |
| RF-13 Base de datos caída | sin código propio (500 por defecto) | B1 |
| RNF-1 a RNF-5 | todos los anteriores | R1 a R5, C1 a C3 |

## 7. Plan de verificación

### Preparación (PowerShell, servidor del usuario en el 8000)

Función que escribe el cuerpo en un archivo temporal (así PowerShell 5.1 no altera las comillas) y lo envía con `curl.exe -i`:

```powershell
function Put-Product([string]$id, [string]$json, [int]$port = 8000) {
  $f = Join-Path $env:TEMP "spec002-body.json"
  [IO.File]::WriteAllText($f, $json)   # UTF-8 sin BOM
  curl.exe -s -i -X PUT "http://127.0.0.1:$port/products/$id" -H "Content-Type: application/json" --data-binary "@$f"
}
$ok = '"price": 10, "stock": 1, "category_id": 1'
```

**Instantánea previa (C1), solo lectura:**

```powershell
curl.exe -s http://127.0.0.1:8000/products -o "$env:TEMP\spec002-antes.json"
```

**Regla de seguridad:** todos los casos de esta sección contra el 8000 fallan antes del `commit`. Los errores de formato usan el producto `999999` (no existe y además el error de formato va primero). Los casos 404, 422 de categoría y 409 con producto existente se ejecutan **primero** en el servidor de prueba 8002 (V1 a V5) y solo si pasan se repiten en el 8000.

### Errores de formato (E), contra el 8000 — todos 422

| Id | Comando | Esperado |
|---|---|---|
| E1 | `Put-Product 999999 '{"price": 10, "stock": 1, "category_id": 1}'` | `name` ausente (`missing`) |
| E2 | `Put-Product 999999 '{"name": "X", "stock": 1, "category_id": 1}'` y lo mismo sin `stock` y sin `category_id` | `missing` del dato que falta |
| E3 | `Put-Product 999999 "{`"name`": null, $ok}"` | error de tipo (desviación aceptada) |
| E4 | `Put-Product 999999 "{`"name`": `"   `", $ok}"` | `string_too_short` |
| E5 | `Put-Product 999999 "{`"name`": `"$('a'*151)`", $ok}"` | `string_too_long` |
| E6 | `Put-Product 999999 "{`"name`": 123, $ok}"` | `string_type` |
| E7 | `Put-Product 999999 "{`"name`": `"X`", `"description`": `"$('d'*256)`", $ok}"` | `string_too_long` |
| E8 | `Put-Product 999999 '{"name": "X", "price": 0, "stock": 1, "category_id": 1}'`, y con `-0`, `-5`, `100000000` | `greater_than` / `less_than` |
| E9 | Lo mismo con `"price": 0.001` | `decimal_max_places` |
| E10 | Lo mismo con `"price": "19.90"` y `"price": true` | `Value error, El precio debe ser un número` |
| E11 | `Put-Product 999999 '{"name": "X", "price": 10, "stock": -1, "category_id": 1}'`, y con `2147483648` | `greater_than_equal` / `less_than_equal` |
| E12 | Lo mismo con `"stock": 1.5`, `5.0`, `"5"` y `true` | `int_type` |
| E13 | Precio inválido **y** stock inválido: `'{"name": "X", "price": 0, "stock": -1, "category_id": 1}'` | Ambos errores en la misma lista |
| E14 | `'{"name": "X", "price": 10, "stock": 1, "category_id": 1.5}'`, y con `"2"`, `true`, `false`, `null` | `int_type` (o tipo para `null`) |
| E15 | Precio inválido **y** categoría inexistente: `'{"name": "X", "price": 0, "stock": 1, "category_id": 999}'` | Solo el error del precio |
| E16 | `Put-Product abc "{`"name`": `"X`", $ok}"` y `Put-Product 1.5 ...` | `int_parsing` en `["path", "product_id"]` |
| E17 | `Put-Product abc '{"name": "X", "price": -5, "stock": 1, "category_id": 1}'` | Errores de ruta **y** de precio juntos (RF-11) |
| E18 | `Put-Product 999 '{"name": "X", "price": -5, "stock": 1, "category_id": 1}'` | Solo el error del precio, sin 404 |
| E19 | `Put-Product ('9'*4400) "{`"name`": `"X`", $ok}"` | 422 de formato (desviación: más de ~4 300 cifras) |
| E20 | `Put-Product abc '{"price": 500,00}'` | Solo `json_invalid`, sin el error de la ruta |
| E21 | `curl.exe -s -i -X PUT http://127.0.0.1:8000/products/999999 -H "Content-Type: application/json"` (sin cuerpo) | `missing` del cuerpo |
| E22 | `Put-Product 999999 '[1, 2]'` y `Put-Product 999999 '"texto"'` | `model_attributes_type` |
| E23 | `Put-Product 999999 "{`"name`": `"X`", `"price`": NaN, `"stock`": 1, `"category_id`": 1}"`, y con `Infinity` y `1e400` en precio, stock, categoría, nombre y descripción | 422 o 500 (desviación); C3 confirma que nada cambia |
| E24 | `Put-Product 999999 "{`"name`": `"X`", `"price`": 10, `"stock`": 1, `"category_id`": $('9'*4400)}"` | 400 `There was an error parsing the body` (desviación) |

### No encontrado (L), contra el 8000 tras pasar V4 — todos 404, sin escribir

| Id | Comando | Esperado |
|---|---|---|
| L1 | `Put-Product 999 "{`"name`": `"X`", $ok}"`, y con `0`, `-1`, `99999999999999999999`, `-99999999999999999999`, `('9'*4000)` | `No existe ningún producto con el id {id}` (el número interpretado), nunca 500 |
| L2 | `Put-Product 0999 ...`, `Put-Product -0 ...`, `Put-Product 999.0 ...`, `Put-Product 9_99 ...`, `Put-Product "%20999%20" ...` | 404 con `id 999`, `id 0`, `id 999`, `id 999`, `id 999`; las mismas rutas con `curl.exe -i http://127.0.0.1:8000/products/<forma>` dan el mismo id (RF-5, tercer punto) |

### Consulta individual corregida (G), contra el 8000

| Id | Comando | Esperado |
|---|---|---|
| G1 | `curl.exe -i http://127.0.0.1:8000/products/99999999999999999999` | 404 `No existe ningún producto con el id 99999999999999999999` |
| G2 | `curl.exe -i http://127.0.0.1:8000/products/-99999999999999999999` y `/products/2147483648` | 404 con el id correspondiente |
| G3 | `curl.exe -i http://127.0.0.1:8000/products/1`, `/products/999`, `/products/abc`, `/products/05` | Igual que antes: 200, 404, 422, 200 del producto 5 |

### Casos que llegan a la base de datos (S, V, N), en el servidor de prueba 8002 con transacción deshecha

Script temporal de Python **fuera del repositorio** (por ejemplo `%TEMP%\spec002_verify.py`), generado desde Bash (no con un here-string de PowerShell) y ejecutado con `.venv\Scripts\python.exe` desde la raíz del proyecto, siguiendo la skill sdd:

1. `async with engine.connect() as conn`, `trans = await conn.begin()`.
2. `app.dependency_overrides[get_db]` por un generador que entrega `AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)`.
3. **Preparación dentro de la transacción** (con `await conn.execute(text(...))` y parámetros; nunca se tocan filas reales salvo en S1 a S3, que modifican el producto 1 mediante la API y se deshacen):
   - Productos temporales, cada uno con `INSERT INTO products (name, description, price, stock, category_id) VALUES (...) RETURNING id`:
     - `P_obj` "Objetivo spec002" (descripción "antes", categoría 1): destino de los renombrados.
     - `P_mal` con nombre `'  Teclado prueba  '` y descripción `'  hola  '` (no cumple las reglas, RF-7).
     - `Teclado`, `CAMION`, `PINGUINO`, `Ano`, `STRASSE`, `Teclado mecánico`, `Canción` (ó en un solo carácter, `ó`), `ÑANDU`, `crème`, `Garcon`, `öl`, `Kelvin`.
     - `Repetido` dos veces (`P_rep1`, `P_rep2`), y `teclado minúsculas`, `Camion propio`. (`Kelvin` se inserta con la letra `K` normal; N10 envía el signo kelvin.)
   - Categoría temporal (autorizada): `INSERT INTO categories (name) VALUES ('spec002-temporal') RETURNING id`, y después `DELETE FROM categories WHERE id = :id_temporal` (solo esa fila).
4. `uvicorn.Server(Config(app, port=8002))` en un hilo; peticiones con `urllib.request` (método `PUT`, cuerpo en bytes UTF-8; las `HTTPError` se leen para obtener código y cuerpo) y comprobación automática de código y cuerpo esperados; `server.should_exit = True`.
5. `await trans.rollback()`, `await engine.dispose()`.

**Verificaciones previas de seguridad (V)** — primero aquí, después repetidas en el 8000 con `Put-Product`:

| Id | Petición | Esperado |
|---|---|---|
| V1 | `PUT /products/1` con `{"name": "X", "price": 10, "stock": 1, "category_id": 999}`, y con `0`, `-3`, `100000000000000000000`, `-100000000000000000000`, `'9'*4000` | 422 `No existe ninguna categoría con el id {id}` |
| V2 | `PUT /products/2` con el nombre del producto 1 (leído con `GET /products/1`) y datos válidos | 409 `Ya existe otro producto con el nombre {nombre del 1}` |
| V3 | `PUT /products/<P_obj>` con `category_id` = id temporal borrado | 422 `No existe ninguna categoría con el id {id_temporal}`; `P_obj` sin cambios |
| V4 | `PUT /products/999` con datos válidos y categoría 999 | 404 (no se informa de la categoría) |
| V5 | `PUT /products/1` con categoría 999 **y** el nombre del producto 2 | 422 de categoría (no 409) |

Tras cada V, `GET /products/<id>` devuelve exactamente lo mismo que antes de la petición.

**Éxitos (S)** — todos 200:

| Id | Petición | Esperado |
|---|---|---|
| S1 | `PUT /products/1` con `{"name": "Smartphone editado", "price": 649.9, "stock": 10, "category_id": 2}` | `"price": "649.90"`, `"category": {"id": 2, ...}`, `description` null, mismo `id` y `created_at` que antes |
| S2 | `GET /products/1` | Idéntico a la respuesta de S1 |
| S3 | `GET /products` | Mismo orden de ids que antes; el elemento del producto 1 sigue en la misma posición y es igual a S1 |
| S4 | `PUT /products/<P_obj>` sin `description`; después con `null`, `""` y `"   "` (reponiendo "antes" entre medias) | `description` null en los cuatro casos |
| S5 | `PUT /products/<P_obj>` con `"name": "A", "name": "B"` | `"name": "B"` |
| S6 | Precio `0.01`, `99999999.99`, `19.900`, `1e2` | `"0.01"`, `"99999999.99"`, `"19.90"`, `"100.00"` |
| S7 | Stock `0`; nombre `"  Teclado obj  "` | `stock` 0; `"name": "Teclado obj"` |
| S8 | Cuerpo con `"id": 1, "created_at": "2000-01-01"` sobre `P_obj` | Se modifica `P_obj`; su `id` y `created_at` no cambian |
| S9 | Cuerpo con `"id": "abc", "created_at": null, "extra": NaN` y el resto válido | 200 (o 500 por `NaN` en dato extra, desviación; si 500, `P_obj` sin cambios) |
| S10 | Reenviar los datos actuales de `P_obj` | 200, producto idéntico |
| S11 | `PUT /products/<P_mal>` con `"  Teclado prueba  "` y `"  hola  "` | `"Teclado prueba"`, `"hola"` (normalizados) |
| S12 | Reenviar como cuerpo la respuesta de `GET /products/<P_obj>` | 422 por el precio en texto (sin cambios) |

**Nombres (N)** — sobre `P_obj` salvo que se indique:

| Id | Nombre enviado | Esperado |
|---|---|---|
| N1 | `"  TECLADO "` | 409 `Ya existe otro producto con el nombre TECLADO` |
| N2 | `Camión` | 409 `... con el nombre Camión` (existe `CAMION`) |
| N3 | `pingüino` | 409 (existe `PINGUINO`) |
| N4 | `Cancio` + `́` + `n` (ó descompuesta) | 409 (existe `Canción` compuesta) |
| N5 | `ñandú` | 409 (existe `ÑANDU`) |
| N6 | `Año` | 200 (`Ano` no es equivalente) |
| N7 | `Straße` | 200 |
| N8 | `Teclado  mecánico` (doble espacio) | 200 |
| N9 | `CRÈME` (existe `crème`), `Garçon` (existe `Garcon`), `ÖL` (existe `öl`), `Ｔeclado` con T de ancho completo (existe `Teclado`) | 200 cada uno (no equivalentes) |
| N10 | `Kelvin` con `K` (signo kelvin, U+212A) | 409 `Ya existe otro producto con el nombre {nombre enviado}` (existe `Kelvin` con la letra `K`; NFC los iguala, spec duda 18) |
| N11 | `P_rep1` con `Repetido`, y después con `REPETIDO` | 200 y 200 (no es cambio de nombre; existe `P_rep2` igual) |
| N12 | `P_rep1` con categoría 999 y nombre `Teclado` | 422 de categoría, no 409 |
| N13 | `teclado minúsculas` → `Teclado Minúsculas`; `Camion propio` → `Camión propio` (sobre sí mismos) | 200; se guarda el nombre enviado |

Además, en el mismo script: `POST /products` con el nombre de un producto existente → 201 (RNF-5, crear sigue permitiendo repetidos).

### Base de datos no disponible (B)

- **B1:** un segundo script temporal fuera del repositorio fija `os.environ["DB_PORT"] = "1"` **antes** de importar la app (solo ese proceso; `.env` no se toca) y arranca `uvicorn.Server` en el 8001. `PUT /products/1` con datos válidos → 500; `GET /healthz` → 503.

### Regresión y cierre (R, C)

- **R1:** el servidor del usuario recarga sin errores; `/docs` y `/openapi.json` muestran `PUT /products/{product_id}` con cuerpo `ProductUpdate` y respuesta `ProductRead`.
- **R2:** `Invoke-RestMethod http://127.0.0.1:8000/hello-world`, `/healthz`, `/categories`, `/categories/1`; `curl.exe -i` de `/categories/999` (404) y `/products/999` (404).
- **R3:** `POST /products` sin cambios: casos E15 y E17 de la spec 001 (`category_id` 999 y `2147483648` → 422) y `category_id` `-2147483648` → 422 (efecto de D7); `POST /categories` con `{"name": "electronics"}` → 409.
- **R4:** con Python 3.12 en el entorno de pruebas fuera del proyecto (como R4 de la spec 001): arranque, G1, V1 y N1 a N9 en el script deshecho. Si ese entorno con Python 3.12 ya no existe, @implementer para y pregunta al usuario cómo conseguirlo; no lo recrea por su cuenta (decidido por el usuario el 2026-10-08).
- **R5:** comprobación de que no se ha añadido nada a `requirements.txt` ni a `main.py`.
- **C2 (solo lectura):** recuentos 24 productos y 6 categorías.
- **C3:** `curl.exe -s http://127.0.0.1:8000/products -o "$env:TEMP\spec002-despues.json"` y `(Get-FileHash "$env:TEMP\spec002-antes.json").Hash -eq (Get-FileHash "$env:TEMP\spec002-despues.json").Hash` → `True`. Borrar después los archivos temporales y los scripts.

**No se verifican** (limitaciones conocidas de la spec): modificaciones simultáneas (RF-8), carrera de renombrados (RF-12) y categoría borrada entre la comprobación y el `commit` (RF-4). El camino del 23503 es el mismo que se verificó en la spec 001 (F1).

## 8. Riesgos y documentación

**Qué podría romperse:**
- **`GET /products/{product_id}`:** se toca para RF-10. G3 y R2 comprueban que el resto no cambia.
- **`POST /products`:** se sustituye su comprobación de rango por `fits_in_integer`. R3 comprueba que responde igual.
- **`FOR UPDATE`:** una modificación espera si otra tiene bloqueada la misma fila. Combinarlo con `joinedload` puede fallar en PostgreSQL (D4); por eso la lectura bloqueante va sin `joinedload`.
- **Coste del duplicado:** cada renombrado lee los nombres de todos los demás productos. Aceptable con el tamaño actual; si el catálogo crece mucho, habría que replantearlo (otra spec).
- **Versión de Unicode:** NFC usa la tabla de Unicode de cada versión de Python (3.12 frente a 3.14). Para las letras del alfabeto español no hay diferencias; R4 lo comprueba.
- **Dos formatos de 422 y un 409 sin UNIQUE:** los clientes deben aceptar lista o texto en `detail`, como hoy.
- **Ids consumidos:** los `INSERT` de preparación del script consumen ids de `products` y `categories` aunque se deshagan (efecto aceptado por la skill sdd).

**Puntos de la spec resueltos (2026-10-08, spec dudas 17 y 18; la spec sigue aprobada):**
1. **Redacción de "Nombres equivalentes".** Corregida en la spec: solo se igualan A–Z, Ñ, á é í ó ú y ü; `à`, `ç`, `ö` no se igualan a la letra sin marca ni entre mayúscula y minúscula (`À` ≠ `à`). Coincide con la tabla de D2; el plan no cambia.
2. **Signos con equivalencia oficial de Unicode.** Aceptado (opción a): el signo kelvin (U+212A) cuenta como `K`, el ohmio (U+2126) como `Ω` y el ångström (U+212B) como `Å`, porque NFC (D2) los iguala. No se excluyen a mano. N10 espera 409.

**Documentación que hay que actualizar (en la fase de documentación, no en este plan):**
- **README.md:** **antes del código**, fila y sección `PUT /products/{product_id}`, 404 con ids enormes en `GET /products/{product_id}` y ejemplo en "Probar desde la terminal". La sección "Estructura del proyecto" sigue desactualizada (fuera de alcance, ya anotado en MEMORY.md).
- **CLAUDE.md:**
  - `products.py` con `PUT /products/{product_id}`; `product.py` con `ProductUpdate`, `MIN_INTEGER` y `product_name_key`.
  - Regla de códigos: el 409 ya no es solo "IntegrityError por UNIQUE"; también el nombre de producto repetido al modificar, comprobado en el endpoint sin UNIQUE.
  - Trampa de ids enormes: "compruébalo antes de consultar" pasa a ser `fits_in_integer` en el router de productos; `GET /categories/{id}` sigue pendiente.
  - Trampa nueva: `with_for_update=True` sin `joinedload` en la misma lectura; la relación se carga en la reconsulta.
- **Spec 001 (implementada):** la desviación de `NaN` → 500 solo menciona precio y stock; en realidad afecta a cualquier dato del cuerpo. Cambiarla requiere la aprobación del usuario por ser una spec cerrada.
- **MEMORY.md:** estado de la spec 002, decisiones D1 a D9 resumidas y aprendizajes que salgan de la implementación (D4 y D8 marcados "a comprobar").
