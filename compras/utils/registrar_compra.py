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
                import logging
                logger = logging.getLogger(__name__)
                
                inc = int(cantidad) if cantidad is not None else 0
                stock_antes = producto.stock or 0
                producto.stock = stock_antes + inc
                
                logger.warning(
                    f"[registrar_compra] SUMANDO STOCK: {producto.nombre} "
                    f"antes={stock_antes} incremento={inc} despues={producto.stock}"
                )
                
                producto.save(update_fields=["stock"])
            except Exception as e:
                # No detengas la compra si algo falla al sumar stock
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"[registrar_compra] Error sumando stock: {e}")
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
                    print(f"[VALIDACIÓN] Línea marcada para revisión: {instancia.producto.nombre} - Motivos: {instancia.motivo_revision}")
        
        # Validación adicional: Comparar suma esperada (BD) vs total factura
        total_factura = compra.total or Decimal("0")
        suma_esperada_bd = Decimal("0")
        
        for prod_map in productos_mapeados:
            instancia = prod_map.get("compra_producto_instance")
            if instancia and instancia.producto:
                cantidad = instancia.cantidad or 0
                precio_bd = instancia.producto.precio_compra or Decimal("0")
                suma_esperada_bd += cantidad * precio_bd
        
        if total_factura and suma_esperada_bd:
            diferencia = abs(total_factura - suma_esperada_bd)
            diferencia_pct = (diferencia / total_factura) if total_factura else Decimal("0")
            
            if diferencia_pct > Decimal("0.01"):  # >1% diferencia
                motivo_descuadre = (
                    f"total_no_cuadra_con_bd_"
                    f"esperado_{float(suma_esperada_bd):.2f}_"
                    f"factura_{float(total_factura):.2f}_"
                    f"diff_{float(diferencia_pct)*100:.2f}pct"
                )
                
                if not compra.requiere_revision_manual:
                    compra.requiere_revision_manual = True
                    compra.estado_revision = "pendiente"
                
                # Agregar motivo si no existe
                motivos_actuales = resultado_validacion.get('motivos_compra', [])
                if motivo_descuadre not in motivos_actuales:
                    motivos_actuales.append(motivo_descuadre)
                    resultado_validacion['motivos_compra'] = motivos_actuales
                
                print(f"[VALIDACIÓN] Descuadre de totales: Suma BD=${suma_esperada_bd:.2f} vs Factura=${total_factura:.2f} ({float(diferencia_pct)*100:.2f}%)")
        
        # Marcar la compra si requiere revisión
        if resultado_validacion.get("requiere_revision_compra") or compra.requiere_revision_manual:
            compra.requiere_revision_manual = True
            compra.estado_revision = "pendiente"
            compra.save(update_fields=["requiere_revision_manual", "estado_revision"])
            print(f"[VALIDACIÓN] Compra {compra.folio} marcada para revisión - Motivos: {resultado_validacion.get('motivos_compra')}")
            
            # Si es por IEPS especial (licor), marcar TODAS las líneas para revisión
            motivos_compra = resultado_validacion.get('motivos_compra', [])
            tiene_ieps_especial = any('ieps_30pct' in m or 'ieps_53pct' in m for m in motivos_compra)
            
            if tiene_ieps_especial:
                print(f"[VALIDACIÓN] Factura contiene licor (IEPS especial) - Marcando todas las líneas")
                for prod_map in productos_mapeados:
                    instancia = prod_map.get("compra_producto_instance")
                    if instancia and not instancia.requiere_revision_manual:
                        instancia.requiere_revision_manual = True
                        instancia.motivo_revision = "toda_factura_requiere_revision_por_contener_licor_ieps_30pct_o_53pct"
                        instancia.save(update_fields=["requiere_revision_manual", "motivo_revision"])
                        print(f"[VALIDACION]   - {instancia.producto.nombre} marcado para revision")
        else:
            print(f"[VALIDACIÓN] Compra {compra.folio} - Sin problemas detectados")
    except Exception as e:
        # No romper el flujo si falla la validación, pero mostrar error completo
        import traceback
        print(f"[ERROR] Error en validaciones automáticas: {e}")
        print(f"[ERROR] Traceback completo:")
        print(traceback.format_exc())
        print(f"[WARNING] Continuando sin validaciones...")

    return compra
