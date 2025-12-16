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
    # Soportar múltiples variantes de nombre/descripción según extractor
    desc = (concepto.get("descripcion", "") or 
            concepto.get("nombre", "") or 
            concepto.get("nombre_detectado", "") or "")
    
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
            # Detectar si es Secretos de la Vid para aplicar validación especial
            prov_name = _extract_provider_name(datos_factura, producto_mapeado)
            es_secretos_vid = prov_name and "secretos" in prov_name.lower() and "vid" in prov_name.lower()
            
            precio_bd = _D(getattr(producto_mapeado, "precio_compra", None))
            if precio_bd and precio_bd > 0:
                # Validación especial para Secretos de la Vid
                if es_secretos_vid:
                    # El extractor de Secretos de la Vid ya calcula el precio final
                    # (con IEPS 26.5%, IVA 16% y descuento 24% aplicados)
                    # Entonces comparamos directamente
                    diferencia_abs = abs(precio_unitario - precio_bd)
                    diferencia_pct = diferencia_abs / precio_bd if precio_bd else Decimal("0")
                    
                    # Secretos de la Vid: ser estricto en ambas direcciones
                    # - Más bajo >5%: raro con descuento fijo del 24%
                    # - Más alto >3%: puede ser licor, error, o falta de descuento
                    
                    if precio_unitario < precio_bd:
                        # Precio más BAJO
                        if diferencia_pct > Decimal("0.05"):  # >5%
                            motivos.append(f"precio_mas_bajo_sospechoso_{float(diferencia_pct)*100:.1f}pct_${float(diferencia_abs):.2f}")
                    else:
                        # Precio más ALTO
                        if diferencia_pct > Decimal("0.03"):  # >3%
                            motivos.append(f"precio_mas_alto_sospechoso_{float(diferencia_pct)*100:.1f}pct_${float(diferencia_abs):.2f}")
                else:
                    # Validación estándar para otros proveedores
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
    
    Validación principal: Suma(cantidad × precio_unitario) ≈ Total factura
    Tolerancia: <1% para manejar redondeos
    
    Args:
        datos_extraidos: dict completo del extractor con conceptos/productos y total
    
    Returns:
        Lista de strings con motivos de revisión a nivel factura.
    """
    motivos = []
    
    total_factura = _D(datos_extraidos.get("total"))
    conceptos = datos_extraidos.get("conceptos") or datos_extraidos.get("productos") or []
    
    if not total_factura or not conceptos:
        return motivos  # No hay datos suficientes para validar
    
    # Calcular suma de productos: cantidad × precio_unitario
    suma_productos = Decimal("0")
    productos_validos = 0
    
    for c in conceptos:
        cantidad = _D(c.get("cantidad"))
        precio_unitario = _D(c.get("precio_unitario"))
        
        if cantidad is not None and precio_unitario is not None:
            importe = cantidad * precio_unitario
            suma_productos += importe
            productos_validos += 1
    
    if productos_validos == 0:
        motivos.append("no_se_pueden_calcular_importes_productos")
        return motivos
    
    # Validar: suma_productos ≈ total_factura (tolerancia <1%)
    try:
        diferencia = abs(total_factura - suma_productos)
        diferencia_pct = (diferencia / total_factura) if total_factura else Decimal("1")
        
        if diferencia_pct > Decimal("0.01"):  # Tolerancia 1%
            motivos.append(
                f"suma_productos_no_coincide_total_"
                f"esperado_{float(total_factura):.2f}_"
                f"calculado_{float(suma_productos):.2f}_"
                f"diff_{float(diferencia_pct)*100:.2f}pct"
            )
    except Exception as e:
        motivos.append(f"error_validacion_totales_{str(e)}")
    
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
    
    # Validación especial para Secretos de la Vid: detectar IEPS especiales (licores)
    proveedor = datos_extraidos.get("proveedor")
    prov_name = ""
    if hasattr(proveedor, "nombre"):
        prov_name = proveedor.nombre.lower()
    elif isinstance(proveedor, str):
        prov_name = proveedor.lower()
    
    es_secretos_vid = "secretos" in prov_name and "vid" in prov_name
    
    if es_secretos_vid:
        ieps_2 = _D(datos_extraidos.get("ieps_2_importe", 0)) or Decimal("0")
        ieps_3 = _D(datos_extraidos.get("ieps_3_importe", 0)) or Decimal("0")
        
        if ieps_2 > 0 or ieps_3 > 0:
            resultado["requiere_revision_compra"] = True
            motivos_licor = []
            if ieps_2 > 0:
                motivos_licor.append(f"contiene_ieps_30pct_${float(ieps_2):.2f}")
            if ieps_3 > 0:
                motivos_licor.append(f"contiene_licor_ieps_53pct_${float(ieps_3):.2f}")
            resultado["motivos_compra"].extend(motivos_licor)
    
    # Validar totales de factura
    motivos_factura = evaluar_totales_factura(datos_extraidos)
    if motivos_factura:
        resultado["requiere_revision_compra"] = True
        resultado["motivos_compra"].extend(motivos_factura)
    
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
