---
name: sdd
description: Úsala siempre que trabajes con Spec-Driven Development en este proyecto (docs/constitution.md o cualquier archivo dentro de specs/): redactar, revisar o cambiar specs, planes y tareas, o implementar y validar tareas de una spec.
---

# Spec-Driven Development (SDD)

## Flujo

Constitución → Spec → Clarificación → Plan → Tareas → Implementación → Validación → Cambio.

- Nunca pases a la siguiente fase sin la aprobación explícita del usuario.
- La spec manda: si algo no está en la spec, no se implementa. Si falta una decisión, para y pregunta.
- Un cambio de requisitos se hace primero en la spec, luego en el plan y las tareas, y por último en el código.
- Cada spec vive en su carpeta: `specs/NNN-nombre/` con `spec.md`, `plan.md` y `tasks.md`.
- No modifiques una fase anterior desde una posterior: marca los problemas como [REVISAR SPEC] o [REVISAR PLAN] y pregunta.
- Al terminar cada fase, actualiza `MEMORY.md`.

## Plantilla de spec (spec.md)

```
# Spec NNN — <nombre de la funcionalidad>
Estado: borrador | aprobada | implementada

## Contexto y objetivo
## Usuarios
## Historias de usuario
- HU-1. Como <tipo de usuario>, quiero <acción> para <beneficio>.
## Definiciones (solo si hay términos que puedan interpretarse de varias formas)
## Requisitos funcionales
## Requisitos no funcionales
## Casos límite
## Fuera de alcance
## Criterios de finalización
## Dudas abiertas
- [NECESITA ACLARACIÓN] <pregunta>
```

La spec describe el QUÉ y el POR QUÉ. Nada de tecnologías, arquitectura, rutas, tablas ni nombres de archivos. Sí se describe el comportamiento observable para quien usa la API: qué datos envía, qué recibe si todo va bien y qué tipo de error recibe si algo falla (no encontrado, duplicado, datos inválidos).

## Requisitos en EARS (en español)

- RF-x: CUANDO <evento>, EL SISTEMA <respuesta>.
- RF-x: SI <condición no deseada>, ENTONCES EL SISTEMA <respuesta>.
- RF-x: MIENTRAS <estado>, EL SISTEMA <respuesta>.
- RF-x: EL SISTEMA <comportamiento que se cumple siempre>.

Cada RF debe ser verificable: nada de "rápido", "correcto" o "claro" sin un criterio medible.

## Plan (plan.md)

1. Resumen técnico (3-4 líneas).
2. Verificación de la constitución: una línea por principio.
3. Contrato de la API: método, ruta, entrada con validaciones, respuesta de éxito y cada error con su código y mensaje en español.
4. Cambios por archivo, descritos en palabras, sin código.
5. Decisiones técnicas, cada una con su porqué y la alternativa descartada.
6. Trazabilidad: tabla RF → archivos → prueba que lo verifica.
7. Plan de verificación manual con comandos concretos para cada caso de éxito y de error: `curl.exe -i` o `Invoke-RestMethod` para lecturas y errores, y el script de "Verificar escrituras sin dejar datos" para los casos que escriben.
8. Riesgos y documentación a actualizar (CLAUDE.md, MEMORY.md, README.md).

Si la spec tiene [NECESITA ACLARACIÓN] sin resolver, no se genera el plan.

## Tareas (tasks.md)

```
- [ ] **T-x: <título corto>**
  - RF: RF-x, RF-y (o "—" si es de preparación o documentación)
  - Archivos: <archivos que toca>
  - Hecho cuando: <comprobación verificable, por ejemplo un Invoke-RestMethod con su respuesta esperada>
```

- Máximo 20-30 minutos por tarea y, en lo posible, un solo archivo.
- En orden de dependencia. Después de cada tarea, la app arranca y los endpoints existentes siguen funcionando.
- Al final, una tarea de verificación completa y otra de documentación, más una tabla RF → tareas.
- Si salen más de 10 tareas, propón dividir la spec.

## Implementación

Una sola tarea cada vez:
1. Implementa la tarea siguiendo el plan, CLAUDE.md y la skill `fastapi-project`.
2. Usa el servidor que el usuario tiene arrancado con `uvicorn app.main:app --reload` en http://127.0.0.1:8000: recoge los cambios solo. No lo arranques tú (no termina y bloquea tu trabajo). Si no responde, para y avisa.
3. Ejecuta la comprobación de "Hecho cuando" (las escrituras, como se explica en "Verificar escrituras sin dejar datos").
4. Comprueba que `/hello-world` y `/healthz` siguen respondiendo.
5. Marca el checkbox y resume en pocas líneas qué hiciste.

Entre tareas:
- Con los comandos manuales (`/sdd-implement`), para después de cada tarea hasta que el usuario apruebe la siguiente.
- Con el agente coordinator, las tareas se encadenan sin pedir aprobación mientras todas pasen su "Hecho cuando"; ante cualquier fallo, bloqueo o pregunta, se para y se avisa al usuario.

No hay tests automáticos: no instales pytest ni otras herramientas sin aprobación (ver la constitución).

## Verificar escrituras sin dejar datos

Los principios 4 y 5 de la constitución exigen verificar las escrituras dentro de una transacción que se deshace y no dejar datos de prueba. Nunca se crean registros reales para verificar, ni siquiera con permiso del usuario.

- Lecturas y errores que no escriben (404, 409, 422…): `curl.exe -i` contra el servidor del usuario (en Bash vale `curl -i`; en PowerShell 5.1 `curl` es un alias de `Invoke-WebRequest`, usa siempre `curl.exe`).
- Casos que escriben (201 de un `POST`, y lo que se lea después dentro de la misma prueba): un script temporal de Python **fuera del repositorio**, ejecutado con el `.venv` desde la raíz del proyecto, que:
  1. Abre una conexión con `engine.connect()` e inicia una transacción externa.
  2. Sustituye `get_db` con `app.dependency_overrides` por una `AsyncSession(bind=conexión, join_transaction_mode="create_savepoint", expire_on_commit=False)`.
  3. Arranca la app con `uvicorn.Server` en el puerto 8002 dentro del propio script, hace las peticiones (por ejemplo con `urllib.request` en un hilo) y después pone `server.should_exit = True`.
  4. Deshace la transacción externa con `rollback` y cierra el motor con `engine.dispose()`.
- Al terminar, comprueba con una consulta de solo lectura que el número de filas no ha cambiado.
- Los identificadores que consumen estas pruebas no vuelven atrás: es un efecto aceptado y no cuenta como modificar datos.

## Validación

Al terminar todas las tareas, ejecuta el plan de verificación completo (las escrituras, dentro de una transacción que se deshace), comprueba cada criterio de finalización de la spec y cambia su estado a "implementada" solo cuando el usuario lo apruebe.

## Commits

Nunca hagas commit ni push en ninguna fase: los cambios se dejan sin confirmar hasta que el usuario lo pida explícitamente (CLAUDE.md).
