# ventas/utils/registrar_venta.py
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from decimal import Decimal
from datetime import datetime
from django.utils.timezone import now

from ventas.models import Factura, DetalleFactura
from inventario.models import Producto, AliasProducto, ProductoNoReconocido


def _resolver_producto(nombre_detectado: str):
    """
    Intenta resolver un Producto a partir del nombre detectado:
      1) Coincidencia exacta por nombre
      2) Alias (AliasProducto.alias__iexact)
    Retorna Producto o None.
    """
    nombre = nombre_detectado.strip()

    # 1) nombre exacto
    prod = Producto.objects.filter(nombre__iexact=nombre).first()
    if prod:
        return prod

    # 2) alias
    alias = AliasProducto.objects.filter(alias__iexact=nombre).select_related("producto").first()
    if alias:
        return alias.producto

    return None


def registrar_venta_automatizada(datos: dict) -> Factura:
    """
    Crea la Factura y sus DetalleFactura si los productos son reconocidos.
    Si un producto no existe, crea un ProductoNoReconocido (origen='venta').
    SOLO recalcula el total si hubo al menos un detalle creado; de lo contrario
    conserva el total extraído del PDF.
    """
    # Normaliza/convierte tipos
    fecha_raw = datos.get("fecha_emision")
    if isinstance(fecha_raw, str):
        # acepta "2025-04-14T17:06:29" o "2025-04-14 17:06:29"
        fecha_raw = fecha_raw.replace("T", " ")
        fecha_dt = datetime.fromisoformat(fecha_raw)
    else:
        fecha_dt = fecha_raw  # ya es datetime

    total_extraido = datos.get("total")
    total_decimal = Decimal(str(total_extraido)) if total_extraido is not None else Decimal("0")

    factura = Factura.objects.create(
        folio_factura=str(datos.get("folio")).strip(),
        total=total_decimal,  # asignamos el total del PDF por defecto
        cliente=datos.get("cliente") or "",
        fecha_facturacion=fecha_dt.date() if fecha_dt else now().date(),
    )

    detalles_creados = 0

    for prod in datos.get("productos", []):
        nombre = str(prod.get("nombre", "")).strip()
        cantidad = Decimal(str(prod.get("cantidad", "0")))
        precio_unitario = Decimal(str(prod.get("precio_unitario", "0")))

        if not nombre or cantidad <= 0 or precio_unitario <= 0:
            # línea inválida; registramos como no reconocido para inspección
            if nombre:
                ProductoNoReconocido.objects.get_or_create(
                    nombre_detectado=nombre,
                    defaults={
                        "fecha_detectado": now(),
                        "uuid_factura": datos.get("uuid") or "",
                        "procesado": False,
                        "origen": "venta",
                    },
                )
            continue

        producto = _resolver_producto(nombre)

        if producto:
            DetalleFactura.objects.create(
                factura=factura,
                producto=producto,
                cantidad=int(cantidad),            # tu modelo usa IntegerField
                precio_unitario=precio_unitario,   # ya trae impuestos (según extractor)
                # precio_compra se llena en save() desde producto.precio_compra
            )
            detalles_creados += 1
        else:
            # Guardamos el nombre para que lo conviertas en alias desde el Admin
            ProductoNoReconocido.objects.get_or_create(
                nombre_detectado=nombre,
                defaults={
                    "fecha_detectado": now(),
                    "uuid_factura": datos.get("uuid") or "",
                    "procesado": False,
                    "origen": "venta",
                },
            )

    # ✅ Solo recalcular si hubo al menos un detalle creado.
    if detalles_creados > 0:
        factura.calcular_total()
    # si no hubo detalles, se conserva el total extraído (no lo pisamos con 0)

    return factura
