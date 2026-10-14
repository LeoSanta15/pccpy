# Plan — 001 Tolerancia no paramétrica unilateral

- **Especificación:** [spec.md](spec.md)
- **Respeta la constitución:** sí.

## Diseño

Solo cambia la rama unilateral de `_nonparam_indices` (`src/pccpy/tolerance.py`): recorrer `r` en orden ascendente,
guardar el último que cumple `P(Bin(n, 1 − p) ≥ r) ≥ confianza` y salir en el primero que no cumple (la cola binomial
decrece con `r`), igual que la rama bilateral. Las ramas inferior y superior comparten la misma cola.

## Decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Mismo criterio que la bilateral (intervalo más estrecho válido) | Dejar `r = 1` | Es válido pero muy conservador y no coincide con la bilateral |
| Sin interpolación entre estadísticos de orden | Interpolar para clavar la confianza | Rompe la garantía de libre distribución y complica la explicación |
| (Pendiente de aclarar) conservar el comportamiento anterior tras un parámetro | Cambio sin opción | Ver pregunta abierta |

## Validación independiente

- Comprobación `tolerancia-no-parametrica-unilateral` en `run_validation()`: cola binomial calculada aparte para
  `n = 300` (r = 9, 0,96593) y para el mínimo `n = 59`.
- Test de simulación con semilla fija (S001-RF-02).

## Riesgos

- Cambia resultados existentes: versión menor y entrada en «Cambios que alteran resultados».
- Los valores de referencia `tests/golden/` de la tolerancia no paramétrica podrían cambiar; se revisa el diff.

## Documentación y traducciones

`tolerance.md` (explicar la elección de `r` en el caso unilateral), docstring de `tolerance_interval`, CHANGELOG y
catálogos de la documentación en inglés.
