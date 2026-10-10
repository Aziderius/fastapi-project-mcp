# Tareas 002: Editar productos

**Spec:** `spec.md` (aprobada el 2026-10-08) · **Plan:** `plan.md` · **Fecha:** 2026-10-08 · **Estado:** aprobadas por el usuario el 2026-10-08

**Convenciones para todas las tareas:**
- El servidor del usuario está en el 8000 con `--reload` y recoge los cambios solo: el implementer **no** lo arranca. Los servidores de prueba usan el 8002 (transacción deshecha) y el 8001 (base de datos caída, solo en T-8).
- `Put-Product` y `$ok` son la función y la variable de PowerShell de la sección 7 del plan.
- **Script deshecho:** el script temporal de la sección 7 del plan, fuera del repositorio (por ejemplo `%TEMP%\spec002_verify.py`), generado desde Bash y ejecutado con `.venv\Scripts\python.exe` desde la raíz. Abre una transacción externa, sustituye `get_db` por una `AsyncSession` con `join_transaction_mode="create_savepoint"`, prepara los datos temporales del plan, arranca la app en el 8002, hace las peticiones, comprueba código y cuerpo, y deshace todo con `rollback` + `engine.dispose()`. **Toda petición que pueda escribir (200 de un `PUT`) se hace solo aquí, nunca contra el 8000.**
- Los casos 404, 422 de categoría y 409 con un producto existente se ejecutan **primero** en el script deshecho y solo si pasan se repiten en el 8000 (regla de seguridad del plan).
- Las comprobaciones con `python -c` usan el `.venv` del proyecto y se ejecutan desde la raíz.
- **Regla de regresión**, parte de "Hecho cuando" en toda tarea que toca `app/`:
  - El servidor del 8000 recarga sin errores de importación.
  - `Invoke-RestMethod` de `/hello-world`, `/healthz` (`{"status": "ok", "database": "ok"}`), `/categories` y `/categories/1` responden como antes; `curl.exe -i` de `/categories/999` y `/products/999` dan 404.
  - La instantánea de `/products` tomada en T-1 sigue teniendo el mismo hash (C3 del plan): no ha cambiado ningún dato.
- No se hace commit al terminar ninguna tarea (regla de CLAUDE.md).

## Preparación

- [x] **T-1: Preparar las herramientas de verificación y la instantánea previa**
  - RF: —
  - Archivos: ninguno del repositorio. Temporales fuera de él: el script deshecho (con la preparación de datos del plan: `P_obj`, `P_mal`, los productos de nombres, `P_rep1`/`P_rep2` y la categoría temporal creada y borrada) y `%TEMP%\spec002-antes.json`.
  - Hecho cuando:
    - `curl.exe -s http://127.0.0.1:8000/products -o "$env:TEMP\spec002-antes.json"` ha guardado la instantánea C1 (24 productos).
    - El script deshecho arranca en el 8002, la preparación termina sin errores y `GET http://127.0.0.1:8002/products` devuelve 24 productos más los temporales; al terminar hace `rollback`.
    - Una consulta de solo lectura posterior cuenta 24 productos y 6 categorías, y el hash de `/products` en el 8000 coincide con la instantánea.

## Documentación primero (principio 2)

- [x] **T-2: Escribir el contrato de `PUT /products/{product_id}` y la corrección del GET en el README**
  - RF: — (documenta RF-1 a RF-13 antes del código)
  - Archivos: `README.md`
  - Cambio (plan, sección 4, punto 1): fila en la tabla de endpoints; sección `PUT /products/{product_id}` con sustitución completa, campos (remitiendo a `POST /products`), 200 de ejemplo, errores en su orden (422 JSON mal formado → 422 formato → 404 → 422 categoría → 409), nombres equivalentes con ejemplos (`Camión`/`CAMION` y `Kelvin` con signo kelvin duplicados; `Año`/`Ano`, `Straße`/`STRASSE`, `À`/`à` distintos), cambio solo de mayúsculas o tildes del propio nombre permitido, limitaciones y desviaciones conocidas; "404 también con ids enormes" en `GET /products/{product_id}`; ejemplo de `PUT` en "Probar desde la terminal" con el aviso de que modifica datos reales.
  - Hecho cuando:
    - Todo coincide con la sección 3 del plan (códigos, mensajes y orden).
    - No se ha tocado `app/`: la regla de regresión se cumple sin cambios.

