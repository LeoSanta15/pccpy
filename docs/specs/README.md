# Desarrollo guiado por especificaciones

Todo trabajo nuevo de `pccpy` que cambie el comportamiento de la biblioteca (una función, un resultado numérico, una
opción) parte de una **especificación escrita y revisada antes de programar**. La especificación dice *qué* debe
cumplirse y *cómo se comprobará*; el código y los tests la implementan; al terminar, cada requisito apunta al test que
lo demuestra.

Los planes anteriores de `docs/planes/` se conservan como historia. Las correcciones triviales (una errata, un
docstring, una traducción) no necesitan especificación.

## Flujo

```
1. Especificar  →  2. Aclarar  →  3. Planificar  →  4. Tareas  →  5. Implementar  →  6. Verificar  →  7. Cerrar
   spec.md          preguntas        plan.md          tasks.md       código + tests     make check       estado
```

1. **Especificar** (`spec.md`). Problema, usuarios, requisitos `S001-RF-01…` y, para cada uno, un criterio de
   aceptación comprobable (dado / cuando / entonces) con la **referencia independiente** que lo respalda
   (CLAUDE.md, R-02). Lo que se deja fuera, también.
2. **Aclarar.** Toda duda se escribe como `[NECESITA ACLARACIÓN: …]` dentro de la especificación; no se adivina. La
   especificación no pasa a `aprobada` mientras quede alguna.
3. **Planificar** (`plan.md`). Diseño, módulos que se tocan, decisiones con su alternativa descartada, riesgos y la
   comprobación que se sumará a `run_validation()`. Se contrasta con `CONSTITUCION.md`.
4. **Tareas** (`tasks.md`). Casillas pequeñas y ordenadas; cada una cita los requisitos que cubre. Los tests que
   fijan los requisitos se escriben **antes** que el código y deben fallar por el motivo esperado.
5. **Implementar.** Cambios quirúrgicos (R-01), una rama y un PR por especificación o por fase.
6. **Verificar.** `make check` en verde, la comprobación de validación en verde y, si cambian resultados numéricos,
   los valores de referencia (`tests/golden/`) regenerados y revisados línea a línea.
7. **Cerrar.** La especificación pasa a `implementada`: todas las tareas marcadas y cada requisito citado por al menos
   un test con su identificador (`S001-RF-01`) en el nombre, el docstring o un comentario.

## Estados

| Estado | Significa | Exige |
|---|---|---|
| `borrador` | Se está escribiendo; puede haber dudas abiertas | estructura completa |
| `aprobada` | Revisada por la persona responsable; se puede implementar | ninguna duda abierta |
| `implementada` | Hecha y verificada | tareas marcadas y trazabilidad a tests |
| `descartada` | No se hará | motivo en la propia especificación |

## Estructura

```
docs/specs/
  README.md              este archivo
  CONSTITUCION.md        principios que toda especificación y todo plan deben respetar
  _plantilla/            spec.md, plan.md y tasks.md para copiar
  NNN-nombre-corto/      una carpeta por especificación (numeración correlativa)
```

Para empezar: `cp -r docs/specs/_plantilla docs/specs/NNN-nombre-corto` y rellena `spec.md`.
`make specs-check` (también dentro de `make check-fast` y del CI) comprueba que la estructura, los estados y la
trazabilidad se cumplen; no juzga si la especificación es buena, eso lo hace la revisión.
