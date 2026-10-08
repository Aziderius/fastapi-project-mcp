---
description: SDD · Nuevo requisito - primero la spec, luego el código (uso - /sdd-change 002-nombre descripción del cambio)
argument-hint: "[NNN-nombre] [descripción del cambio]"
disable-model-invocation: true
---

NO toques código de la aplicación. Sigue la skill sdd (`.claude/skills/sdd/SKILL.md`) y ten en cuenta docs/constitution.md y CLAUDE.md.

Argumentos recibidos: $ARGUMENTS
- La primera palabra ($1) es la carpeta de la spec: `specs/$1/`.
- Todo lo que va después es el nuevo requisito o el cambio.

Si la spec no existe o falta la descripción del cambio, pregúntamelo antes de seguir.

Tu trabajo:
1. Si el cambio es ambiguo, hazme preguntas de UNA en UNA (máximo 3) antes de proponer nada.
2. Propón el cambio en la spec: el RF nuevo o modificado en EARS, sus casos límite y lo que queda fuera de alcance. Un RF nuevo recibe el siguiente número libre; no renumeres los existentes, para no romper la trazabilidad con el plan y las tareas.
3. Comprueba que el cambio no contradice otros RF ni la constitución. Si lo hace, avísame.
4. Indica qué partes de `plan.md` y `tasks.md` habría que cambiar después, y si alguna tarea ya hecha se ve afectada.
5. Muéstrame el cambio propuesto como diff y espera mi aprobación.

Solo cuando lo apruebe:
- Aplica el cambio en `specs/$1/spec.md` y pon su estado en "borrador" hasta que vuelva a aprobarla.
- Actualiza MEMORY.md.
- Indícame el siguiente comando: normalmente `/sdd-clarify $1` y después `/sdd-plan $1`.

No modifiques el plan ni las tareas: eso se hace en sus propias fases.
