Fase I iterativa
================

``phase_one`` calcula la carta, excluye los puntos con señal, recalcula los límites y repite hasta que el
proceso queda estable; ``PhaseOneResult.phase2`` aplica los límites resultantes a datos nuevos.

.. autofunction:: pccpy.phase_one

.. autoclass:: pccpy.PhaseOneResult
   :members: excluded_labels, to_frame, summary, phase2, plot

.. autoclass:: pccpy.PhaseOneIteration
