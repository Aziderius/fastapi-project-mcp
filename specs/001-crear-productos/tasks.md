# Tareas 001: Crear productos

**Spec:** `spec.md` (v2) · **Plan:** `plan.md` · **Fecha:** 2026-10-07 · **Estado:** completadas el 2026-10-07

**Convenciones para todas las tareas:**
- Los servidores de prueba usan los puertos 8001 y 8002, porque el del usuario usa el 8000.
- `Send-Product` y `$ok` son la función y la variable de PowerShell de la sección 7 del plan.
- Las comprobaciones con `python -c` usan el `.venv` del proyecto y se ejecutan desde la raíz.
- **Regla de regresión**, que forma parte de "Hecho cuando" en toda tarea que toca `app/`: el servidor arranca sin errores y las 11 respuestas de referencia (R2 del plan) siguen idénticas byte a byte.
- No se hace commit al terminar ninguna tarea (regla de CLAUDE.md).

## Preparación

- [x] **T-1: Comprobar las herramientas de verificación**
  - RF: —
  - Archivos: ninguno del repositorio. Scripts temporales fuera de él: el servidor de prueba con la transacción que se deshace (plan, sección 7) y el comparador de respuestas de referencia.
  - Hecho cuando:
    - El servidor de prueba arranca en el 8002 y `Invoke-RestMethod http://127.0.0.1:8002/products` devuelve los 23 productos.
    - Al detenerlo, una consulta de solo lectura sigue contando 23 productos y 6 categorías.
    - El comparador devuelve `11/11 respuestas idénticas` contra el código actual.
  - [REVISAR PLAN] R2 usa "las 11 respuestas de referencia guardadas antes de la migración a async", que están en la carpeta temporal de la sesión. Si esa carpeta ya no existe cuando se ejecuten estas tareas, el plan no dice si hay que volver a capturarlas desde el código actual (que es equivalente) ni quién lo decide.

## Documentación primero (principio 2)

- [x] **T-2: Escribir el contrato de `POST /products` en el README**
  - RF: — (documenta el contrato de RF-1 a RF-10 antes del código)
  - Archivos: `README.md`
  - Hecho cuando:
    - La tabla de endpoints tiene la fila `POST /products`.
    - Hay una sección `POST /products` con el cuerpo, las validaciones, el ejemplo de respuesta 201 y los dos tipos de 422 (lista de FastAPI y `"No existe ninguna categoría con el id 999"`).
    - "Probar desde la terminal" tiene un ejemplo nuevo.
    - Todo coincide con la sección 3 del plan.
    - El servidor sigue arrancando sin cambios, porque no se ha tocado código.

## Schema de entrada

- [x] **T-3: `ProductCreate` con nombre y descripción**
  - RF: RF-2 (nombre obligatorio), RF-3, RF-4
  - Archivos: `app/schemas/product.py`
  - Cambio:
    - Constante del máximo de un INTEGER (2 147 483 647) con su comentario.
    - Clase `ProductCreate` con `name` (recortado, de 1 a 150) y `description` (opcional, recortada, de 255 como máximo, y `None` si queda vacía).
    - Comentario de cabecera actualizado.
  - Hecho cuando:
    - `python -c "from app.schemas.product import ProductCreate as P; print(repr(P.model_validate({'name': '\t  Teclado  \n', 'description': '   '}).name), P.model_validate({'name': 'X', 'description': '  hola  '}).description)"` imprime `'Teclado' hola`.
    - Con `'name': '   '`, con `'name': 'a' * 151` y con `'description': 'd' * 256` da `ValidationError`.
    - Con `'description': ' ' * 300` da `description=None`.
    - Se cumple la regla de regresión.

