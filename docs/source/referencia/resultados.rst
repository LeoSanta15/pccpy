Objetos de resultado
=======================

Toda carta de control devuelve un :class:`~pccpy.ControlChart` (las
multivariadas devuelven la subclase :class:`~pccpy.MultivariateChart`), con un
:class:`~pccpy.Panel` por cada gráfico que la compone (por ejemplo, el panel
``"I"`` y el panel ``"MR"`` de una carta I-MR).

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
