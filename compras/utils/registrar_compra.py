# compras/utils/registrar_compra.py
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from typing import Any

from django.utils.timezone import now

from compras.models import Compra, CompraProducto
from inventario.models import Producto, ProductoNoReconocido
from inventario.utils import encontrar_producto_unico
from utils.utils_validacion import es_producto_valido
from compras.utils.validation import aplicar_validaciones_a_compra

def _D(x):
    if x is None or x == "":
        return None
    try:
        return Decimal(str(x).replace(",", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return None

def _to_json_safe(obj: Any) -> Any:
    """Convierte Decimal, date, datetime a string recursivamente para JSONField."""
    if isinstance(obj, (Decimal, date, datetime)):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_json_safe(x) for x in obj]
    return obj

def _parse_fecha_emision(fecha_raw):
    if isinstance(fecha_raw, datetime):
        return fecha_raw
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(str(fecha_raw), fmt)
        except Exception:
            continue
    # Último recurso: ahora
    return now()

def registrar_compra_automatizada(datos_extraidos: dict) -> Compra:
    # ---- Cabecera de compra ----
    fecha = _parse_fecha_emision(datos_extraidos.get("fecha_emision"))
    fecha_compra = fecha.date()

    compra = Compra.objects.create(
        folio = datos_extraidos.get("folio"),
        total = _D(datos_extraidos.get("total")) or Decimal("0"),
        proveedor = datos_extraidos.get("proveedor"),   # debe venir instancia FK
        fecha = fecha_compra,
        uuid  = datos_extraidos.get("uuid") or datos_extraidos.get("uuid_sat"),
    )

    # ---- Recolectar info para validaciones ----
    productos_mapeados = []
    productos_creados = []  # Lista de instancias CompraProducto creadas

    # ---- Detalle / productos ----
    for item in (datos_extraidos.get("productos") or []):
        nombre = (item.get("nombre") or item.get("nombre_detectado") or "").strip()
        if not nombre:
            continue
        if not es_producto_valido(nombre):
            continue

        cantidad = _D(item.get("cantidad")) or Decimal("0")
        precio_unitario = _D(item.get("precio_unitario")) or Decimal("0")

        # Resolver producto de forma unificada (nombre/alias/soft match)
        producto, err = encontrar_producto_unico(nombre)

        if producto:
            # Crea línea de compra
            det_kwargs = dict(
                compra=compra,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
            )
            if hasattr(CompraProducto, "importe"):
                try:
                    det_kwargs["importe"] = (cantidad or 0) * (precio_unitario or 0)
                except Exception:
                    pass
            compra_producto = CompraProducto.objects.create(**det_kwargs)
            productos_creados.append(compra_producto)
            
            # Recolectar para validación
            productos_mapeados.append({
                "concepto": item,
                "producto": producto,
                "nombre": nombre,
                "compra_producto_instance": compra_producto
            })

            # Suma a stock (tu modelo Producto tiene campo 'stock' entero)
            try:
                inc = int(cantidad) if cantidad is not None else 0
                producto.stock = (producto.stock or 0) + inc
                producto.save(update_fields=["stock"])
            except Exception:
                # No detengas la compra si algo falla al sumar stock
                pass

        else:
            # --- No hubo match → crear "Producto no reconocido" con snapshot y prefill ---
            conceptos = datos_extraidos.get("conceptos") or []

            # prefill desde primera línea si faltan
            if (cantidad is None or cantidad == 0 or precio_unitario is None or precio_unitario == 0) and conceptos:
                first = conceptos[0]
                cantidad = _D(cantidad) or _D(first.get("cantidad")) or Decimal("1")
                precio_unitario = _D(precio_unitario) or _D(first.get("precio_unitario")) or None

            ProductoNoReconocido.objects.create(
                nombre_detectado = nombre or (conceptos and conceptos[0].get("descripcion")) or "POR CLASIFICAR",
                fecha_detectado  = now(),
                uuid_factura     = datos_extraidos.get("uuid") or datos_extraidos.get("uuid_sat"),
                procesado        = False,
                origen           = "compra",
                cantidad         = cantidad,
                precio_unitario  = precio_unitario,
                raw_conceptos    = _to_json_safe(conceptos) if conceptos else None,  # JSONField: convertir Decimal a str
            )
            
            # Recolectar para validación (sin producto mapeado)
            productos_mapeados.append({
                "concepto": item,
                "producto": None,
                "nombre": nombre,
                "compra_producto_instance": None
            })

    # ---- Aplicar validaciones y marcar flags ----
    try:
        resultado_validacion = aplicar_validaciones_a_compra(datos_extraidos, productos_mapeados)
        
        # Marcar líneas individuales
        for idx, info_validacion in enumerate(resultado_validacion.get("lineas_revision", [])):
            if idx < len(productos_mapeados):
                instancia = productos_mapeados[idx].get("compra_producto_instance")
                if instancia and info_validacion.get("requiere_revision"):
                    instancia.requiere_revision_manual = True
                    instancia.motivo_revision = ";".join(info_validacion.get("motivos", []))
                    instancia.save(update_fields=["requiere_revision_manual", "motivo_revision"])
        
        # Marcar la compra si requiere revisión
        if resultado_validacion.get("requiere_revision_compra"):
            compra.requiere_revision_manual = True
            compra.estado_revision = "pendiente"
            compra.save(update_fields=["requiere_revision_manual", "estado_revision"])
    except Exception as e:
        # No romper el flujo si falla la validación
        print(f"[WARNING] Error en validaciones automáticas: {e}")

    return compra
