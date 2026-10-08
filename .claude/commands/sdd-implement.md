---
description: SDD · Implementa UNA tarea y la verifica (uso - /sdd-implement 002-nombre T-3)
argument-hint: "[NNN-nombre] [T-x]"
disable-model-invocation: true
---

Implementa SOLO la tarea $2 de `specs/$1/tasks.md` (acepta tanto "T3" como "T-3"). Sigue `specs/$1/plan.md`, docs/constitution.md, CLAUDE.md, la skill sdd (`.claude/skills/sdd/SKILL.md`) y la skill `fastapi-project` (`.claude/skills/fastapi-project/SKILL.md`).

Antes de empezar, para y avísame si:
- La tarea no existe o ya está marcada como hecha.
- Alguna tarea anterior de la que depende no está marcada como hecha.
- La tarea necesita algo que el plan no describe, o una dependencia nueva.

Pasos:
1. Implementa la tarea tocando solo los archivos que indica.
2. Comprueba que mi servidor (`uvicorn app.main:app --reload`, en http://127.0.0.1:8000) ha recogido los cambios sin errores. No lo arranques tú: si no responde, para y avísame.
3. Ejecuta la comprobación de "Hecho cuando:" y muéstrame el resultado. Usa `curl.exe -i` para lecturas y errores. Si la comprobación escribe datos, hazla dentro de una transacción que se deshace, como indica la skill sdd ("Verificar escrituras sin dejar datos"): nunca dejes registros de prueba.
4. Comprueba que `/hello-world` y `/healthz` siguen respondiendo igual.
5. Si todo está bien, marca $2 como hecha en tasks.md. Si algo falla, no la marques: explícame qué falla y por qué.
6. Actualiza MEMORY.md y resume en pocas líneas qué cambiaste, qué RF cubre la tarea y cualquier decisión que hayas tomado por tu cuenta.

No hay tests automáticos: no instales pytest ni otras herramientas (ver la constitución).

No hagas commit ni push.

Después PÁRATE. No empieces la siguiente tarea.
