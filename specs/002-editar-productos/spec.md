# Spec 002 — Editar productos
Estado: implementada (2026-10-08)

**Fecha:** 2026-10-08 · **Depende de:** spec 001 (crear productos), en estado "implementada".

## Contexto y objetivo

Hoy los productos del catálogo se pueden consultar (el listado o uno concreto) y crear (spec 001), pero no modificar. Si un precio, un stock o una categoría cambian, la única forma de reflejarlo es tocar la base de datos a mano.

**Objetivo:** permitir modificar un producto existente desde la API sustituyendo todos sus datos editables, con las mismas validaciones de datos y los mismos mensajes que al crearlo, e impidiendo que un cambio de nombre repita el nombre de otro producto.

**Por qué:** es el siguiente paso natural para gestionar el catálogo desde la propia API y, en un proyecto educativo, enseña la diferencia entre crear un recurso y sustituir uno que ya existe. Además, corrige un defecto conocido: consultar un producto con un identificador enorme devuelve hoy un error del servidor en lugar de "no encontrado".

## Usuarios

- **Quien gestiona el catálogo:** corrige o actualiza los datos de productos existentes.
- **Quien integra la API** (una aplicación cliente, un panel de administración): necesita que crear y modificar validen igual los mismos datos y que las diferencias entre ambas operaciones estén documentadas.
- **Quien aprende con el proyecto:** usa esta operación como referencia de una sustitución completa.

En esta versión no hay control de acceso: cualquiera que pueda llamar a la API puede modificar productos.

## Historias de usuario

- **HU-1.** Como gestor del catálogo, quiero sustituir los datos de un producto existente (nombre, descripción, precio, stock y categoría), para mantener el catálogo al día sin tocar la base de datos.
- **HU-2.** Como gestor del catálogo, quiero cambiar un producto de categoría, para reorganizar el catálogo.
- **HU-3.** Como gestor del catálogo, quiero recibir el producto completo tras modificarlo, para confirmar al instante qué quedó guardado.
- **HU-4.** Como integrador, quiero que las validaciones de cada dato y sus mensajes de error sean los mismos que al crear un producto, para reutilizar la misma lógica en el cliente.
- **HU-5.** Como integrador, quiero recibir "no encontrado" para cualquier identificador de producto que no exista, incluidos los enormes (dentro del límite de cifras indicado en "Desviaciones conocidas aceptadas"), para no tratar errores del servidor que no son culpa mía.
- **HU-6.** Como gestor del catálogo, quiero que al renombrar un producto no pueda darle el nombre de otro producto, aunque solo se diferencien en mayúsculas o tildes, para no introducir nombres repetidos nuevos en el catálogo.

## Definiciones

- **Espacio en blanco, longitud y error de datos inválidos:** con el mismo significado que en la spec 001 (sección 4, "Definiciones usadas en los requisitos").
- **Datos editables:** nombre, descripción, precio, stock e identificador de categoría.
- **Datos fijos:** identificador del producto y fecha y hora de alta. Nunca cambian.
- **Sustitución completa:** la modificación reemplaza todos los datos editables a la vez con los valores enviados. Lo que no se envía no conserva su valor anterior: si es obligatorio, es un error; si es la descripción, queda nula.
- **Número entero admitido:** un número entero de hasta 4 000 cifras, positivo, 0 o negativo. Los requisitos sobre identificadores enormes se garantizan dentro de ese límite (ver "Desviaciones conocidas aceptadas" para los más largos).
- **Producto inexistente:** un identificador de la petición que es un número entero admitido y no corresponde a ningún producto.
- **Identificador en los mensajes (`{id}`):** el número entero tal como el sistema lo ha interpretado, escrito en su forma decimal habitual (sin ceros a la izquierda, sin signo `+` y con `-0` como `0`), no el texto exacto que envió el cliente. Por ejemplo, si el identificador del producto llega como `05`, el mensaje dice `id 5`.
- **Valor no finito:** `NaN`, `Infinity`, `-Infinity` o un número tan grande que se lee como infinito (por ejemplo, `1e400`).
- **Nombres equivalentes:** dos nombres son equivalentes si coinciden después de quitar los espacios en blanco de los extremos de ambos y comparándolos con estas reglas, que se aplican letra a letra:
  - No se distinguen mayúsculas de minúsculas solo en las letras del alfabeto español: de la A a la Z, la Ñ, las vocales con tilde (á, é, í, ó, ú) y la ü.
  - No se distinguen las vocales con tilde (á, é, í, ó, ú) ni la ü de la vocal sin marca: `Camión`, `Camion` y `CAMION` son equivalentes; `pingüino` y `PINGUINO` también.
  - La ñ es una letra distinta de la n: `Año` y `Ano` no son equivalentes (`Año` y `AÑO` sí).
  - Una misma letra escrita en dos formas internas distintas (por ejemplo, la `ó` como un solo carácter o como `o` seguida de la tilde) cuenta como la misma letra. Esto incluye los signos que Unicode declara oficialmente equivalentes a una letra: el signo kelvin (`K`) cuenta como la letra `K`, el signo ohmio (`Ω`) como la letra griega `Ω` y el signo ångström (`Å`) como la letra `Å`.
  - Cualquier otro carácter se compara tal cual, sin más equivalencias: otras letras con marca (`à`, `ç`, `ö`) no se igualan a la letra sin marca ni entre su mayúscula y su minúscula (`À` y `à` son distintas), una letra nunca equivale a varias (`ß` no equivale a `SS` ni a `ss`) y los caracteres que solo se parecen (letras de otros alfabetos, ligaduras, letras de ancho completo) son distintos.
  - Los espacios internos sí cuentan: `Teclado  mecánico` (doble espacio) y `Teclado mecánico` no son equivalentes.
- **Cambio de nombre:** la modificación cambia el nombre si el nombre recibido no es equivalente al que tiene guardado el producto. Cambiar solo mayúsculas, tildes, la forma interna de una letra o los espacios de los extremos no es un cambio de nombre.
- **Datos normalizados:** los datos recibidos después de aplicar las reglas de la spec 001 (nombre y descripción recortados, descripción vacía como nula, precio con 2 decimales). El nombre se guarda tal como se envió una vez recortado: la equivalencia de nombres solo sirve para comparar y no unifica mayúsculas ni tildes al guardar.

## Requisitos funcionales

Notación EARS: *EL SISTEMA DEBERÁ…* (siempre), *CUANDO…* (evento), *SI… ENTONCES…* (situación no deseada).

**RF-1. Modificación de un producto.**
- CUANDO se envía una petición de modificación de un producto existente con datos válidos, una categoría existente y un nombre que no repite el de otro producto (RF-12), EL SISTEMA DEBERÁ sustituir todos sus datos editables por los datos normalizados recibidos y responder con la respuesta de éxito estándar, que es distinta de la de recurso creado que usa la creación (spec 001, RF-1).
- CUANDO se modifica un producto, EL SISTEMA DEBERÁ mostrar los datos nuevos de inmediato en la consulta individual y en el listado, sin cambiar su posición en el listado.

**RF-2. Datos de entrada (sustitución completa).**
- EL SISTEMA DEBERÁ exigir los mismos datos que al crear un producto (spec 001, RF-2): **nombre**, **precio**, **stock** e **identificador de categoría** obligatorios, y **descripción** opcional.
- SI un dato obligatorio no se envía o se envía con valor nulo, ENTONCES EL SISTEMA DEBERÁ responder con un error de datos inválidos y no modificar el producto.
- EL SISTEMA DEBERÁ dejar nula la descripción del producto cuando la petición no la incluya, la envíe nula o su longitud sea 0, aunque el producto tuviera antes una descripción.
- SI el cuerpo de la petición falta, no es un objeto con datos (por ejemplo, es una lista o un texto) o no se puede interpretar, ENTONCES EL SISTEMA DEBERÁ responder con un error de datos inválidos.
- SI un dato aparece repetido en el cuerpo de la petición, ENTONCES EL SISTEMA DEBERÁ usar el último valor recibido.

**RF-3. Validaciones idénticas a las de la creación.**
- EL SISTEMA DEBERÁ aplicar al nombre, la descripción, el precio y el stock las mismas reglas que al crear un producto (spec 001, RF-3 a RF-6): mismos recortes de espacios en blanco, mismas longitudes máximas (150 y 255), mismos límites de precio (mayor que 0, como máximo 2 decimales significativos y menor que 100 000 000) y de stock (entero de 0 a 2 147 483 647), y el mismo tipo de error de datos inválidos. Las únicas excepciones son las desviaciones conocidas de los valores no finitos y de los números demasiado largos (ver "Desviaciones conocidas aceptadas").
- SI el precio o el stock se envían como texto, el stock como decimal (`5.0`) o cualquiera de ellos como `true`/`false`, ENTONCES EL SISTEMA DEBERÁ responder con un error de datos inválidos (solo se aceptan números de verdad, como en la spec 001).
- CUANDO se modifica un producto, EL SISTEMA DEBERÁ conservar el precio exacto y devolverlo con exactamente 2 decimales y el mismo formato que en la consulta (por ejemplo, `"19.90"`).

**RF-4. Cambio de categoría.**
- CUANDO se envía un identificador de categoría existente distinto del actual, EL SISTEMA DEBERÁ mover el producto a esa categoría.
- SI el identificador de categoría no es un número entero (incluidos `true`/`false`, decimales como `1.5` y textos como `"2"`), ENTONCES EL SISTEMA DEBERÁ responder con un error de datos inválidos de formato, salvo en los casos de las desviaciones conocidas (valores no finitos y números demasiado largos).
- SI el identificador de categoría es un número entero admitido que no corresponde a ninguna categoría existente, ENTONCES EL SISTEMA DEBERÁ responder con un error de datos inválidos con el mensaje en español `No existe ninguna categoría con el id {id}` (el mismo de la spec 001, RF-7) y no modificar el producto.
- SI la categoría nueva deja de existir entre la comprobación y el final de la modificación, ENTONCES EL SISTEMA DEBERÁ responder con el mismo error de categoría inexistente y no modificar el producto.

**RF-5. Producto inexistente.**
- SI el identificador del producto que se quiere modificar es un producto inexistente (incluidos 0, negativos e identificadores fuera del rango de un entero, como `99999999999999999999` o `-99999999999999999999`), ENTONCES EL SISTEMA DEBERÁ responder con un error de "no encontrado" con el mensaje en español `No existe ningún producto con el id {id}` (el mismo que la consulta individual de productos), y nunca con un error del servidor.
- SI el identificador del producto no es un número entero (por ejemplo, `abc` o `1.5`), ENTONCES EL SISTEMA DEBERÁ responder con un error de datos inválidos de formato.
- EL SISTEMA DEBERÁ interpretar el identificador del producto de la petición exactamente igual que la consulta individual de productos: acepta las mismas formas de escribir un entero y obtiene el mismo número (ver "Desviaciones conocidas aceptadas").

**RF-6. Datos fijos.**
- EL SISTEMA NO DEBERÁ cambiar nunca el identificador ni la fecha y hora de alta de un producto.
- EL SISTEMA DEBERÁ ignorar el identificador, la fecha de alta y cualquier otro dato no previsto que llegue en el cuerpo de la petición, sea cual sea su valor (incluidos valores con un formato que no sería válido, como un identificador `"abc"` o una fecha nula) y también si ese identificador no coincide con el del producto que se modifica. Los valores no finitos en estos datos siguen la desviación conocida correspondiente.

**RF-7. Respuesta.**
- CUANDO se modifica un producto, EL SISTEMA DEBERÁ devolverlo completo y con la misma forma que la consulta individual: identificador, nombre, descripción, precio, stock, identificador de categoría, la categoría (identificador y nombre, ya la nueva si ha cambiado) y la fecha de alta original.
- SI los datos normalizados recibidos coinciden con los que ya tiene guardados el producto, ENTONCES EL SISTEMA DEBERÁ responder con el mismo éxito y el producto sin cambios.
- SI los datos guardados de un producto no cumplen las reglas de la spec 001 (por ejemplo, un nombre con espacios en los extremos), ENTONCES EL SISTEMA DEBERÁ tratar una petición que reenvía esos datos igual que una creación con ellos: los guarda normalizados o responde con un error de datos inválidos.

**RF-8. Modificaciones simultáneas (limitación conocida, no verificada).**
- CUANDO llegan dos modificaciones válidas del mismo producto a la vez, EL SISTEMA DEBERÁ aplicar ambas por completo, una después de la otra, de modo que el producto quede con todos los datos de la última que termine (nunca una mezcla de las dos).

**RF-9. Sin efectos parciales.**
- SI la petición termina en cualquier error, ENTONCES EL SISTEMA NO DEBERÁ modificar el producto ni ningún otro producto o categoría.
- EL SISTEMA DEBERÁ modificar como máximo un producto por petición.

**RF-10. Corrección de la consulta individual de productos (defecto existente).**
- SI se consulta un producto concreto con un número entero admitido que no corresponde a ningún producto (incluidos los que quedan fuera del rango de un entero, como `99999999999999999999` o `-99999999999999999999`), ENTONCES EL SISTEMA DEBERÁ responder con el error de "no encontrado" `No existe ningún producto con el id {id}`, y nunca con un error del servidor. Hoy los identificadores fuera de rango responden con un error del servidor: es un defecto que esta spec corrige.
- EL SISTEMA DEBERÁ mantener sin cambios el resto del comportamiento de la consulta individual de productos, incluidas las formas de escribir el identificador que acepta hoy.

**RF-11. Orden de los errores en la modificación.**
- SI el cuerpo de la petición no se puede interpretar (está mal formado), ENTONCES EL SISTEMA DEBERÁ responder con un error de datos inválidos que informe solo de ese error de formato, sin informar del identificador del producto ni comprobar si el producto o la categoría existen.
- SI el cuerpo se puede interpretar y el identificador del producto o algún dato del cuerpo tienen un formato inválido (incluido un cuerpo ausente o que no es un objeto), ENTONCES EL SISTEMA DEBERÁ responder con un único error de datos inválidos que informe de todos esos errores de formato juntos, sin comprobar si el producto o la categoría existen.
- SI todos los datos tienen un formato válido y el producto es inexistente, ENTONCES EL SISTEMA DEBERÁ responder con el error de "no encontrado" de RF-5, sin comprobar la categoría ni el nombre.
- SI todos los datos tienen un formato válido, el producto existe y la categoría no existe, ENTONCES EL SISTEMA DEBERÁ responder con el error de categoría inexistente de RF-4, sin comprobar el nombre.
- SI todos los datos tienen un formato válido, el producto y la categoría existen y el nombre repite el de otro producto, ENTONCES EL SISTEMA DEBERÁ responder con el error de duplicado de RF-12.

**RF-12. Nombres repetidos al modificar.**
- SI la modificación cambia el nombre del producto y el nombre recibido es equivalente al de cualquier otro producto, de cualquier categoría, ENTONCES EL SISTEMA DEBERÁ responder con un error de duplicado con el mensaje en español `Ya existe otro producto con el nombre {nombre}`, donde `{nombre}` es el nombre recibido ya recortado (con sus mayúsculas y tildes tal como se envió), y no modificar el producto.
- SI la modificación no cambia el nombre del producto, ENTONCES EL SISTEMA DEBERÁ aceptarlo sin comprobar repetidos, aunque ese nombre ya esté repetido en otros productos, y guardar el nombre recibido recortado tal como se envió (por ejemplo, `Camion` pasa a `Camión` si se envía `Camión`).
- EL SISTEMA DEBERÁ seguir permitiendo nombres repetidos al crear productos (spec 001, RF-8, sin cambios). Esta regla solo se aplica a la modificación.

**RF-13. Base de datos no disponible.**
- SI la base de datos no está disponible al modificar un producto, ENTONCES EL SISTEMA DEBERÁ responder con un error genérico del servidor y no modificar nada, como en el resto de operaciones (spec 001, sección 9).

## Requisitos no funcionales

- **RNF-1. Coherencia con la creación.** Ante los mismos datos del cuerpo, la modificación valida cada dato exactamente igual que la creación (spec 001), con los mismos mensajes propios. Las diferencias, todas documentadas en esta spec, son: la respuesta de éxito (estándar en lugar de recurso creado, RF-1), el identificador del producto en la petición y sus errores (formato y "no encontrado", RF-5), el orden de los errores (RF-11), el rechazo de nombres repetidos cuando el nombre cambia (RF-12) y que un cuerpo mal formado se informa solo (RF-11).
- **RNF-2. Coherencia con la consulta.** Un producto recién modificado es indistinguible, en forma y formato, de uno consultado después.
- **RNF-3. Idioma.** Los mensajes de error que escribe el proyecto van en español (principio 6 de la constitución). Los mensajes automáticos de validación de formato pueden ir en inglés, como en la spec 001.
- **RNF-4. Integridad de los datos existentes.** La funcionalidad no altera la estructura del almacenamiento. Solo modifica el producto indicado en la petición.
- **RNF-5. Sin cambios en lo que ya existe.** Las operaciones actuales (listar productos, crear productos, consultar, listar y crear categorías, y comprobar el estado) responden exactamente igual que antes; en particular, crear un producto con un nombre repetido sigue funcionando. La consulta individual de productos solo cambia en lo que indica RF-10.

## Casos límite

| Caso | Resultado esperado |
|---|---|
| Modificación válida de un producto existente | Éxito; se devuelve el producto con los datos nuevos, el mismo identificador y la misma fecha de alta. |
| Mismos datos que ya tiene el producto | Éxito; producto sin cambios. |
| Producto guardado con datos que no cumplen las reglas (por ejemplo, nombre con espacios en los extremos) y petición que los reenvía | Igual que al crear: se guardan normalizados o datos inválidos (RF-7). |
| Producto con descripción y petición sin descripción, con `null`, `""` o `"   "` | Éxito; la descripción queda nula. |
| Petición sin nombre, precio, stock o categoría (por ejemplo, solo `{"price": 10}`) | Datos inválidos; el producto no cambia. |
| Nombre `"  Teclado  "` | Se guarda como `"Teclado"`. |
| Nombre vacío, de 151 caracteres tras recortar, numérico o nulo | Datos inválidos. |
| Descripción de 256 caracteres tras recortar | Datos inválidos. |
| Precio `0.01`, `99999999.99`, `19.900` o `1e2` | Éxito (`"0.01"`, `"99999999.99"`, `"19.90"`, `"100.00"`). |
| Precio `0`, `-0`, `-5`, `0.001`, `100000000` o `"19.90"` (texto) | Datos inválidos. |
| Valor no finito (`NaN`, `Infinity` o `1e400`) en el precio, el stock, la categoría, el nombre o la descripción | El producto no cambia; la respuesta puede ser un error genérico del servidor en lugar de datos inválidos (desviación conocida, igual que al crear). |
| Valor no finito en un dato no previsto (por ejemplo, `"id": NaN`) | Si la respuesta es un error del servidor, el producto no cambia; si no, es la que corresponde al resto del cuerpo (por ejemplo, éxito ignorando ese dato) (desviación conocida). |
| Stock `0` | Éxito (producto agotado). |
| Stock `-1`, `1.5`, `5.0`, `"5"`, `true` o `2147483648` | Datos inválidos. |
| Categoría existente distinta de la actual | Éxito; la respuesta muestra la nueva categoría (identificador y nombre). |
| Categoría `1.5`, `"2"`, `true`, `false` o nula | Datos inválidos de formato. |
| Categoría `999`, `0`, `-3`, `100000000000000000000` o `-100000000000000000000` | Datos inválidos, `No existe ninguna categoría con el id {id}`; el producto no cambia. |
| Categoría, precio o stock con más de 4 000 cifras | No se garantiza la respuesta de RF-4 ni de RF-11, pero el producto no cambia (desviación conocida: a partir de unas 4 300 cifras, en cualquier dato del cuerpo, el cuerpo no se puede leer y la respuesta es un error de petición incorrecta). |
| Precio inválido **y** categoría inexistente | Solo se informa del precio. |
| Precio inválido **y** stock inválido | Se informan ambos en la misma respuesta. |
| La categoría nueva ya no existe al llegar la petición (se borró antes) | Datos inválidos, `No existe ninguna categoría con el id {id}`; el producto no cambia. |
| La categoría nueva se borra durante la modificación, entre la comprobación y el guardado (solo es posible si no tiene productos) | Datos inválidos, `No existe ninguna categoría con el id {id}`; el producto no cambia (limitación conocida, no verificada). |
| La categoría actual del producto | No puede desaparecer durante la modificación: mientras el producto le pertenezca, no se puede borrar. |
| Producto `999` (inexistente), `0` o `-1` | No encontrado, `No existe ningún producto con el id {id}`. |
| Producto `99999999999999999999` o `-99999999999999999999` (fuera del rango de un entero) | No encontrado, `No existe ningún producto con el id {id}`; nunca error del servidor. |
| Producto `05` o `-0` en la petición | Se interpreta como `5` o `0`; si no existe, el mensaje dice `id 5` o `id 0`. |
| Producto `1.0`, `5_0`, `0_1` o ` 5 ` (con espacios) en la petición | Se interpreta igual que en la consulta individual actual (`1`, `50`, `1` y `5`); desviación conocida aceptada. |
| Producto con más de 4 000 cifras en la petición | No se garantiza "no encontrado" (desviación conocida: a partir de unas 4 300 cifras, datos inválidos de formato). |
| Producto `abc` o `1.5` | Datos inválidos de formato. |
| Cuerpo con `id` distinto del de la petición o con fecha de alta | Se ignoran; se modifica el producto indicado en la petición y sus datos fijos no cambian. |
| Cuerpo con datos no previstos, incluso con contenido inválido (`"id": "abc"`, `"created_at": null`) | Se ignoran; éxito si el resto es válido. |
| Respuesta de una consulta reenviada tal cual como cuerpo | Datos inválidos por el precio (llega como texto); la categoría anidada, el identificador y la fecha de alta se ignoran como datos no previstos. |
| Cuerpo ausente o que es una lista | Datos inválidos. |
| Cuerpo mal formado (por ejemplo, `{"price": 500,00}`) | Datos inválidos; solo se informa de ese error, aunque el identificador del producto también sea inválido o no exista. |
| Dato repetido en el cuerpo | Se usa el último valor. |
| Base de datos no disponible | Error genérico del servidor; nada cambia. |
| Dos modificaciones simultáneas del mismo producto | El producto queda con todos los datos de la última que termine (limitación conocida, no verificada). |
| Consulta individual del producto `99999999999999999999` o `-99999999999999999999` | No encontrado, `No existe ningún producto con el id {id}` (corrección de RF-10); nunca error del servidor. |
| Producto `999` (inexistente) **y** precio negativo | Datos inválidos del precio (RF-11); no se informa del producto. |
| Producto `999` (inexistente) con datos válidos | No encontrado. |
| Producto `999` (inexistente) con datos válidos **y** categoría inexistente | No encontrado; no se informa de la categoría. |
| Producto `abc` **y** precio negativo | Datos inválidos; se informan ambos errores de formato en la misma respuesta. |
| Producto existente con datos válidos **y** categoría inexistente | Datos inválidos, `No existe ninguna categoría con el id {id}`. |
| Nombre nuevo equivalente al de otro producto (misma u otra categoría, por ejemplo `"  TECLADO "` si existe `Teclado`) | Duplicado, `Ya existe otro producto con el nombre TECLADO`; el producto no cambia. |
| Nombre nuevo `Camión` si existe otro producto `CAMION` (o `Camion`) | Duplicado, `Ya existe otro producto con el nombre Camión`. |
| Nombre nuevo `Año` si existe otro producto `Ano` | No es equivalente (la ñ es otra letra): éxito. |
| Nombre nuevo `Straße` si existe otro producto `STRASSE` | No es equivalente (`ß` no equivale a `SS`): éxito. |
| Nombre nuevo con una `ó` escrita como `o` seguida de la tilde, si existe otro producto con la `ó` escrita como un solo carácter | Equivalente: duplicado. |
| Nombre nuevo `Kelvin` escrito con el signo kelvin (`K`), si existe otro producto `Kelvin` con la letra `K` | Equivalente (equivalencia oficial de Unicode): duplicado. || Mismo nombre que ya tiene el producto, aunque otros productos se llamen igual | Éxito. |
| Solo cambian mayúsculas, tildes o espacios de los extremos del propio nombre (`teclado` → `Teclado`, `Camion` → `Camión`) | No es un cambio de nombre: éxito, sin comprobar repetidos; se guarda el nombre enviado (`Teclado`, `Camión`). |
| Nombre `Teclado  mecánico` (doble espacio) si existe `Teclado mecánico` | No es equivalente: éxito. |
| Categoría inexistente **y** nombre repetido | Solo se informa de la categoría. |
| Crear un producto con el nombre de otro | Sigue permitido (spec 001, sin cambios). |
| Dos modificaciones simultáneas que dan a dos productos el mismo nombre nuevo | Pueden terminar ambas con éxito (limitación conocida, no verificada). |

## Fuera de alcance

- Eliminar productos (será una spec posterior).
- El comportamiento si el producto deja de existir (por ejemplo, borrado a mano en la base de datos) entre la comprobación y el final de la modificación: se definirá en la spec de eliminar productos.
- Modificación parcial, enviando solo algunos datos (posible operación futura aparte).
- Guardar la fecha y hora de la última modificación (alteraría la estructura del almacenamiento).
- Cualquier cambio en categorías, incluida la corrección del mismo defecto de identificadores enormes en la consulta individual de categorías.
- Crear el producto si no existe al intentar modificarlo.
- Modificar varios productos en una sola petición.
- Detectar conflictos entre modificaciones simultáneas (por ejemplo, con versiones): se queda la última.
- Impedir nombres repetidos al crear productos o garantizarlo en el almacenamiento (la spec 001 no cambia).
- Corregir los nombres repetidos que ya existen en los datos.
- Unificar mayúsculas, tildes o la forma interna de las letras al guardar los nombres: la equivalencia solo se usa para comparar.
- Autenticación o permisos.
- Resolver las desviaciones conocidas (nulo en un obligatorio señalado como "tipo incorrecto", valores no finitos como error del servidor, formas aceptadas del identificador en la petición y números demasiado largos): se aceptan también aquí y se tratarán en una spec propia que cubra crear, consultar y modificar a la vez (ver "Desviaciones conocidas aceptadas").

## Desviaciones conocidas aceptadas

Comportamientos heredados de las operaciones actuales (creación y consulta individual), aceptados por el usuario para esta spec, con el mismo comportamiento que ya tienen hoy. Siguen el criterio de la spec 001 de aceptar los mensajes y comportamientos automáticos de validación:

