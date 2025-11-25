# compras/utils/validation.py
"""
Sistema de validación automática para marcar compras sospechosas.
NO modifica el extractor, solo evalúa después de la extracción.
"""
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional, Tuple, Set
import re
from django.apps import apps


def _D(x) -> Optional[Decimal]:
    """Helper para convertir a Decimal de forma segura."""
    if x is None or x == "":
        return None
    try:
        return Decimal(str(x).replace(",", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return None


def evaluar_concepto_para_revision(
    concepto: Dict[str, Any],
    producto_mapeado: Optional[Any] = None,
    datos_factura: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Evalúa un concepto extraído y retorna lista de motivos de revisión.
    
    Args:
        concepto: dict con descripcion, cantidad, precio_unitario, importe
        producto_mapeado: instancia de Producto si se encontró match, None si no
        datos_factura: dict completo de la factura (para validaciones de totales)
    
    Returns:
        Lista de strings con motivos de revisión. Lista vacía = OK.
    """
    motivos = []
    
    # 1. Validar descripción
    desc = concepto.get("descripcion", "") or concepto.get("nombre", "") or ""
    if not desc or len(desc.strip()) == 0:
        motivos.append("descripcion_vacia")
    elif len(desc.strip()) < 12:
        motivos.append("descripcion_muy_corta")
    else:
        # Contar caracteres alfabéticos
        alpha_count = sum(1 for c in desc if c.isalpha())
        if alpha_count < 5:
            motivos.append("descripcion_pocos_caracteres_alfabeticos")
    
    # 2. Validar mapeo de producto
    if producto_mapeado is None:
        motivos.append("producto_no_reconocido")
    
    # 3. Validaciones numéricas
    cantidad = _D(concepto.get("cantidad"))
    precio_unitario = _D(concepto.get("precio_unitario"))
    importe = _D(concepto.get("importe"))
    
    if cantidad is not None and precio_unitario is not None and importe is not None:
        # Validar cantidad × P/U ≈ importe
        importe_calculado = cantidad * precio_unitario
        try:
            diferencia = abs(importe - importe_calculado)
            diferencia_pct = diferencia / importe if importe else Decimal("1")
            
            # Tolerancia: 2% (ajustable según necesidad)
            if diferencia_pct > Decimal("0.02"):
                motivos.append(f"importe_no_coincide_diff_{float(diferencia_pct)*100:.1f}pct")
        except Exception:
            motivos.append("error_validacion_numerica")
    else:
        # Faltan valores numéricos
        if cantidad is None or cantidad == 0:
            motivos.append("cantidad_faltante_o_cero")
        if precio_unitario is None or precio_unitario == 0:
            motivos.append("precio_unitario_faltante_o_cero")
        # No marcar 'importe_faltante' si podemos derivarlo con cantidad x P/U
        if importe is None and not (cantidad is not None and cantidad != 0 and precio_unitario is not None and precio_unitario != 0):
            motivos.append("importe_faltante")

    # 4. Validar precio vs precio guardado en BD (guardián de precios)
    if producto_mapeado is not None and precio_unitario is not None:
        try:
            precio_bd = _D(getattr(producto_mapeado, "precio_compra", None))
            if precio_bd and precio_bd > 0:
                diferencia = precio_unitario - precio_bd
                diferencia_pct = abs(diferencia) / precio_bd
                
                # Ignorar diferencias insignificantes (< $1 absoluto)
                if abs(diferencia) >= Decimal("1.0"):
                    # Umbral conservador: 2% más caro, 10% más barato
                    if diferencia > 0 and diferencia_pct > Decimal("0.02"):  # Más caro
                        motivos.append(f"precio_mas_alto_bd_diff_{float(diferencia_pct)*100:.1f}pct")
                    elif diferencia < 0 and diferencia_pct > Decimal("0.10"):  # Más barato
                        motivos.append(f"precio_mas_bajo_bd_diff_{float(diferencia_pct)*100:.1f}pct")
        except Exception:
            # No romper validación si falla comparación de precios
            pass
    
    # 5. Reglas provider-specific (Vieja Bodega)
    try:
        prov_name = _extract_provider_name(datos_factura, producto_mapeado)
        if prov_name and prov_name.startswith("vieja bodega"):
            motivos += _evaluar_vieja_bodega(desc, producto_mapeado)
    except Exception:
        # Nunca romper validación por reglas específicas
        pass
    
    return motivos


# ----------------------
# Reglas específicas: Vieja Bodega
# ----------------------

CRITICAL_TOKENS_VB: Set[str] = {
    "MP", "SPIRO",  # microperforado spiro
    "BIB", "BAG",   # bag-in-box
    "RESERVA", "CRIANZA", "GRAN", "BLEND",
}

CAPACITY_RE = re.compile(r"(\d{2,4})(?:\s*)(ML|L|LT)", re.I)
LEN_WARN_VB = 39  # sugerido, ajustable si se requiere


def _norm_text(s: str) -> str:
    s = (s or "").upper().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _tokens(s: str) -> Set[str]:
    s = _norm_text(s)
    return set(re.findall(r"[A-Z0-9]+", s))


def _extract_capacity_ml(s: str) -> Optional[int]:
    if not s:
        return None
    m = CAPACITY_RE.search(s)
    if not m:
        return None
    qty = int(m.group(1))
    unit = m.group(2).upper()
    if unit in ("L", "LT") and qty < 50:  # 1.5 L → 1500 ml
        return qty * 1000
    return qty


def _extract_provider_name(datos_factura: Optional[Dict[str, Any]], producto_mapeado: Optional[Any]) -> Optional[str]:
    """Obtiene el nombre de proveedor en minúsculas, robusto a distintos tipos."""
    name = None
    if datos_factura is not None:
        prov = datos_factura.get("proveedor")
        if hasattr(prov, "nombre"):
            name = getattr(prov, "nombre", None)
        elif isinstance(prov, str):
            name = prov
    if not name and producto_mapeado is not None:
        try:
            name = getattr(getattr(producto_mapeado, "proveedor", None), "nombre", None)
        except Exception:
            name = None
    return (name or "").strip().lower()


def _evaluar_vieja_bodega(desc: str, producto_mapeado: Optional[Any]) -> List[str]:
    motivos: List[str] = []
    desc_norm = _norm_text(desc)
    tokens_desc = _tokens(desc_norm)

    # Señal C: longitud sospechosa (posible truncado de 2 líneas en una)
    if len(desc_norm) >= LEN_WARN_VB:
        motivos.append("descripcion_larga_posible_truncado")

    # Señal A: tokens críticos faltantes respecto al producto mapeado
    if producto_mapeado is not None:
        try:
            nombre_prod = _norm_text(getattr(producto_mapeado, "nombre", ""))
            tokens_prod = _tokens(nombre_prod)
            faltantes = sorted(list((tokens_prod & CRITICAL_TOKENS_VB) - tokens_desc))
            if faltantes:
                motivos.append("tokens_faltantes_en_descripcion:" + ",".join(faltantes))

            # Señal D: capacidad inconsistente o ausente vs producto
            cap_desc = _extract_capacity_ml(desc_norm)
            cap_prod = _extract_capacity_ml(nombre_prod)
            if cap_prod and cap_desc and cap_desc != cap_prod:
                motivos.append("capacidad_inconsistente")
            elif cap_prod and not cap_desc:
                motivos.append("capacidad_ausente_en_descripcion")
        except Exception:
            pass

    # Señal B: buscar posibles variantes en catálogo del mismo proveedor que añadan tokens críticos
    try:
        Producto = apps.get_model("inventario", "Producto")
        qs = Producto.objects.filter(proveedor__nombre__istartswith="vieja bodega").only("nombre")[:500]
        for p in qs:
            nombre_cat = _norm_text(getattr(p, "nombre", ""))
            tokens_cat = _tokens(nombre_cat)
            # Si la línea es subconjunto del nombre en catálogo y en catálogo hay tokens críticos extra
            extras_criticos = (tokens_cat & CRITICAL_TOKENS_VB) - tokens_desc
            if tokens_desc and tokens_desc.issubset(tokens_cat) and extras_criticos:
                motivos.append("posible_variante_no_capturada:" + ",".join(sorted(list(extras_criticos))))
                break
    except Exception:
        pass

    return motivos


def evaluar_totales_factura(datos_extraidos: Dict[str, Any]) -> List[str]:
    """
    Valida los totales de la factura completa.
    
    Args:
        datos_extraidos: dict completo del extractor con conceptos, subtotal, iva, total
    
    Returns:
        Lista de strings con motivos de revisión a nivel factura.
    """
    motivos = []
    
    subtotal = _D(datos_extraidos.get("subtotal"))
    iva = _D(datos_extraidos.get("iva"))
    total = _D(datos_extraidos.get("total"))
    conceptos = datos_extraidos.get("conceptos") or datos_extraidos.get("productos") or []
    
    # 1. Validar suma de importes = subtotal
    if subtotal and conceptos:
        suma_importes = Decimal("0")
        for c in conceptos:
            imp = _D(c.get("importe"))
            if not imp:
                q = _D(c.get("cantidad"))
                pu = _D(c.get("precio_unitario"))
                try:
                    if q is not None and pu is not None:
                        imp = q * pu
                except Exception:
                    imp = None
            if imp:
                suma_importes += imp
        
        try:
            diferencia = abs(subtotal - suma_importes)
            diferencia_pct = diferencia / subtotal if subtotal else Decimal("1")
            if diferencia_pct > Decimal("0.02"):  # Tolerancia 2%
                motivos.append(f"suma_importes_no_coincide_subtotal_diff_{float(diferencia_pct)*100:.1f}pct")
        except Exception:
            motivos.append("error_validacion_suma_importes")
    
    # 2. Validar subtotal + IVA ≈ total
    if subtotal and total:
        total_calculado = subtotal + (iva or Decimal("0"))
        try:
            diferencia = abs(total - total_calculado)
            diferencia_pct = diferencia / total if total else Decimal("1")
            if diferencia_pct > Decimal("0.02"):  # Tolerancia 2%
                motivos.append(f"subtotal_mas_iva_no_coincide_total_diff_{float(diferencia_pct)*100:.1f}pct")
        except Exception:
            motivos.append("error_validacion_totales")
    
    # 3. Número atípico de líneas (opcional, comentado por ahora)
    # num_lineas = len(conceptos)
    # if num_lineas == 0:
    #     motivos.append("factura_sin_conceptos")
    # elif num_lineas > 50:
    #     motivos.append("numero_atipico_lineas_muy_alto")
    
    return motivos


def aplicar_validaciones_a_compra(
    datos_extraidos: Dict[str, Any],
    productos_mapeados: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aplica todas las validaciones y retorna información para marcar flags.
    
    Args:
        datos_extraidos: dict del extractor
        productos_mapeados: lista de dicts con info de cada producto
            Cada elemento debe tener: {
                "concepto": dict original,
                "producto": instancia o None,
                "nombre": str
            }
    
    Returns:
        dict con:
            "requiere_revision_compra": bool
            "motivos_compra": list[str]
            "lineas_revision": list[dict] con info por línea
    """
    resultado = {
        "requiere_revision_compra": False,
        "motivos_compra": [],
        "lineas_revision": []
    }
    
    # Validar totales de factura
    motivos_factura = evaluar_totales_factura(datos_extraidos)
    if motivos_factura:
        resultado["requiere_revision_compra"] = True
        resultado["motivos_compra"] = motivos_factura
    
    # Validar cada línea
    for item in productos_mapeados:
        concepto = item.get("concepto", {})
        producto = item.get("producto")
        
        motivos_linea = evaluar_concepto_para_revision(
            concepto,
            producto_mapeado=producto,
            datos_factura=datos_extraidos
        )
        
        linea_info = {
            "nombre": item.get("nombre", ""),
            "requiere_revision": bool(motivos_linea),
            "motivos": motivos_linea
        }
        resultado["lineas_revision"].append(linea_info)
        
        # Si alguna línea requiere revisión, marcar la compra completa
        if motivos_linea:
            resultado["requiere_revision_compra"] = True
    
    return resultado
