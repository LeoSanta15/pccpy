Muestreo de aceptación
========================

pccpy implementa los tres planes de muestreo más utilizados en la industria:

* **ANSI/ASQ Z1.4** (atributos): plan n/c basado en la tabla estándar.
* **MIL-STD-414** (variables): plan n/k (método del factor de aceptabilidad; tablas A-2 y B-1).
* **Dodge-Romig** (atributos): minimiza el número promedio de inspección
  total (ATI) para un LTPD o AOQL objetivo.

Todos los planes calculan automáticamente α, β (fijado en 0.10), LTPD y AOQL,
y devuelven objetos con `.oc_curve()`, `.aoq_curve()`, `.summary()`,
`.to_frame()` y `.plot()`.

Por atributos — Z1.4
---------------------

.. autofunction:: pccpy.acceptance_sampling_attributes
.. autofunction:: pccpy.plot_sampling_attributes
.. autoclass:: pccpy.SamplingPlanAttributes
   :members:
.. autofunction:: pccpy.plot_sampling_double
.. autoclass:: pccpy.DoublePlanAttributes
   :members:

Por variables — MIL-STD-414
---------------------------

.. autofunction:: pccpy.acceptance_sampling_variables
.. autofunction:: pccpy.plot_sampling_variables
.. autoclass:: pccpy.SamplingPlanVariables
   :members:

Dodge-Romig
-----------

.. autofunction:: pccpy.dodge_romig
.. autoclass:: pccpy.DodgeRomigPlan
   :members:
