Intervalos de tolerancia
==========================

Un intervalo de tolerancia (L, U) garantiza que, con confianza ``1−α``,
al menos una fracción ``p`` de la población cae dentro del intervalo.

Se soportan dos métodos:

* **normal** — supone distribución normal. Para bilateral usa la
  aproximación de Howe (1969); para unilateral, la distribución t no
  central exacta.
* **nonparametric** — libre de distribución, basado en estadísticos de
  orden. Requiere muestras más grandes para la misma cobertura y confianza.

.. autofunction:: pccpy.tolerance_interval
.. autofunction:: pccpy.tolerance_interval_summary
.. autofunction:: pccpy.plot_tolerance
.. autoclass:: pccpy.ToleranceResult
   :members:
