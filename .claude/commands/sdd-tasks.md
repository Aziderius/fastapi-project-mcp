---
description: SDD · Divide el plan en tareas pequeñas y verificables (uso - /sdd-tasks 002-nombre)
argument-hint: "[NNN-nombre]"
disable-model-invocation: true
---

NO escribas código de la aplicación en ningún momento. A partir de `specs/$1/spec.md` y `specs/$1/plan.md`, genera `specs/$1/tasks.md` siguiendo el formato de tareas de la skill sdd (`.claude/skills/sdd/SKILL.md`). Ten en cuenta también docs/constitution.md y CLAUDE.md.

Para y avísame, sin generar nada, si:
- Falta la spec o el plan.
- El plan tiene marcas [REVISAR SPEC] sin resolver.
- `specs/$1/tasks.md` ya existe (no lo sobrescribas sin mi permiso).

Reglas para las tareas:
- Máximo 20-30 minutos cada una y, en lo posible, un solo archivo.
- En orden de dependencia: ninguna tarea puede necesitar algo de una tarea posterior.
- Cada una con checkbox, los RF que cubre, los archivos que toca y una línea "Hecho cuando:" verificable con lo que ya existe (un `Invoke-RestMethod` con su respuesta esperada, o que el servidor arranque y el endpoint aparezca en `/docs`).
- Después de cada tarea, la app debe seguir arrancando y los endpoints existentes deben seguir funcionando.
- Al final, una tarea de verificación completa con todas las pruebas del plan, otra para actualizar CLAUDE.md, MEMORY.md y README.md, y una tabla RF → tareas que demuestre que todos los RF están cubiertos.
- Sigue el plan: no añadas tareas que el plan no justifique. Si encuentras un hueco o una contradicción, márcalo como [REVISAR PLAN].
- Intenta que no sean más de 10. Si salen más, no generes el archivo: propón cómo dividir la spec.

No modifiques la spec ni el plan. Al terminar, actualiza MEMORY.md, muéstrame la lista de tareas y espera mi aprobación.
