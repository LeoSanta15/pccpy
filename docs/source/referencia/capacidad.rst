Capacidad del proceso
========================

.. autofunction:: pccpy.capability_analysis
.. autofunction:: pccpy.capability_nonnormal
.. autofunction:: pccpy.capability_boxcox
.. autofunction:: pccpy.capability_sixpack

.. note::

   :class:`~pccpy.CapabilityResult` expone dos propiedades adicionales:

   * ``dpmo`` — defectos por millón de oportunidades esperados (= PPM general).
   * ``sigma_level`` — nivel sigma del proceso (= Z.Bench, sin el desplazamiento
     de 1.5σ). Ambas aparecen en ``.to_frame()`` y ``.summary()``.
