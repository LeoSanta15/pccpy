# Plan — 005 Guardar y reutilizar una Fase I

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí (principios 1, 3, 4 y 5).
- **Plan original:** docs/planes/PLAN_FASE1_GUARDAR.md (fases G1, G2 y G3)

> Plan retroactivo: resume el diseño que quedó en el código, no un diseño previo.

## Diseño

`PhaseOneResult.to_dict/from_dict/to_json/from_json/from_limits` en `src/pccpy/phase_one.py`; las cartas se identifican por nombre y se reconstruyen con las mismas funciones públicas.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| JSON sin pickle | Pickle | Pickle ejecuta código al cargar; el JSON se puede revisar |
| Cartas por nombre | Guardar el objeto función | Es serializable y no depende del entorno |
| Rechazar un esquema más nuevo | Intentar leerlo | Evita resultados silenciosamente erróneos |

## Validación independiente

Comprobación de `run_validation()`: «Fase II tras guardar y cargar una Fase I (JSON)» frente a los mismos límites dados a mano.

## Riesgos

Cambios futuros del esquema: el número de versión del esquema los detecta.

## Documentación y traducciones

Sección «Reutilizar una Fase I que ya tienes» del inicio rápido y del README (es/en), catálogos `.po`.
