# ventas/utils/registrar_venta.py
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.utils.timezone import now
from django.db import transaction  # ← FALTA EN TU ARCHIVO

from ventas.models import Factura, DetalleFactura
from inventario.models import ProductoNoReconocido
from inventario.utils import encontrar_producto_unico


def registrar_venta_automatizada(datos: dict, replace_if_exists: bool = False) -> Factura:
    """
    Crea/actualiza una Factura y sus DetalleFactura desde datos extraídos del PDF.
    - Idempotencia:
        * replace_if_exists=True: si existe el folio, borra detalles y recrea (signals ajustan stock).
        * replace_if_exists=False: si existe el folio, lanza ValueError (u omite fuera).
    - Transaccional: si una línea falla, no queda nada a medias.
    - Resolución con encontrar_producto_unico (evita ambigüedades).
    - Total: lo recalculan las signals al crear/borrar detalles; si no hay líneas válidas,
             se conserva el total extraído del PDF.
    """
    # Fecha
    fecha_raw = datos.get("fecha_emision") or datos.get("fecha")
    if isinstance(fecha_raw, str) and fecha_raw:
        fecha_raw = fecha_raw.replace("T", " ")
        fecha_dt = datetime.fromisoformat(fecha_raw)
    else:
        fecha_dt = fecha_raw

    # Total del PDF (solo si no hay líneas válidas)
    total_extraido = datos.get("total")
    try:
        total_decimal = Decimal(str(total_extraido)) if total_extraido is not None else Decimal("0")
    except InvalidOperation:
        total_decimal = Decimal("0")

    folio = str(datos.get("folio") or "").strip()
    if not folio:
        raise ValueError("Falta 'folio' en datos de la venta.")

    cliente = (datos.get("cliente") or "").strip()
    metodo_pago = datos.get("metodo_pago")  # PUE o PPD
    fecha_fact = fecha_dt.date() if fecha_dt else now().date()
    items = datos.get("productos") or datos.get("items") or []
    if not items:
        return Factura.objects.create(
            folio_factura=folio,
            cliente=cliente,
            fecha_facturacion=fecha_fact,
            total=total_decimal,
            metodo_pago=metodo_pago,
        )

    with transaction.atomic():
        # Idempotencia por folio
        try:
            factura = Factura.objects.get(folio_factura=folio)
            if not replace_if_exists:
                raise ValueError(f"Ya existe la venta con folio {folio}.")
            DetalleFactura.objects.filter(factura=factura).delete()  # signals restauran stock
            factura.cliente = cliente or factura.cliente
            factura.fecha_facturacion = fecha_fact or factura.fecha_facturacion
            factura.metodo_pago = metodo_pago or factura.metodo_pago
            factura.total = Decimal("0.00")  # se recalcula por signals
            factura.save(update_fields=["cliente", "fecha_facturacion", "metodo_pago", "total"])
        except Factura.DoesNotExist:
            factura = Factura.objects.create(
                folio_factura=folio,
                cliente=cliente,
                fecha_facturacion=fecha_fact,
                total=Decimal("0.00"),
                metodo_pago=metodo_pago,
            )

        detalles_creados = 0

        for prod in items:
            nombre = str(prod.get("nombre") or prod.get("producto") or "").strip()
            raw_cantidad = prod.get("cantidad", "0")
            raw_pu = prod.get("precio_unitario", "")

            # Validaciones mínimas
            try:
                cantidad = int(Decimal(str(raw_cantidad)))
            except Exception:
                cantidad = 0
            if not nombre or cantidad <= 0:
                if nombre:
                    ProductoNoReconocido.objects.get_or_create(
                        nombre_detectado=nombre,
                        defaults={"fecha_detectado": now(), "uuid_factura": datos.get("uuid") or "",
                                  "procesado": False, "origen": "venta"},
                    )
                continue

            # Resolver producto (seguro)
            producto, err = encontrar_producto_unico(nombre)
            if err == "not_found":
                ProductoNoReconocido.objects.get_or_create(
                    nombre_detectado=nombre,
                    defaults={"fecha_detectado": now(), "uuid_factura": datos.get("uuid") or "",
                              "procesado": False, "origen": "venta"},
                )
                raise ValueError(f"[{folio}] Producto '{nombre}' no encontrado.")
            if err == "ambiguous":
                raise ValueError(f"[{folio}] Producto '{nombre}' ambiguo.")

            # Precio unitario
            try:
                precio_unitario = Decimal(str(raw_pu)) if str(raw_pu).strip() != "" else (producto.precio_venta or Decimal("0"))
            except InvalidOperation:
                precio_unitario = producto.precio_venta or Decimal("0")

            DetalleFactura.objects.create(
                factura=factura,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
            )
            detalles_creados += 1

        if detalles_creados == 0:
            factura.total = total_decimal
            factura.save(update_fields=["total"])

        return factura