## Schemas

- [x] **T-3: `MIN_INTEGER` y `ProductUpdate`**
  - RF: RF-2, RF-3, RF-6 (datos no previstos ignorados)
  - Archivos: `app/schemas/product.py`
  - Cambio: constante `MIN_INTEGER` (−2 147 483 648) junto a `MAX_INTEGER`, con comentario; clase `ProductUpdate(ProductCreate)` sin campos ni validadores nuevos, con docstring; comentario de cabecera actualizado (D1).
  - Hecho cuando:
    - `python -c "from app.schemas.product import ProductUpdate as U; print(U.model_validate({'name': '  Teclado  ', 'description': '   ', 'price': 1e2, 'stock': 0, 'category_id': 1, 'id': 'abc', 'created_at': None}))"` imprime `name='Teclado' description=None price=Decimal('100.0') stock=0 category_id=1` (sin `id` ni `created_at`).
    - Con `price` `'19.90'` o `True` da `ValidationError` con `El precio debe ser un número`; con `stock` `5.0` o `'5'`, `category_id` `1.5` o `'2'`, o sin `name` da `ValidationError`.
    - `python -c "from app.schemas.product import MIN_INTEGER, MAX_INTEGER; print(MIN_INTEGER, MAX_INTEGER)"` imprime `-2147483648 2147483647`.
    - Se cumple la regla de regresión.

- [x] **T-4: Clave de comparación de nombres `product_name_key`**
  - RF: RF-12 (definición de nombres equivalentes y de cambio de nombre)
  - Archivos: `app/schemas/product.py`
  - Cambio (D2): tabla de traducción con `str.maketrans` (A–Z → a–z; Á É Í Ó Ú Ü y á é í ó ú ü → vocal sin marca en minúscula; Ñ → ñ) con un comentario de lo que **no** se iguala; función `product_name_key(name)` = `strip()` + `unicodedata.normalize("NFC")` + `translate`, con docstring y ejemplos (incluido el signo kelvin).
  - Hecho cuando un `python -c` que importa `product_name_key as k` imprime `True` para cada una de estas comparaciones (todas en una línea de salida):
    - Iguales: `k('Camión') == k('CAMION')`, `k('pingüino') == k('PINGUINO')`, `k('  TECLADO ') == k('Teclado')`, `k('Canción') == k('Canción')`, `k('ñandú') == k('ÑANDU')`, `k('Kelvin') == k('Kelvin')`.
    - Distintas: `k('Año') != k('Ano')`, `k('Straße') != k('STRASSE')`, `k('À') != k('à')`, `k('CRÈME') != k('crème')`, `k('Garçon') != k('Garcon')`, `k('ÖL') != k('öl')`, `k('Ｔeclado') != k('Teclado')`, `k('Teclado  mecánico') != k('Teclado mecánico')`.
    - Se cumple la regla de regresión.

## Router

- [x] **T-5: `fits_in_integer`, `product_not_found` y corrección de `GET /products/{product_id}`**
  - RF: RF-10 (y prepara RF-4 y RF-5)
  - Archivos: `app/routers/products.py`
  - Cambio (D7): función `fits_in_integer(value)` con `MIN_INTEGER`/`MAX_INTEGER`; función `product_not_found(product_id)` con el 404 actual; `get_product` responde 404 sin consultar si el id no cabe; `create_product` usa `fits_in_integer` en lugar de su comprobación en línea.
  - Hecho cuando:
    - G1 y G2 del plan: `curl.exe -i http://127.0.0.1:8000/products/99999999999999999999`, `/-99999999999999999999` y `/2147483648` → 404 `No existe ningún producto con el id {id}` (nunca 500).
    - G3: `/products/1` → 200, `/products/999` → 404, `/products/abc` → 422, `/products/05` → 200 del producto 5, igual que antes.
    - R3 (parte del POST, fallan antes del `commit`): `POST /products` con `category_id` `999`, `2147483648` y `-2147483648` → 422 `No existe ninguna categoría con el id {id}`.
    - Se cumple la regla de regresión.

