# Spec 001: Crear productos

**Estado:** implementada (v2, con 2 desviaciones conocidas; ver sección 9) · **Fecha:** 2026-10-07

## 1. Contexto y objetivo

Hoy el catálogo de productos solo se puede consultar: el listado completo o un producto concreto. No hay forma de añadir productos a través de la API, así que el catálogo solo crece si alguien modifica la base de datos a mano.

**Objetivo:** permitir dar de alta un producto nuevo desde la API, con los mismos datos que muestra la consulta, garantizando que siempre pertenezca a una categoría existente y que sus datos sean válidos.

**Por qué:** es el primer paso para gestionar el catálogo desde la propia API y, en un proyecto educativo, es el ejemplo natural de una operación de escritura con validación y relación con otro recurso.

## 2. Usuarios

- **Quien gestiona el catálogo:** da de alta productos nuevos.
- **Quien integra la API** (una aplicación cliente, un panel de administración): necesita respuestas y errores predecibles.
- **Quien aprende con el proyecto:** usa esta operación como referencia para futuras operaciones de escritura.

En esta versión no hay control de acceso: cualquiera que pueda llamar a la API puede crear productos.

## 3. Historias de usuario

- **HU-1.** Como gestor del catálogo, quiero crear un producto indicando su nombre, descripción, precio, stock y categoría, para que aparezca en el catálogo sin tocar la base de datos.
- **HU-2.** Como gestor del catálogo, quiero recibir el producto completo tras crearlo, para confirmar al instante qué se guardó y con qué identificador.
- **HU-3.** Como integrador, quiero que cada error indique qué dato falla y por qué, con los mensajes propios del proyecto en español, para mostrar al usuario qué corregir.
- **HU-4.** Como gestor del catálogo, quiero poder dar de alta un producto agotado (stock 0), para tenerlo en el catálogo antes de recibir unidades.

## 4. Requisitos funcionales

Notación EARS: *El sistema DEBERÁ…* (siempre), *CUANDO…* (evento), *SI… ENTONCES…* (situación no deseada).

**Definiciones usadas en los requisitos:**
- **Espacio en blanco:** espacio, tabulador, salto de línea, espacio no separable y cualquier otro carácter que represente un hueco en blanco.
- **Longitud:** número de caracteres, contando cada carácter como uno (también un emoji simple), y medida después de quitar los espacios en blanco de los extremos.
- **Error de datos inválidos:** respuesta de error que indica, para cada dato incorrecto o ausente, cuál es y el motivo. Puede incluir varios datos a la vez.

**RF-1. Alta de un producto.**
- CUANDO se envía una petición de alta con datos válidos y una categoría existente, el sistema DEBERÁ crear el producto y responder indicando explícitamente que se ha creado un recurso nuevo, de forma distinguible de una consulta con éxito.
- CUANDO se crea un producto, el sistema DEBERÁ asignarle un identificador único y la fecha y hora de alta, con el mismo formato que muestra la consulta de productos.
- CUANDO se crea un producto, el sistema DEBERÁ hacerlo consultable de inmediato de forma individual y en el listado, en la posición que le corresponde según el orden habitual del listado (por identificador).

**RF-2. Datos de entrada.**
- El sistema DEBERÁ aceptar estos datos: **nombre** (obligatorio), **descripción** (opcional), **precio** (obligatorio), **stock** (obligatorio) e **identificador de categoría** (obligatorio).
- SI un dato obligatorio no se envía o se envía con valor nulo, ENTONCES el sistema DEBERÁ responder con un error de datos inválidos que lo señale como ausente.
- SI el cuerpo de la petición falta, no es un objeto con datos (por ejemplo, es una lista o un texto) o no se puede interpretar, ENTONCES el sistema DEBERÁ responder con un error de datos inválidos.
- SI un dato aparece repetido en el cuerpo de la petición, ENTONCES el sistema DEBERÁ usar el último valor recibido.

**RF-3. Nombre.**
- CUANDO se recibe el nombre, el sistema DEBERÁ quitar los espacios en blanco de los extremos, conservar el resto tal cual (incluidas mayúsculas, minúsculas y espacios internos) y guardarlo así.
- SI la longitud del nombre es 0 o supera los 150 caracteres, ENTONCES el sistema DEBERÁ responder con un error de datos inválidos.
- SI el nombre no es un texto, ENTONCES el sistema DEBERÁ responder con un error de datos inválidos.

**RF-4. Descripción.**
- CUANDO se recibe la descripción, el sistema DEBERÁ quitar los espacios en blanco de los extremos antes de cualquier otra comprobación.
- CUANDO la descripción no se envía, se envía con valor nulo o su longitud es 0, el sistema DEBERÁ guardarla como ausente y devolverla como valor nulo.
- SI la longitud de la descripción supera los 255 caracteres, ENTONCES el sistema DEBERÁ responder con un error de datos inválidos.

**RF-5. Precio.**
- El sistema DEBERÁ evaluar el precio por su valor numérico: los ceros finales no cuentan como decimales (`19.900` equivale a `19.90`) y se admite la notación científica si el valor resultante es válido.
- SI el precio es cero o negativo (incluido `-0`), tiene más de 2 decimales significativos, es igual o mayor que 100 000 000, o no es un número finito, ENTONCES el sistema DEBERÁ responder con un error de datos inválidos. No se redondea.
- CUANDO se crea un producto, el sistema DEBERÁ conservar el precio exacto y devolverlo con exactamente 2 decimales y el mismo formato que en la consulta de productos (por ejemplo, `"19.90"`).

**RF-6. Stock.**
- SI el stock no es un número entero, es negativo o supera 2 147 483 647, ENTONCES el sistema DEBERÁ responder con un error de datos inválidos.
- El sistema DEBERÁ aceptar un stock de 0.

**RF-7. Categoría.**
- SI el identificador de categoría no es un número entero, ENTONCES el sistema DEBERÁ responder con un error de datos inválidos de formato.
- SI el identificador de categoría es un número entero (de cualquier magnitud, incluidos 0 y negativos) que no corresponde a ninguna categoría existente, ENTONCES el sistema DEBERÁ responder con un error de datos inválidos con el mensaje en español `No existe ninguna categoría con el id {id}`.
- El sistema DEBERÁ comprobar la existencia de la categoría solo cuando todos los datos tengan un formato válido. Por eso, en una misma petición, los errores de formato se informan juntos y el de categoría inexistente se informa solo.
- SI la categoría deja de existir entre la comprobación y el final del alta, ENTONCES el sistema DEBERÁ responder con el mismo error de categoría inexistente y no crear el producto.

**RF-8. Nombres repetidos.**
- CUANDO se envía un producto con el mismo nombre que otro existente, en la misma categoría o en otra, el sistema DEBERÁ crearlo igualmente como un producto distinto. Esto también se aplica a altas simultáneas.

**RF-9. Respuesta.**
- CUANDO se crea un producto, el sistema DEBERÁ devolverlo completo y con la misma forma que la consulta individual de un producto: identificador, nombre, descripción, precio, stock, identificador de categoría, la categoría (identificador y nombre) y la fecha de alta.

**RF-10. Sin efectos parciales.**
- SI la petición termina en cualquier error, ENTONCES el sistema NO DEBERÁ crear ningún producto ni modificar productos o categorías existentes.
- El sistema DEBERÁ garantizar que los identificadores sean únicos, pero no que sean consecutivos: un intento fallido puede hacer que se salte un identificador.

## 5. Requisitos no funcionales

- **RNF-1. Coherencia.** Un producto recién creado debe ser indistinguible, en forma y formato, de uno consultado después.
- **RNF-2. Idioma.** Los mensajes de error que escribe el proyecto, como el de la categoría inexistente, van en español (principio 6 de la constitución). Ese principio solo cubre los mensajes propios, así que los mensajes de validación de formato que no escribe el proyecto pueden ir en inglés.
- **RNF-3. Integridad de los datos existentes.** La funcionalidad no altera la estructura del almacenamiento ni modifica productos o categorías existentes.
- **RNF-4. Sin cambios en lo que ya existe.** Las operaciones actuales (consultar productos y categorías, crear categorías y comprobar el estado) responden exactamente igual que antes.
- **RNF-5. Una sola operación.** Cada petición crea como máximo un producto.

## 6. Casos límite

