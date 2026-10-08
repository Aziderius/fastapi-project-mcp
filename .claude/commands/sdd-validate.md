---
description: SDD · Valida la spec RF por RF contra la API en marcha (uso - /sdd-validate 002-nombre)
argument-hint: "[NNN-nombre]"
disable-model-invocation: true
---

Valida `specs/$1/spec.md` requisito por requisito. Sigue la skill sdd (`.claude/skills/sdd/SKILL.md`), `specs/$1/plan.md` (sobre todo su plan de verificación) y docs/constitution.md.

Antes de empezar, para y avísame si:
- Falta la spec, el plan o las tareas.
- Quedan tareas sin marcar como hechas en `specs/$1/tasks.md`.
- Mi servidor no responde en http://127.0.0.1:8000. No lo arranques tú: avísame.

Datos de prueba (principios 4 y 5 de la constitución):
- Las comprobaciones que escriben datos se ejecutan dentro de una transacción que se deshace al final, como indica la skill sdd ("Verificar escrituras sin dejar datos"). Nunca crees registros reales, ni siquiera con mi permiso.
- No borres ni modifiques datos existentes. Al terminar, confirma con una consulta de solo lectura que el número de filas no ha cambiado.

Para cada RF:
1. Indica qué prueba del plan de verificación lo cubre.
2. Ejecútala y muestra la respuesta obtenida y la esperada. Para comprobar códigos de error (404, 409, 422…), usa `curl.exe -i`, porque `Invoke-RestMethod` lanza una excepción en las respuestas de error y oculta el código.
3. Marca el resultado: ✅ cumple, ❌ falla o ⚠️ sin prueba que lo cubra.

Después:
- Comprueba que `/hello-world`, `/healthz` y los endpoints que ya existían siguen respondiendo igual.
- Revisa cada criterio de finalización de la spec y marca si se cumple.
- Dame un veredicto: ¿la spec está cumplida? Si lo está, propón cambiar su estado a "implementada", pero no lo cambies sin mi aprobación.

NO arregles nada. Si algo falla o falta, dilo claramente e indica qué fase habría que revisar (spec, plan o implementación). No hagas commit ni push.
