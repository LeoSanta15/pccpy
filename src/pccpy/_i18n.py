"""Traducción de los textos visibles de pccpy.

El idioma fuente es el español: sin catálogo (o sin traducción para un texto concreto) se devuelve el original.
El idioma se elige para todo el proceso (:func:`set_language` o la variable de entorno ``PCCPY_LANG``) y puede
sobrescribirse localmente con :func:`language`.
"""
from __future__ import annotations

import contextlib
import contextvars
import gettext
import os
import warnings
from collections.abc import Iterator
from pathlib import Path

DOMINIO = "pccpy"
IDIOMA_FUENTE = "es"
_LOCALES = Path(__file__).parent / "locale"
_cache: dict[str, gettext.NullTranslations] = {}
_global: str = IDIOMA_FUENTE  # idioma de todo el proceso; se fija al final del módulo desde PCCPY_LANG
# Sobrescritura local (``with language(...)``). Un hilo nuevo NO la hereda; el idioma global sí es visible desde cualquier hilo.
_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("pccpy_idioma", default=None)


def _normalizar(lang: str) -> str:
    """``'en_US'``, ``'EN-us'`` y ``'en.UTF-8'`` → ``'en'``."""
    codigo = str(lang).strip().lower().replace("-", "_").split(".")[0].split("_")[0]
    if not codigo:
        raise ValueError(tr("El idioma no puede estar vacío."))
    return codigo


def available_languages() -> list[str]:
    """Idiomas disponibles: el español (idioma fuente) y los que tengan catálogo compilado."""
    con_catalogo = {
        d.name for d in _LOCALES.glob("*") if (d / "LC_MESSAGES" / f"{DOMINIO}.mo").is_file()
    } if _LOCALES.is_dir() else set()
    return sorted(con_catalogo | {IDIOMA_FUENTE})


def _validar(lang: str) -> str:
    codigo = _normalizar(lang)
    disponibles = available_languages()
    if codigo not in disponibles:
        raise ValueError(
            tr("Idioma no disponible: {lang!r}. Idiomas disponibles: {disponibles}.").format(
                lang=lang, disponibles=", ".join(disponibles)
            )
        )
    return codigo


def _idioma_inicial() -> str:
    """Idioma al importar: ``PCCPY_LANG`` si es válido; si no, el español (con un aviso, sin romper el import)."""
    valor = os.environ.get("PCCPY_LANG")
    if not valor:
        return IDIOMA_FUENTE
    try:
        return _validar(valor)
    except ValueError:
        warnings.warn(
            tr("La variable PCCPY_LANG={valor!r} no es un idioma disponible; se usa {defecto!r}.").format(
                valor=valor, defecto=IDIOMA_FUENTE
            ),
            UserWarning,
            stacklevel=2,
        )
        return IDIOMA_FUENTE


def _catalogo(lang: str) -> gettext.NullTranslations:
    if lang not in _cache:
        _cache[lang] = gettext.translation(DOMINIO, localedir=str(_LOCALES), languages=[lang], fallback=True)
    return _cache[lang]


def get_language() -> str:
    """Idioma activo (la sobrescritura local de :func:`language` si existe; si no, el global)."""
    return _ctx.get() or _global


def tr(mensaje: str) -> str:
    """Traduce ``mensaje`` al idioma activo (o lo devuelve igual si no hay traducción)."""
    if not mensaje:  # gettext("") devuelve la cabecera del catálogo, no una cadena vacía
        return mensaje
    return _catalogo(get_language()).gettext(mensaje)


def N_(mensaje: str) -> str:
    """Marca un texto para extraerlo **sin** traducirlo todavía (constantes de módulo): se traduce con ``tr()`` al mostrarlo."""
    return mensaje


def set_language(lang: str) -> None:
    """Fija el idioma de todo el proceso (visible desde cualquier hilo).

    Parameters
    ----------
    lang : str
        Código del idioma: ``'es'`` o ``'en'`` (se aceptan variantes como ``'en_US'``).

    Raises
    ------
    ValueError
        Si el idioma no está disponible (ver :func:`available_languages`).
    """
    global _global
    _global = _validar(lang)


@contextlib.contextmanager
def language(lang: str) -> Iterator[None]:
    """Cambia el idioma solo dentro del bloque ``with`` (en el contexto actual).

    Un hilo creado dentro del bloque no hereda este idioma: usa el global.

    Raises
    ------
    ValueError
        Si el idioma no está disponible.
    """
    token = _ctx.set(_validar(lang))
    try:
        yield
    finally:
        _ctx.reset(token)


_global = _idioma_inicial()
