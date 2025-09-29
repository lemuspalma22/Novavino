import re
import unicodedata
from typing import Tuple, Optional, List

from inventario.models import Producto, AliasProducto

# Regex utilitarias
_SPACES_RE = re.compile(r"\s+")
_PUNCT_SOFT_RE = re.compile(r"[.\u00B7\u2022•·]+$")  # puntos/símbolos suaves al final


def _strip_accents(s: str) -> str:
    """Quita acentos/diacríticos (ANÉCDOTA -> ANECDOTA)."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def _normalize_mes_variants(s: str) -> str:
    """
    Unifica variantes de 'mes(es)' a sufijo 'm':
      '6 meses' -> '6m', '6 mes' -> '6m', '6 m' -> '6m', '6M' -> '6m'
    """
    s = re.sub(r"\b(\d+)\s*mes(?:es)?\b", r"\1m", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(\d+)\s*m\b", r"\1m", s, flags=re.IGNORECASE)
    return s


def normalize_text(s: str) -> str:
    """
    Normalización tolerante para matching:
      - trim
      - colapsar espacios múltiples
      - quitar puntos/símbolos suaves finales
      - quitar acentos
      - pasar a minúsculas
      - unificar variantes '6 meses'/'6 m'/'6M' -> '6m'
    """
    if not s:
        return ""
    s = s.strip()
    s = _PUNCT_SOFT_RE.sub("", s)     # quita '.' y similares al final
    s = _SPACES_RE.sub(" ", s)        # colapsa espacios
    s = _strip_accents(s)             # quita acentos
    s = s.lower()
    s = _normalize_mes_variants(s)
    return s


def _collect_candidates() -> Tuple[List[Producto], List[AliasProducto]]:
    """
    Carga productos y aliases. Suficiente para catálogos pequeños/medianos.
    (Si creciera mucho, podemos cachear normalizados en memoria por corrida.)
    """
    productos = list(Producto.objects.all().only("id", "nombre"))
    aliases = list(AliasProducto.objects.select_related("producto").only("id", "alias", "producto_id"))
    return productos, aliases


def encontrar_producto_unico(texto_busqueda: str) -> Tuple[Optional[Producto], Optional[str]]:
    """
    Devuelve (producto, error) donde:
      - producto: Producto o None
      - error: None si hay match único
               'ambiguous' si hay múltiples
               'not_found' si no hay match.

    Prioridades de matching (tolerante con normalización):
      1) Coincidencia EXACTA por alias normalizado.
      2) Coincidencia EXACTA por nombre de producto normalizado.
      3) Coincidencia "suave" (contains) por nombre/alias normalizados si resulta única.
      En cualquier caso con >1 coincidencias -> 'ambiguous'.
    """
    target = normalize_text(texto_busqueda or "")
    if not target:
        return None, "not_found"

    productos, aliases = _collect_candidates()

    # 1) Alias exacto (normalizado)
    alias_hits = []
    for a in aliases:
        alias_norm = normalize_text(getattr(a, "alias", "") or "")
        if alias_norm == target:
            alias_hits.append(a.producto)
    # deduplicar por id
    alias_hits = list({p.id: p for p in alias_hits}.values())
    if len(alias_hits) == 1:
        return alias_hits[0], None
    if len(alias_hits) > 1:
        return None, "ambiguous"

    # 2) Nombre de producto exacto (normalizado)
    prod_hits = []
    for p in productos:
        name_norm = normalize_text(getattr(p, "nombre", "") or "")
        if name_norm == target:
            prod_hits.append(p)
    prod_hits = list({p.id: p for p in prod_hits}.values())
    if len(prod_hits) == 1:
        return prod_hits[0], None
    if len(prod_hits) > 1:
        return None, "ambiguous"

    # 3) Búsqueda "suave": contener/ser contenido, si resulta única
    soft_hits = []
    for p in productos:
        name_norm = normalize_text(getattr(p, "nombre", "") or "")
        if target in name_norm or name_norm in target:
            soft_hits.append(p)
    for a in aliases:
        alias_norm = normalize_text(getattr(a, "alias", "") or "")
        if target in alias_norm or alias_norm in target:
            soft_hits.append(a.producto)

    soft_hits = list({p.id: p for p in soft_hits}.values())
    if len(soft_hits) == 1:
        return soft_hits[0], None
    if len(soft_hits) > 1:
        return None, "ambiguous"

    return None, "not_found"