- **Dato obligatorio nulo:** se rechaza como datos inválidos, pero el error lo señala como "tipo incorrecto" y no como "ausente". Cumple RF-2 (es un error de datos inválidos y el producto no cambia).
- **Valores no finitos en cualquier dato del cuerpo, previsto o no (`NaN`, `Infinity`, `-Infinity` o `1e400`):** la respuesta puede ser un error genérico del servidor en lugar de la que fijan RF-2 a RF-6 y RF-11 (también por delante del orden de errores). Lo que sí se garantiza: (a) ningún valor no finito llega a guardarse; (b) si la respuesta es un error del servidor, el producto no cambia; (c) si no lo es, la respuesta es la que fijan los requisitos para el resto del cuerpo (por ejemplo, un dato no previsto con `NaN` se ignora). Es la única excepción a RF-3, junto con la siguiente. Al crear productos pasa lo mismo, aunque la spec 001 solo lo describe para el precio y el stock.
- **Números demasiado largos:** los requisitos sobre identificadores enormes se garantizan para números enteros de hasta 4 000 cifras. Con números más largos no se garantizan: hoy, a partir de unas 4 300 cifras, un número en el cuerpo (de cualquier dato) hace que el cuerpo no se pueda leer y la respuesta es un error de petición incorrecta (distinto de datos inválidos), y un identificador del producto en la petición da un error de datos inválidos de formato en lugar de "no encontrado". Lo que sí se garantiza: si el número de más de 4 000 cifras es el identificador del producto o un dato previsto (categoría, precio o stock), el producto no cambia; si está en un dato no previsto, se aplica RF-6 mientras el cuerpo se pueda leer.
- **Formas aceptadas del identificador del producto en la petición:** además de los enteros escritos de forma habitual (con ceros a la izquierda o signo), se aceptan como enteros un decimal con parte decimal nula (`1.0` → `1`), guiones bajos entre cifras (`5_0` → `50`, `0_1` → `1`) y espacios en los extremos (` 5 ` → `5`). Es el comportamiento actual de la consulta individual, que no cambia (RF-10), y la modificación lo comparte (RF-5). El `{id}` de los mensajes es el número interpretado.

## Limitaciones conocidas

Comportamientos que esta spec describe o acepta, pero que no se verifican porque la verificación de la constitución (una sola prueba que se deshace al terminar) no permite provocar peticiones simultáneas reales:

- **Modificaciones simultáneas del mismo producto (RF-8):** se espera que gane la última modificación completa, nunca una mezcla.
- **Nombre nuevo repetido en modificaciones simultáneas (RF-12):** RF-12 solo se garantiza entre modificaciones que no coinciden en el tiempo; dos productos distintos renombrados a la vez con nombres equivalentes pueden terminar ambos con éxito.
- **Categoría nueva borrada durante la modificación (RF-4, último punto):** se espera el error de categoría inexistente, pero solo se verifica el caso en que la categoría ya no existe al llegar la petición, no el borrado entre la comprobación y el guardado.

## Criterios de finalización

- **Antes de implementar:** la documentación del proyecto describe la nueva operación, con su cuerpo, su respuesta y sus errores (incluido el de duplicado), y recoge la corrección de la consulta individual (principio 2 de la constitución).
- Todos los criterios de RF-1 a RF-13 y los casos límite se han comprobado sin dejar datos de prueba (principios 4 y 5), **salvo las limitaciones conocidas**, que no se verifican:
  - Las modificaciones con éxito, incluida su visibilidad en el listado y en la consulta individual, se comprueban dentro de una prueba que se deshace al terminar; al final, los productos y categorías usados conservan sus datos originales.
  - Los casos que necesitan datos que hoy no existen se comprueban preparándolos dentro de esa misma prueba que se deshace: un producto guardado con datos que no cumplen las reglas (RF-7), productos con nombres repetidos o equivalentes (RF-12, incluido "mismo nombre que ya tiene el producto aunque otros se llamen igual") y nombres con tilde, ñ, `ß` o letras escritas en dos formas internas. El detalle se decide en el plan.
  - La categoría inexistente al llegar la petición (RF-4) se comprueba dentro de la prueba que se deshace con una categoría temporal sin productos, creada y eliminada solo ella antes de la petición. Esto verifica la comprobación previa, no el borrado entre la comprobación y el guardado.
  - Los errores que no modifican nada (formato, no encontrado, categoría inexistente, duplicado con datos existentes) se comprueban contra la API.
  - Las desviaciones conocidas se comprueban según lo que garantizan: con un valor no finito, el producto no cambia o la respuesta es la de los requisitos; con números de más de 4 000 cifras en el identificador o en un dato previsto, el producto no cambia; las formas aceptadas del identificador dan el mismo resultado en la modificación y en la consulta individual.
  - La base de datos no disponible se comprueba sin tocar la configuración del proyecto, como en la spec 001.
- Las operaciones existentes responden igual que antes (RNF-5), salvo la corrección de RF-10.
- La nueva operación aparece en la documentación interactiva de la API.
- La documentación del proyecto coincide con el comportamiento final (principio 2).

## Dudas abiertas

No quedan dudas abiertas ([NECESITA ACLARACIÓN]).

Resueltas con el usuario el 2026-10-08 durante el plan (correcciones de redacción que alinean el texto con lo ya aprobado; la spec sigue aprobada):

- **17. Redacción de "Nombres equivalentes".** Se igualan solo A–Z, Ñ, las vocales con tilde (á, é, í, ó, ú) y la ü; otras letras con marca (`à`, `ç`, `ö`) no se igualan a la letra sin marca ni entre su mayúscula y su minúscula (`À` ≠ `à`). Corrige la redacción anterior ("vocales con tilde o diéresis", "no se distinguen sus mayúsculas"), que contradecía la duda 15.
- **18. Signos con equivalencia oficial de Unicode.** Se acepta que el signo kelvin cuente como `K`, el signo ohmio como `Ω` y el signo ångström como `Å`, como "la misma letra en dos formas internas" (Definiciones y caso límite nuevo).

Resueltas con el usuario el 2026-10-08 al aprobar la spec (propuestas del planner confirmadas tal cual):

- **13. Texto y orden del duplicado.** `Ya existe otro producto con el nombre {nombre}`, al final del orden de errores (RF-11, RF-12).
- **14. Cambio de nombre.** Cambiar solo mayúsculas, tildes, la forma interna de una letra o los espacios de los extremos del propio nombre no es un cambio de nombre; se guarda el nombre enviado (RF-12).
- **15. Caracteres poco habituales.** La equivalencia solo se aplica al alfabeto español: `ß` ≠ `SS`; `à`, `ç`, `ö` no se igualan a la letra sin marca ni entre mayúscula y minúscula (por tanto, `À` ≠ `à`, aceptado expresamente); la misma letra en dos formas internas sí es igual; los caracteres parecidos de otros alfabetos son distintos (ver "Definiciones").
- **16. Límite de cifras.** Se garantiza hasta 4 000 cifras para los números enteros admitidos.

Resueltas con el usuario el 2026-10-08 (primera ronda):

- **1. Mensaje de "no encontrado".** Se usa el mensaje actual de la consulta individual, `No existe ningún producto con el id {id}`, también al modificar (RF-5 y RF-10).
- **2. Orden de los errores.** Formato (cuerpo e identificador juntos), después producto inexistente y por último categoría inexistente (RF-11).
- **3. Producto que desaparece durante la modificación.** Fuera de alcance hasta la spec de eliminar productos.

Resueltas con el usuario el 2026-10-08 tras la primera revisión de @reviewer:

- **4. Modificaciones simultáneas (RF-8).** Se mantiene "gana la última modificación completa, nunca una mezcla" como comportamiento esperado, anotado como limitación conocida que no se verifica.
- **5. Cuerpo mal formado (RF-11).** Se informa solo de ese error; en el resto de casos, los errores de formato del identificador y del cuerpo se informan juntos.
- **6. Nombres repetidos al modificar (RF-12).** Se rechazan como duplicado si el nombre cambia y es equivalente al de cualquier otro producto. Si el nombre no cambia, se permite. La carrera entre renombrados simultáneos es una limitación conocida. Crear sigue permitiendo repetidos. El duplicado va después de la categoría inexistente en el orden de errores, porque solo tiene sentido comprobarlo cuando la petición es aplicable (producto y categoría existen).
- **7. Consultar y reenviar.** Se rechaza como al crear: el precio en texto da datos inválidos y la categoría anidada se ignora como dato no previsto.
- **8. Datos guardados que no cumplen las reglas (RF-7).** "Los mismos datos" significa los datos normalizados; si lo guardado incumple las reglas, la modificación lo normaliza o da datos inválidos, igual que al crear.

Resueltas con el usuario el 2026-10-08 tras la segunda revisión de @reviewer (que comprobó en solo lectura que hoy hay 24 productos y 6 categorías, ninguna fila incumple las reglas, no hay nombres repetidos ni con tilde o ñ y ninguna categoría está vacía):

- **9. Valores no finitos.** La desviación conocida se amplía a cualquier dato del cuerpo, incluidos los no previstos; se resolverá en la futura spec de desviaciones.
- **10. Categoría que desaparece.** Se verifica con una categoría temporal creada y eliminada (solo ella) dentro de la prueba que se deshace; el borrado durante la modificación queda como limitación no verificada.
- **11. Nombres equivalentes.** Se ignoran mayúsculas y tildes (á, é, í, ó, ú y ü); la ñ es otra letra; las dos formas internas de una misma letra cuentan como iguales; los espacios internos cuentan.
- **12. Puntos menores (decididos por el planner).** Las formas aceptadas del identificador y el límite de cifras se describen como desviaciones conocidas heredadas; los casos que necesitan datos inexistentes hoy se preparan dentro de la prueba que se deshace; las notas que había dentro de RF-4, RF-8 y RF-12 pasan a "Limitaciones conocidas" o se eliminan por redundantes.