- [x] **T-6: Endpoint `PUT /products/{product_id}` (sin la comprobación de nombres repetidos)**
  - RF: RF-1, RF-2, RF-3, RF-4, RF-5, RF-6, RF-7, RF-8 (bloqueo), RF-9, RF-11 (hasta la categoría), RF-13
  - Archivos: `app/routers/products.py`
  - Cambio (plan, sección 4, punto 3, pasos 1–3 y 5–7; D4, D5, D6, D9): `update_product` con `response_model=ProductRead` y 200; id fuera de rango → 404; `db.get(Product, id, with_for_update=True)` sin `joinedload` → 404 si no existe; categoría fuera de rango o inexistente → 422; asignación de los cinco datos; `commit` con respaldo `IntegrityError` 23503 → 422 y `rollback`; reconsulta con `joinedload` y `populate_existing=True`; comentario de cabecera. El paso 4 (409) queda para T-7.
  - Hecho cuando:
    - `/docs` muestra `PUT /products/{product_id}` con cuerpo `ProductUpdate` y respuesta `ProductRead`.
    - En el script deshecho (8002): S1 (200, `"price": "649.90"`, categoría 2, `description` null, mismo `id` y `created_at`), S2, S3, S4, S6 y S11 dan lo esperado; V1, V3 y V4 dan 422/422/404 y el producto no cambia.
    - D4 comprobado en el mismo script: la lectura con `with_for_update=True` sin `joinedload` funciona (y se anota si `with_for_update` + `joinedload` falla, como prevé el plan).
    - Después, en el 8000: E16, E17, E18 y E20 (formato) y, ya pasados en el 8002, V1 y V4 dan lo mismo.
    - Se cumple la regla de regresión (24 productos, 6 categorías, mismo hash).

- [x] **T-7: Nombres repetidos al modificar (409)**
  - RF: RF-12, RF-11 (último nivel)
  - Archivos: `app/routers/products.py`
  - Cambio (plan, sección 4, punto 3, paso 4; D3): si `product_name_key` del nombre recibido difiere del guardado, se leen los nombres de los demás productos (`select(Product.name).where(Product.id != product_id)`) y, si alguno tiene la misma clave, 409 `Ya existe otro producto con el nombre {nombre recibido recortado}`, antes de asignar datos.
  - Hecho cuando:
    - En el script deshecho (8002): V2 → 409, V5 → 422 de categoría (no 409), N1 → 409 `... con el nombre TECLADO`, N2 → 409 `... Camión`, N6 → 200, N10 → 409, N11 → 200 y 200, N12 → 422, N13 → 200 con el nombre enviado; `POST /products` con un nombre existente → 201 (RNF-5).
    - Después, en el 8000: V2 y V5 dan lo mismo.
    - Se cumple la regla de regresión.

## Cierre

- [x] **T-8: Verificación completa**
  - RF: RF-1 a RF-13 (y RNF-1 a RNF-5)
  - Archivos: ninguno del repositorio (scripts temporales fuera de él, que se borran al terminar).
  - Hecho cuando todas las pruebas de la sección 7 del plan dan el resultado esperado:
    - E1 a E24 contra el 8000 (producto 999999; E23 admite 422 o 500 por la desviación de `NaN`).
    - V1 a V5, S1 a S12 y N1 a N13 en el script deshecho (8002); V1 a V5 repetidos después en el 8000.
    - L1 y L2 contra el 8000 (404 con el id interpretado; mismas formas en `GET` dan el mismo id).
    - G1 a G3.
    - B1: `DB_PORT=1` solo en el proceso de prueba (8001), `PUT /products/1` → 500 y `/healthz` → 503; `.env` sin tocar.
    - R1 a R5 (`/docs` y `/openapi.json`, regresión, `POST /products` y `POST /categories` → 409, Python 3.12, `requirements.txt` y `main.py` sin cambios).
    - C2: una consulta de solo lectura cuenta **24 productos y 6 categorías**.
    - C3: el hash de `/products` coincide con la instantánea de T-1; después se borran los archivos temporales y los scripts.
  - R4 (Python 3.12): si el entorno de pruebas con Python 3.12 de la spec 001 ya no existe, parar y preguntar al usuario cómo conseguirlo; no recrearlo por cuenta propia (decidido por el usuario el 2026-10-08).
    - R4 no ejecutado: entorno 3.12 sin dependencias; omitido por decisión del usuario el 2026-10-08, pendiente.