- [x] **T-4: Precio en `ProductCreate`**
  - RF: RF-5
  - Archivos: `app/schemas/product.py`
  - Cambio:
    - `price` como `Decimal` mayor que 0 y menor que 100 000 000, con 2 decimales.
    - Validador previo que rechaza texto y booleanos con `"El precio debe ser un número"`.
  - Hecho cuando:
    - `python -c "from app.schemas.product import ProductCreate as P; print(P.model_validate({'name': 'X', 'price': 19.900}).price, P.model_validate({'name': 'X', 'price': 1e2}).price)"` imprime `19.9 100.0`. El formato `"19.90"` y `"100.00"` se comprueba en T-6.
    - Con `price` igual a `0`, `-5`, `0.001`, `19.999`, `100000000`, `float('nan')`, `'19.90'` y `True` da `ValidationError`. Los dos últimos con el mensaje `El precio debe ser un número`.
    - Se cumple la regla de regresión.

- [x] **T-5: Stock y categoría en `ProductCreate`**
  - RF: RF-2 (el resto de datos obligatorios), RF-6, RF-7 (formato del id)
  - Archivos: `app/schemas/product.py`
  - Cambio:
    - `stock` como entero estricto entre 0 y el máximo de INTEGER.
    - `category_id` como entero estricto.
  - Hecho cuando:
    - `python -c "from app.schemas.product import ProductCreate as P; print(P.model_validate({'name': 'X', 'price': 10, 'stock': 0, 'category_id': 10**20}))"` imprime el modelo con `stock=0 category_id=100000000000000000000`. El formato es válido; la existencia se comprueba en T-6.
    - Con `stock` igual a `-1`, `2147483648`, `1.5`, `5.0`, `'5'` y `True`, y con `category_id` igual a `1.5`, `'1'` y `None`, da `ValidationError`.
    - Sin `name`, `price`, `stock` o `category_id` da `ValidationError` de dato ausente.
    - Se cumple la regla de regresión.

## Endpoint

- [x] **T-6: Endpoint `POST /products` (camino feliz y categoría inexistente)**
  - RF: RF-1, RF-5 (formato de salida), RF-7 (comprobación previa e ids fuera de rango), RF-8, RF-9
  - Archivos: `app/routers/products.py`
  - Cambio:
    - Función que construye el 422 de categoría inexistente.
    - Endpoint `create_product` con 201 y `ProductRead`, que hace en orden:
      1. Si el id está fuera del rango de INTEGER, responde 422.
      2. Si `db.get(Category, id)` devuelve `None`, responde 422.
      3. Crea el producto, lo añade a la sesión y hace `commit`.
      4. Vuelve a consultarlo con `joinedload(Product.category)` y `populate_existing=True`.
    - Comentario de cabecera actualizado. Todavía **sin** tratar `IntegrityError`; eso va en T-7.
  - Hecho cuando:
    - `/docs` muestra `POST /products`.
    - `Send-Product '{"name": "X", "price": 10, "stock": 1, "category_id": 999}'` devuelve `422 -> {"detail":"No existe ninguna categoría con el id 999"}`.
    - Lo mismo con `2147483648`, con el mensaje correspondiente y **no** 500.
    - En el servidor de prueba del 8002:
      - `Send-Product '{"name": "Teclado", "price": 49.9, "stock": 0, "category_id": 1}' 8002` devuelve `201` con `"price":"49.90"` y `"category":{"id":1,"name":"electronics"}`.
      - `Invoke-RestMethod http://127.0.0.1:8002/products/<id>` devuelve lo mismo.
    - Al detener el servidor de prueba siguen contándose 23 productos.
    - Se cumple la regla de regresión.

- [x] **T-7: Fallo de clave foránea en el `commit`**
  - RF: RF-7 (categoría que desaparece durante el alta), RF-10
  - Archivos: `app/routers/products.py`
  - Cambio: capturar `IntegrityError` en el `commit` y hacer `rollback`. Si el código es `23503`, responder con el 422 de categoría inexistente; si no, relanzar el error.
  - Hecho cuando:
    - La prueba F1 del plan (un script con la transacción deshecha que simula que la categoría 999999 existe en la comprobación previa) devuelve 422 con `"No existe ninguna categoría con el id 999999"`.
    - No queda ningún producto creado: siguen siendo 23.
    - Se cumple la regla de regresión.

## Cierre

