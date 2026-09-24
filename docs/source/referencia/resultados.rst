Objetos de resultado
=======================

Toda carta de control devuelve un :class:`~spyc.ControlChart` (las
multivariadas devuelven la subclase :class:`~spyc.MultivariateChart`), con un
:class:`~spyc.Panel` por cada gráfico que la compone (por ejemplo, el panel
``"I"`` y el panel ``"MR"`` de una carta I-MR).

.. autoclass:: spyc.ControlChart
   :members:

.. autoclass:: spyc.MultivariateChart
   :members:
   :show-inheritance:

.. autoclass:: spyc.Panel
   :members:

Capacidad y normalidad devuelven, respectivamente:

.. autoclass:: spyc.CapabilityResult
   :members:

.. autoclass:: spyc.NonNormalCapabilityResult
   :members:

.. autoclass:: spyc.NormalityResult
   :members:
