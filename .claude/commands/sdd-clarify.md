---
description: SDD · Revisa la spec como un QA (solo detecta, no resuelve)
argument-hint: "[NNN-nombre]"
disable-model-invocation: true
---

Revisa `specs/$1/spec.md` como si fueras un QA muy profesional. Sigue las reglas de la skill sdd (`.claude/skills/sdd/SKILL.md`) y ten en cuenta docs/constitution.md y CLAUDE.md.

Si la carpeta o el archivo no existen, avísame y para.

Lista:
1. Ambigüedades restantes: requisitos que no se pueden verificar o que admiten varias interpretaciones.
2. Contradicciones entre requisitos.
3. Casos límite no cubiertos, incluidos los que se derivan de los datos reales (valores nulos, longitudes máximas, duplicados, relaciones que no existen).
4. Conflictos con docs/constitution.md o con las reglas de CLAUDE.md.
5. Requisitos que no siguen el formato EARS de la skill o que no tienen criterio de aceptación.

Formato: lista numerada agrupada por esos cinco apartados. En cada punto, indica el RF, la HU o la sección afectada. Si un apartado no tiene problemas, escribe "Sin problemas".

No propongas soluciones y no modifiques ningún archivo: solo detecta.
