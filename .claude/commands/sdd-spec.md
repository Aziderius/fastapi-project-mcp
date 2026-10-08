---
description: SDD · Entrevista y genera la spec (uso - /sdd-spec 002-nombre idea inicial)
argument-hint: "[NNN-nombre] [idea inicial]"
disable-model-invocation: true
---

NO escribas código de la aplicación en ningún momento. Lee docs/constitution.md, CLAUDE.md y MEMORY.md, y sigue las reglas de la skill sdd (`.claude/skills/sdd/SKILL.md`). Puedes consultar el código para entender qué existe hoy, pero la spec no debe mencionarlo.

Argumentos recibidos: $ARGUMENTS
- La primera palabra ($1) es el nombre de la carpeta: `specs/$1/`.
- Todo lo que va después es la idea inicial.

Si falta la idea inicial o el nombre no sigue el formato `NNN-nombre`, pregúntamelo antes de seguir. Si `specs/$1/` ya existe, avísame y no la sobrescribas.

Tu trabajo:
1. Hazme preguntas de UNA en UNA para eliminar ambigüedades: validaciones, casos límite, comportamiento ante errores y qué queda fuera de esta versión. Máximo 5 preguntas. Espera mi respuesta antes de hacer la siguiente.
2. Con mis respuestas, genera `specs/$1/spec.md` siguiendo la plantilla de la skill sdd, con los requisitos en EARS y "Estado: borrador".
3. Solo el QUÉ y el POR QUÉ: nada de tecnologías, arquitectura, rutas, tablas ni nombres de archivos. Sí puedes describir el comportamiento observable para quien usa la API: qué envía, qué recibe y qué tipo de error obtiene.

Al terminar, actualiza MEMORY.md y espera mi aprobación antes de pasar a la siguiente fase.
