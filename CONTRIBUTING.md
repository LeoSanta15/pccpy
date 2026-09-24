# Contribuir a pccpy

1. Haz un fork y clona el repositorio.
2. Instala en modo desarrollo: `pip install -e ".[dev]"`.
3. Ejecuta las pruebas: `pytest` (deben pasar todas).
4. Todo cambio numérico debe ir acompañado de una prueba que lo compare con una
   referencia independiente (fórmula manual, tabla publicada u otra librería),
   no con la propia salida de pccpy.
5. Código, docstrings y mensajes de error en español.
6. Abre un Pull Request describiendo qué cambia y cómo lo verificaste.

## Reportar diferencias con Minitab

Si un resultado difiere de Minitab, abre un [issue](https://github.com/LeoSanta15/pccpy/issues)
con: los datos (o una muestra reproducible), la llamada a pccpy, el resultado de
pccpy y el de Minitab (con la versión de Minitab y las opciones usadas).