| Caso | Resultado esperado |
|---|---|
| Nombre `"  Teclado  "` o `"\tTeclado\n"` | Se crea como `"Teclado"`. |
| Nombre `"Teclado  mecánico"` (doble espacio interno) | Se crea tal cual. |
| Nombre de 150 caracteres tras recortar, aunque tenga más antes de recortar | Se crea. |
| Nombre de 151 caracteres tras recortar, vacío o solo espacios en blanco | Datos inválidos. |
| Nombre con emojis (cada uno cuenta como un carácter) | Se crea si la longitud es válida. |
| Nombre numérico (`123`) o nulo | Datos inválidos. |
| Descripción `""`, `"   "` o nula | Se crea con descripción nula. |
| Descripción `"  hola  "` | Se crea como `"hola"`. |
| Descripción de 300 espacios en blanco | Se crea con descripción nula (primero se recorta, después se mide). |
| Descripción de 256 caracteres tras recortar | Datos inválidos. |
| Precio `0.01`, `99999999.99`, `19.900` o `1e2` | Se crea (`"0.01"`, `"99999999.99"`, `"19.90"`, `"100.00"`). |
| Precio `0`, `-0`, `-5`, `0.001`, `19.999` o `100000000` | Datos inválidos. |
| Precio no finito (`NaN`, `Infinity`) | Datos inválidos. |
| Stock `0` | Se crea (producto agotado). |
| Stock `-1`, `1.5` o `2147483648` | Datos inválidos. |
| Categoría `1.5` o nula | Datos inválidos de formato. |
| Categoría `999`, `0`, `-3` o `100000000000000000000` | Datos inválidos, `No existe ninguna categoría con el id {id}`. |
| Precio inválido **y** categoría inexistente | Solo se informa del precio. |
| Precio inválido **y** stock inválido | Se informan ambos en la misma respuesta. |
| Cuerpo ausente, mal formado o que es una lista | Datos inválidos. |
| Dato repetido en el cuerpo | Se usa el último valor. |
| Dos altas idénticas, seguidas o simultáneas | Se crean dos productos con identificadores distintos. |
| Alta fallida seguida de una correcta | El nuevo identificador puede no ser consecutivo al anterior. |

## 7. Fuera de alcance

- Editar o borrar productos.
- Crear varios productos en una sola petición.
- Impedir nombres de producto repetidos.
- Crear la categoría en la misma petición si no existe.
- Autenticación o permisos para crear productos.
- Paginación del listado de productos.
- Límites de negocio para precio y stock más bajos que los de RF-5 y RF-6.
- Límites de tamaño del cuerpo de la petición.
- Movimientos de stock, imágenes, monedas o historial de precios.

## 8. Criterios de finalización

- **Antes de implementar:** la documentación del proyecto ya describe la operación, con su cuerpo, su respuesta y sus errores (principio 2 de la constitución).
- Todos los criterios de RF-1 a RF-10 y los casos límite de la sección 6 se han comprobado sin dejar datos de prueba (principios 4 y 5).
  - Las altas con éxito, incluida la visibilidad en el listado y la consulta individual, se comprueban dentro de una prueba que se deshace al terminar.
  - Los errores se comprueban contra la API, porque no guardan nada.
- Las operaciones existentes responden igual que antes (RNF-4).
- La nueva operación aparece en la documentación interactiva de la API.
- La documentación del proyecto coincide con el comportamiento final (principio 2).

## 9. Dudas resueltas y desviaciones conocidas

No quedan dudas abiertas. Las seis se resolvieron con el usuario antes del plan (2026-10-07):

- **Dónde vive la spec.** Conviven: esta spec contiene el diseño, y la sección de la operación en la documentación del proyecto es el contrato público, que se escribe antes del código. El principio 2 de la constitución no cambia.
- **Valores convertibles.** Se rechazan como datos inválidos: el precio o el stock enviados como texto (`"19.90"`, `"5"`), un stock escrito como decimal (`5.0`) y los valores `true`/`false` en campos numéricos. Solo se aceptan números de verdad.
- **Datos no previstos.** Se ignoran (por ejemplo, un identificador o una fecha de alta enviados por el cliente). El sistema siempre asigna los suyos.
- **Base de datos no disponible.** Se devuelve un error genérico del servidor, como en el resto de operaciones.
- **Caracteres invisibles o de control.** Se aceptan sin tratamiento; solo se recortan los espacios en blanco de los extremos.
- **Identificadores no consecutivos.** Es compatible con el principio 5: el contador de identificadores no es un dato existente y ninguna fila se modifica.

**Desviaciones conocidas** (comportamiento real distinto de esta spec, pendientes de decisión del usuario):

- **RF-2, dato obligatorio nulo:** se rechaza como datos inválidos, pero el error lo señala como "tipo incorrecto" y no como "ausente".
- **RF-5, precio o stock no finitos (`NaN`, `Infinity`):** el valor se rechaza, pero la respuesta es un error genérico del servidor en lugar de datos inválidos, porque el error de validación no se puede devolver con ese valor. Pasa también en las demás operaciones que reciben datos.
