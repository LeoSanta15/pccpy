Bootstrap
=========

Intervalos de confianza por bootstrap (percentil y BCa) para cualquier estadístico de una muestra; útil cuando los
datos son asimétricos y los intervalos normales pierden cobertura.

.. autofunction:: pccpy.bootstrap_ci

.. autoclass:: pccpy.BootstrapResult
   :members: ci, to_frame, summary
