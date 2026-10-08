---
description: SDD · Genera el plan técnico de una spec aprobada (uso - /sdd-plan 002-nombre)
argument-hint: "[NNN-nombre]"
disable-model-invocation: true
---

NO escribas código de la aplicación en ningún momento. Vamos a generar el plan técnico de `specs/$1/spec.md`. Sigue las reglas de la skill sdd (`.claude/skills/sdd/SKILL.md`).

Lee, en este orden: `specs/$1/spec.md`, docs/constitution.md, CLAUDE.md, MEMORY.md, la skill `fastapi-project` (`.claude/skills/fastapi-project/SKILL.md`) y el código actual de `app/`.

Para y avísame, sin generar nada, si:
- La spec no existe o su estado no es "aprobada".
- La spec tiene dudas marcadas como [NECESITA ACLARACIÓN].
- La spec contradice la constitución.
- `specs/$1/plan.md` ya existe (no lo sobrescribas sin mi permiso).

Si todo está en orden, genera `specs/$1/plan.md` con la estructura de la skill sdd:
1. Resumen técnico.
2. Verificación de la constitución, una línea por principio.
3. Contrato de la API: método, ruta, entrada con validaciones, respuesta de éxito y cada error con su código y mensaje en español.
4. Cambios por archivo, descritos en palabras, sin código.
5. Decisiones técnicas con su porqué y la alternativa descartada. Ten en cuenta las trampas de la skill `fastapi-project`: errores de integridad que hay que distinguir entre sí, relaciones `lazy="raise"` y `refresh` que no recarga relaciones.
6. Trazabilidad: tabla RF → archivos → prueba que lo verifica. Todos los RF deben aparecer.
7. Plan de verificación manual con comandos concretos para cada caso de éxito y de error: `curl.exe -i` o `Invoke-RestMethod` para lecturas y errores, y el script de transacción deshecha de la skill sdd para los casos que escriben datos.
8. Riesgos y documentación a actualizar.

Reglas:
- No modifiques la spec. Si encuentras un error o un hueco, márcalo en el plan como [REVISAR SPEC].
- No añadas nada que la spec no pida, ni dependencias nuevas.
- No dividas el trabajo en tareas: eso es el siguiente paso.

Al terminar, actualiza MEMORY.md, muéstrame un resumen del plan y espera mi aprobación.