- [x] **T-9: Actualizar CLAUDE.md, MEMORY.md y README.md**
  - RF: —
  - Archivos: `CLAUDE.md`, `MEMORY.md`, `README.md` (y `specs/001-crear-productos/spec.md` **solo si el usuario lo aprueba**)
  - Cambio, según la sección 8 del plan:
    - **CLAUDE.md:** `PUT /products/{product_id}` en `products.py`; `ProductUpdate`, `MIN_INTEGER` y `product_name_key` en `product.py`; el 409 también para el nombre repetido al modificar (sin UNIQUE); trampa de ids enormes resuelta con `fits_in_integer` en productos (categorías pendiente); trampa nueva: `with_for_update=True` sin `joinedload` en la misma lectura.
    - **MEMORY.md:** estado verificado de la spec 002, D1 a D9 resumidas, resultado de las comprobaciones de D4 y D8, máximo ~50 líneas.
    - **README.md:** ajustar la sección de T-2 si T-8 ha mostrado alguna diferencia (principio 2).
    - **Spec 001 — requiere aprobación del usuario:** ampliar la desviación de `NaN` → 500 a cualquier dato del cuerpo. Sin aprobación, no se toca y queda anotado en MEMORY.md.
  - Hecho cuando:
    - La sección `PUT /products/{product_id}` del README coincide con los resultados de T-8.
    - CLAUDE.md describe `PUT /products/{product_id}` y las trampas nuevas.
    - MEMORY.md tiene 50 líneas o menos y no contiene datos sensibles.
    - La spec 001 solo ha cambiado si el usuario lo aprobó expresamente.
    - No se ha hecho commit.

## Cobertura RF → tareas

| RF | Tareas que lo implementan | Tareas que lo verifican |
|---|---|---|
| RF-1 Modificación, visibilidad, posición | T-6 | T-6, T-8 (S1, S2, S3) |
| RF-2 Datos de entrada, descripción nula, cuerpo, repetidos | T-3 (herencia), T-6 (asignación) | T-3, T-6, T-8 (E1 a E3, E21, E22, S4, S5, S12) |
| RF-3 Validaciones idénticas, precio exacto | T-3 (herencia) | T-3, T-6, T-8 (E4 a E13, S6, S7) |
| RF-4 Cambio de categoría, inexistente, borrada | T-5 (rango), T-6 | T-6, T-8 (S1, E14, E15, V1, V3, V5) |
| RF-5 Producto inexistente, formas del id | T-5 (`fits_in_integer`, `product_not_found`), T-6 | T-6, T-8 (E16 a E19, V4, L1, L2) |
| RF-6 Datos fijos y no previstos | T-3, T-6 | T-3, T-8 (S1, S8, S9) |
| RF-7 Respuesta, sin cambios, datos no conformes | T-6 (reconsulta) | T-6, T-8 (S1, S10, S11) |
| RF-8 Simultáneas | T-6 (`with_for_update`) | No verificado (limitación conocida); revisión de código en T-6 |
| RF-9 Sin efectos parciales | T-6 (errores antes del `commit`, `rollback`), T-7 | Todas (regla de regresión), T-8 (V1 a V5, C2, C3) |
| RF-10 GET con ids enormes | T-5 | T-5, T-8 (G1 a G3) |
| RF-11 Orden de errores | T-6 (404 → 422), T-7 (409 al final); FastAPI para los dos primeros niveles | T-6, T-7, T-8 (E15, E17, E18, E20, V4, V5, N12) |
| RF-12 Nombres repetidos | T-4 (`product_name_key`), T-7 | T-4, T-7, T-8 (N1 a N13) |
| RF-13 Base de datos caída | T-6 (sin código propio: 500 por defecto) | T-8 (B1) |

Todos los RF tienen al menos una tarea que los implementa; todos menos RF-8 (limitación conocida de la spec) tienen otra que los verifica.
