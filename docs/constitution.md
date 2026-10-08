# Constitución de la API

Principios innegociables del proyecto. Las reglas operativas están en `CLAUDE.md`; si chocan, manda esta constitución.

1. **Stack mínimo.** Python ≥ 3.12, FastAPI, SQLAlchemy 2.0 async, asyncpg, PostgreSQL y pydantic-settings. Las dependencias directas son solo las de `requirements.txt`, fijadas con `==`. Añadir una tecnología requiere aprobación explícita y actualizar este principio en el mismo cambio.
2. **La spec va antes que el código.** Cada endpoint tiene su sección en `README.md` (ruta, cuerpo, respuestas y códigos de estado) antes de implementarse. Si el código y la spec no coinciden, es un defecto y se corrige en el mismo cambio. Nunca se deja que diverjan.
3. **Cada capa tiene una sola responsabilidad.** `routers`: HTTP y consultas con la sesión inyectada. `schemas`: validar la entrada y la salida. `models`: describir las tablas existentes. `database`: el motor y las sesiones. `core`: la configuración. Las importaciones solo bajan: `routers → schemas/models/database → core`. Ninguna capa importa de `routers`, y `main.py` solo registra routers.
4. **Verificación con lo que ya existe.** Un cambio está terminado cuando el servidor arranca sin errores, cada endpoint afectado responde lo esperado con `Invoke-RestMethod` (casos de éxito y de error) y aparece en `/docs`. Las escrituras se verifican dentro de una transacción que se deshace. Añadir pytest u otra herramienta requiere aprobación.
5. **Los datos existentes no se tocan.** Los modelos reflejan el esquema real. Nada crea, altera ni vacía tablas, ni deja datos de prueba. Las credenciales viven solo en `.env`, que no se lee, no se versiona y no aparece en logs.
6. **Español para las personas, inglés para el código.** Los identificadores van en inglés. Los comentarios, los docstrings, los `detail` que escribe el proyecto y la documentación van en español.
