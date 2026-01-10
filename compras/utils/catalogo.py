# compras/utils/catalogo.py
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional
from django.apps import apps
from django.db.models import Q
import os

# ========= Helpers de app/modelo =========
def _get_model(app_label: str, model_name: str):
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None

# Tus modelos están en 'inventario'
Producto = _get_model("inventario", "Producto")
AliasProducto = _get_model("inventario", "AliasProducto")
# ProductoNoReconocido LO CREA registrar_compra.py cuando no encuentra el Producto.
# No lo importamos aquí para no duplicar lógica.

# ========= Helpers de valores =========
def _D(x, default="0"):
    try:
        return Decimal(str(x))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)

def _norm(x) -> str:
    return str(x or "").strip()

def _first(*vals):
    for v in vals:
        if v is not None and _norm(v) != "":
            return v
    return None

# ========= Resolución de alias/nombre =========
def _resolve_nombre_producto(nombre_o_desc: str) -> Optional[str]:
    """
    Devuelve el nombre oficial del Producto si hay match por:
      1) Producto.nombre (iexact)
      2) AliasProducto.alias (iexact) -> Producto.nombre
    Si no hay match, devuelve None.
    """
    if not nombre_o_desc:
        return None
    txt = nombre_o_desc.strip()

    # 1) Match directo por nombre de Producto
    if Producto:
        p = Producto.objects.filter(nombre__iexact=txt).first()
        if p:
            return p.nombre

    # 2) Match por AliasProducto
    if AliasProducto:
        alias = AliasProducto.objects.filter(alias__iexact=txt).first()
        if alias and getattr(alias, "producto", None):
            # usamos el nombre oficial del producto destino
            return alias.producto.nombre

    return None

# ========= Builder principal =========
def ensure_product_list_for_registrar(data: dict, proveedor_nombre: str = "") -> List[Dict[str, Any]]:
    """
    Construye data["productos"] con el formato que espera registrar_compra_automatizada:
      - Cada item: {"nombre" (o "nombre_detectado"), "cantidad", "precio_unitario"}
    Intenta resolver alias -> reemplaza por Producto.nombre para que registre directo.
    Si la factura no trae conceptos y CREATE_UNRECOGNIZED_WHEN_EMPTY=1, crea 1 item con 'nombre_detectado'.
    
    IMPORTANTE: Prorrateo de impuestos (IVA, IEPS, etc.) al precio_unitario:
      - Si hay subtotal y total, calcula impuestos_totales = total - subtotal.
      - Para cada concepto, prorratea impuestos según su proporción del subtotal.
      - precio_unitario final = (importe_neto + impuestos_prorrateados) / cantidad.
    """
    productos = []
    conceptos = data.get("conceptos") or data.get("productos") or []
    
    # Prorrateo de impuestos
    subtotal = _D(data.get("subtotal") or 0)
    total = _D(data.get("total") or 0)
    impuestos_totales = total - subtotal if (total and subtotal and total > subtotal) else Decimal(0)

    for c in conceptos:
        if not isinstance(c, dict):
            continue

        # Extraer valores
        desc = _first(c.get("descripcion"), c.get("nombre"), c.get("producto"))
        cantidad = _D(c.get("cantidad"), "1")

        precio_unitario_neto = None
        if c.get("precio_unitario") not in (None, ""):
            precio_unitario_neto = _D(c.get("precio_unitario"))

        importe_neto = None
        if c.get("importe") not in (None, ""):
            importe_neto = _D(c.get("importe"))

        # Completar faltantes
        if precio_unitario_neto is None and (importe_neto is not None) and cantidad:
            try:
                precio_unitario_neto = (importe_neto / cantidad)
            except Exception:
                pass
        
        if importe_neto is None and precio_unitario_neto is not None and cantidad:
            importe_neto = precio_unitario_neto * cantidad

        # Prorratear impuestos a esta línea
        precio_unitario_bruto = precio_unitario_neto
        if impuestos_totales and subtotal and importe_neto:
            try:
                proporcion = importe_neto / subtotal
                impuestos_linea = impuestos_totales * proporcion
                importe_bruto = importe_neto + impuestos_linea
                precio_unitario_bruto = importe_bruto / cantidad if cantidad else importe_bruto
            except Exception:
                pass

        # Resolver alias -> nombre oficial (si existe)
        nombre_resuelto = _resolve_nombre_producto(_norm(desc))
        if nombre_resuelto:
            item = {
                "nombre": nombre_resuelto,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario_bruto if precio_unitario_bruto is not None else _D(0),
            }
        else:
            # Sin match: pasamos 'nombre' literal; si no existe, registrar_compra creará ProductoNoReconocido
            item = {
                "nombre": _norm(desc),
                "cantidad": cantidad,
                "precio_unitario": precio_unitario_bruto if precio_unitario_bruto is not None else _D(0),
            }

        productos.append(item)

    # Si no hay conceptos y queremos un "no reconocido" único (fallback)
    if not productos and os.getenv("CREATE_UNRECOGNIZED_WHEN_EMPTY", "0") in ("1", "true", "True"):
        # registrar_compra acepta 'nombre' o 'nombre_detectado'
        etiqueta = f"POR CLASIFICAR – {proveedor_nombre}" if proveedor_nombre else "POR CLASIFICAR"
        total = _D(data.get("total") or 0)
        productos.append({
            "nombre_detectado": etiqueta,      # registrar_compra lo usará como nombre
            "cantidad": _D(1),
            "precio_unitario": total,
        })

    data["productos"] = productos
    return productos
