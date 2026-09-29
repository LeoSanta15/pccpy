MSA / Gage R&R
================

Los estudios de sistemas de medición (MSA) cuantifican cuánta variación
del proceso se debe al sistema de medición. pccpy implementa los cinco
estudios más comunes del manual AIAG MSA (4ª ed.):

* **Crossed Gage R&R** — cada operador mide cada parte (diseño cruzado).
* **Nested Gage R&R** — cada operador mide un conjunto distinto de partes.
* **Type 1 Study** — sesgo y repetibilidad de una sola fuente de variación.
* **Linearity and Bias** — variación del sesgo a lo largo del rango de medición.
* **Attribute Agreement Analysis** — concordancia entre operadores y vs
  referencia (Kappa de Cohen y Kappa de Fleiss).

Crossed Gage R&R
-----------------

.. autofunction:: pccpy.gage_rr
.. autofunction:: pccpy.plot_gage_rr
.. autoclass:: pccpy.GageRRResult
   :members:

Nested Gage R&R
----------------

.. autofunction:: pccpy.gage_rr_nested

Estudio Tipo 1
---------------

.. autofunction:: pccpy.gage_type1
.. autofunction:: pccpy.gage_type1_summary
.. autofunction:: pccpy.plot_type1
.. autoclass:: pccpy.Type1Result
   :members:

Linealidad y sesgo
-------------------

.. autofunction:: pccpy.gage_linearity
.. autofunction:: pccpy.plot_linearity
.. autoclass:: pccpy.LinearityResult
   :members:

Concordancia por atributos
---------------------------

.. autofunction:: pccpy.attribute_agreement
.. autofunction:: pccpy.plot_attribute_agreement
.. autoclass:: pccpy.AttributeAgreementResult
   :members:
