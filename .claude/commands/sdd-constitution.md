---
description: SDD · Propone o revisa la constitución del proyecto (principios innegociables)
argument-hint: "[contexto adicional opcional]"
disable-model-invocation: true
---

Vamos a crear (o revisar, si ya existe) `docs/constitution.md`. Sigue las reglas de la skill sdd (`.claude/skills/sdd/SKILL.md`).

Antes de proponer nada, lee CLAUDE.md, MEMORY.md, README.md y el código de `app/`.

Contexto adicional: $ARGUMENTS

Proponme 6 principios innegociables, cortos y verificables, que cubran:
1. Simplicidad del stack: qué tecnologías forman el proyecto y qué hace falta para añadir una nueva.
2. Relación entre spec y código.
3. Separación de capas: qué responsabilidad tiene cada una (routers, schemas, models, database, core) y qué no puede hacer.
4. Política de verificación: hoy no hay tests automáticos; cómo se comprueba un cambio con lo que ya existe y qué requiere aprobación.
5. Protección de los datos: las tablas existentes, sus datos y las credenciales del `.env`.
6. Idioma del código, los comentarios, los mensajes de la API y la documentación.

Reglas:
- Máximo 15 líneas. Cada principio debe poder comprobarse mirando el código o el repositorio.
- No copies reglas de CLAUDE.md: la constitución recoge principios; CLAUDE.md, reglas operativas.
- Si la constitución ya existe, indica qué principios cambiarías y por qué.
- Si algún principio contradice el estado actual del proyecto, señálalo.

NO escribas ni modifiques ningún archivo: muéstrame la propuesta y espera mi aprobación.
