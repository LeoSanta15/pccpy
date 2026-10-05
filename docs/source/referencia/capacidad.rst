Capacidad del proceso
========================

.. autofunction:: pccpy.capability_analysis
.. autofunction:: pccpy.capability_analysis_summary
.. autofunction:: pccpy.capability_nonnormal
.. autofunction:: pccpy.capability_boxcox
.. autofunction:: pccpy.capability_sixpack
.. autofunction:: pccpy.plot_capability
.. autofunction:: pccpy.capability_binomial
.. autofunction:: pccpy.capability_poisson

.. autoclass:: pccpy.BinomialCapabilityResult
   :members: to_frame, summary, plot, save_plot, to_excel, homogeneous

.. autoclass:: pccpy.PoissonCapabilityResult
   :members: to_frame, summary, plot, save_plot, to_excel, homogeneous

.. note::

   :class:`~pccpy.CapabilityResult` expone dos propiedades adicionales:

   * ``dpmo`` — defectos por millón de oportunidades esperados (= PPM general).
   * ``sigma_level`` — nivel sigma del proceso (= Z.Bench, sin el desplazamiento
     de 1.5σ). Ambas aparecen en ``.to_frame()`` y ``.summary()``.

.. note::

   **Uso sin límites de especificación** (desde v0.10.7):
   ``lsl`` y ``usl`` son opcionales en :func:`~pccpy.capability_analysis` y
   :func:`~pccpy.capability_analysis_summary`. Los índices que dependen de
   especificaciones (Cp, Cpk, Pp, Ppk, dpmo, sigma_level) se devuelven como
   ``NaN`` cuando no se pasan; ``sigma_within`` y ``sigma_overall`` siempre
   se calculan::

      import pccpy as pp
      r = pp.capability_analysis(datos)   # sin lsl ni usl
      print(r.sigma_within, r.sigma_overall)  # valores válidos
      print(r.cp)                             # nan
