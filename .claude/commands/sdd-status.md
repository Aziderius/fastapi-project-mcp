---
description: SDD · Dónde estamos - fase actual y siguiente paso de una spec (uso - /sdd-status 002-nombre, o sin argumentos para ver todas)
argument-hint: "[NNN-nombre opcional]"
disable-model-invocation: true
---

No modifiques ningún archivo. Sigue la skill sdd (`.claude/skills/sdd/SKILL.md`).

Spec indicada: $ARGUMENTS

Si no se indica ninguna spec, lista todas las carpetas de `specs/` con su nombre, su estado y su fase actual en una línea cada una, y para.

Si se indica una, lee `specs/$1/` (spec.md, plan.md y tasks.md, los que existan) y MEMORY.md, y dime en pocas líneas:
1. En qué fase del flujo SDD está la spec y su estado (borrador, aprobada o implementada).
2. Tareas hechas y pendientes (x de y), si existe tasks.md.
3. Bloqueos: marcas [NECESITA ACLARACIÓN], [REVISAR SPEC] o [REVISAR PLAN] sin resolver, o incoherencias entre los archivos (por ejemplo, tareas hechas con la spec en borrador).
4. El siguiente paso exacto, con el comando `/sdd-*` que debo ejecutar y sus argumentos.
