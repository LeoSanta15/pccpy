Cartas multivariadas
=======================

Todas aceptan ``stages`` (reestima parámetros, o reinicia el acumulador en
MEWMA/MCUSUM, al empezar cada etapa) y ``boxcox`` (transforma cada variable por
separado antes de calcular la carta). Ver la sección "Etapas y Box-Cox" de la
página principal del proyecto para ejemplos.

.. autofunction:: spyc.t2_chart
.. autofunction:: spyc.generalized_variance_chart
.. autofunction:: spyc.mewma_chart
.. autofunction:: spyc.mewma_limit
.. autofunction:: spyc.mcusum_chart
.. autofunction:: spyc.mcusum_limit