- [x] **T-8: Verificación completa**
  - RF: RF-1 a RF-10 (y RNF-1 a RNF-5)
  - Archivos: ninguno del repositorio (servidores y scripts de prueba temporales).
  - Hecho cuando todas las pruebas de la sección 7 del plan dan el resultado esperado:
    - E1 a E22 contra el 8001.
    - S1 a S12 contra el 8002, con la transacción deshecha.
    - F1.
    - R1, que incluye `/docs` y `/openapi.json`.
    - R2: las 11 respuestas de referencia, `/healthz` y un 500 con `DB_PORT=1` solo en el proceso de prueba.
    - R3: siguen 23 productos y 6 categorías.
    - R4: R1, E15, E17 y S1 con Python 3.12.
  - [REVISAR PLAN]
    - **E2 (`name` nulo) y E14 (`category_id` nulo):** el plan espera "ausente o nulo", pero la spec (RF-2) pide que un obligatorio nulo **se señale como ausente**. El plan no incluye ningún mecanismo para eso: Pydantic lo informa como error de tipo (`string_type` o `int_type`), no como `missing`. Hay que decidir si el tipo de error vale o si el plan debe añadir ese tratamiento.
    - **E22 (`[1, 2]`):** el plan espera `model_attributes_type`. Hay que confirmar el tipo exacto al ejecutar la prueba, porque el plan no lo comprobó.

- [x] **T-9: Actualizar CLAUDE.md, MEMORY.md y README.md**
  - RF: —
  - Archivos: `CLAUDE.md`, `MEMORY.md`, `README.md`
  - Cambio, según la sección 8 del plan:
    - **CLAUDE.md:**
      - `POST /products` y `ProductCreate` en la arquitectura.
      - Los papeles de `specs/NNN-*/` (el diseño) y del README (el contrato, que se escribe antes del código).
      - La regla de códigos: id de la ruta inexistente → 404; id del cuerpo inexistente → 422.
      - La trampa de `populate_existing=True`.
    - **MEMORY.md:**
      - Estado verificado.
      - Decisiones D1 a D4 con su porqué.
      - Aprendizajes: el rango de asyncpg y el modo estricto de `Decimal`.
      - Próximo paso: el defecto de ids enormes en los GET.
    - **README.md:** ajustar la sección de T-2 si la verificación de T-8 ha mostrado alguna diferencia (principio 2).
  - Hecho cuando:
    - La sección `POST /products` del README coincide con los resultados de T-8.
    - CLAUDE.md describe `POST /products`.
    - MEMORY.md tiene 50 líneas o menos y no contiene datos sensibles.
    - No se ha hecho commit.

## Cobertura RF → tareas

| RF | Tareas que lo implementan | Tareas que lo verifican |
|---|---|---|
| RF-1 Alta, id, fecha y visibilidad | T-6 | T-6, T-8 (S1, S11, S12) |
| RF-2 Datos de entrada, ausentes y cuerpo | T-3, T-5 (FastAPI para el cuerpo) | T-3, T-5, T-8 (E1, E2, E20 a E22, S9, S10) |
| RF-3 Nombre | T-3 | T-3, T-8 (S2, S7, S8, E3 a E5) |
| RF-4 Descripción | T-3 | T-3, T-8 (S3, S4, E6) |
| RF-5 Precio | T-4, T-6 (formato de salida) | T-4, T-6, T-8 (S5, S6, E7 a E10) |
| RF-6 Stock | T-5 | T-5, T-8 (S1, E11 a E13) |
| RF-7 Categoría | T-5 (formato), T-6 (existencia y rango), T-7 (carrera) | T-6, T-7, T-8 (E14 a E18, F1) |
| RF-8 Nombres repetidos | T-6 | T-8 (S8) |
| RF-9 Forma de la respuesta | T-6 | T-6, T-8 (S1, S11) |
| RF-10 Sin efectos parciales | T-7 | T-7, T-8 (F1, R3) |

Todos los RF tienen al menos una tarea que los implementa y otra que los verifica.
