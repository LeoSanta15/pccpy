Objetos de resultado
=======================

Toda carta de control devuelve un :class:`~pccpy.ControlChart` (las
multivariadas devuelven la subclase :class:`~pccpy.MultivariateChart`), con un
:class:`~pccpy.Panel` por cada gráfico que la compone (por ejemplo, el panel
``"I"`` y el panel ``"MR"`` de una carta I-MR).

.. autofunction:: pccpy.plot_control_chart

.. autoclass:: pccpy.ControlChart
   :members:

.. autoclass:: pccpy.MultivariateChart
   :members:
   :show-inheritance:

.. autoclass:: pccpy.Panel
   :members:

Capacidad y normalidad devuelven, respectivamente:

.. autoclass:: pccpy.CapabilityResult
   :members:

.. autoclass:: pccpy.NonNormalCapabilityResult
   :members:

.. autoclass:: pccpy.NormalityResult
   :members:

Herramientas de análisis de proceso
--------------------------------------

Los demás módulos devuelven objetos propios documentados en sus páginas
de referencia:

* :class:`~pccpy.RunChartResult` — véase :doc:`run_chart_y_precontrol`.
* :class:`~pccpy.PreControlResult` — véase :doc:`run_chart_y_precontrol`.
* :class:`~pccpy.ToleranceResult` — véase :doc:`tolerancia`.
* :class:`~pccpy.SamplingPlanAttributes`, :class:`~pccpy.SamplingPlanVariables`,
  :class:`~pccpy.DodgeRomigPlan` — véase :doc:`muestreo_aceptacion`.
* :class:`~pccpy.GageRRResult`, :class:`~pccpy.Type1Result`,
  :class:`~pccpy.LinearityResult`, :class:`~pccpy.AttributeAgreementResult`
  — véase :doc:`msa`.
