Cartas multivariadas
=======================

Todas aceptan ``stages`` (reestima parámetros, o reinicia el acumulador en
MEWMA/MCUSUM, al empezar cada etapa) y ``boxcox`` (transforma cada variable por
separado antes de calcular la carta). Ver la sección "Etapas y Box-Cox" de la
página principal del proyecto para ejemplos.

.. autofunction:: pccpy.t2_chart
.. autofunction:: pccpy.generalized_variance_chart
.. autofunction:: pccpy.mewma_chart
.. autofunction:: pccpy.mewma_limit
.. autofunction:: pccpy.mcusum_chart
.. autofunction:: pccpy.mcusum_limit
