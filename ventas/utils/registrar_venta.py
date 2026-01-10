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

    # Montos del PDF
    total_extraido = datos.get("total")
    subtotal_extraido = datos.get("subtotal")
    descuento_extraido = datos.get("descuento")
    
    try:
        total_decimal = Decimal(str(total_extraido)) if total_extraido is not None else Decimal("0")
    except InvalidOperation:
        total_decimal = Decimal("0")
    
    try:
        subtotal_decimal = Decimal(str(subtotal_extraido)) if subtotal_extraido is not None else Decimal("0")
    except InvalidOperation:
        subtotal_decimal = Decimal("0")
    
    try:
        descuento_decimal = Decimal(str(descuento_extraido)) if descuento_extraido is not None else Decimal("0")
    except InvalidOperation:
        descuento_decimal = Decimal("0")

    folio = str(datos.get("folio") or "").strip()
    if not folio:
        raise ValueError("Falta 'folio' en datos de la venta.")

    cliente = (datos.get("cliente") or "").strip()
    metodo_pago = datos.get("metodo_pago")  # PUE o PPD
    uuid_cfdi = datos.get("uuid") or ""
    fecha_fact = fecha_dt.date() if fecha_dt else now().date()
    items = datos.get("productos") or datos.get("items") or []
    if not items:
        return Factura.objects.create(
            folio_factura=folio,
            cliente=cliente,
            fecha_facturacion=fecha_fact,
            subtotal=subtotal_decimal,
            descuento=descuento_decimal,
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
            factura.subtotal = Decimal("0.00")  # se recalcula por signals
            factura.descuento = descuento_decimal  # conservar descuento del PDF
            factura.total = Decimal("0.00")  # se recalcula por signals
            factura.save(update_fields=["cliente", "fecha_facturacion", "metodo_pago", "subtotal", "descuento", "total"])
        except Factura.DoesNotExist:
            factura = Factura.objects.create(
                folio_factura=folio,
                cliente=cliente,
                fecha_facturacion=fecha_fact,
                subtotal=Decimal("0.00"),
                descuento=descuento_decimal,
                total=Decimal("0.00"),
                metodo_pago=metodo_pago,
                uuid_factura=uuid_cfdi,
            )

        detalles_creados = 0
        productos_no_reconocidos = 0

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
                    productos_no_reconocidos += 1  # BUG FIX: incrementar contador
                continue

            # Resolver producto (seguro)
            producto, err = encontrar_producto_unico(nombre)
            if err == "not_found":
                # Guardar info adicional en PNR para poder procesar después
                ProductoNoReconocido.objects.get_or_create(
                    nombre_detectado=nombre,
                    uuid_factura=uuid_cfdi,
                    defaults={
                        "fecha_detectado": now(),
                        "procesado": False,
                        "origen": "venta",
                        "cantidad": Decimal(str(cantidad)),
                        "precio_unitario": Decimal(str(raw_pu)) if str(raw_pu).strip() else None,
                    },
                )
                productos_no_reconocidos += 1
                continue  # NO lanzar error, solo registrar PNR y continuar
            if err == "ambiguous":
                # Producto ambiguo también es un caso para revisión manual
                ProductoNoReconocido.objects.get_or_create(
                    nombre_detectado=nombre,
                    uuid_factura=uuid_cfdi,
                    defaults={
                        "fecha_detectado": now(),
                        "procesado": False,
                        "origen": "venta",
                        "cantidad": Decimal(str(cantidad)),
                        "precio_unitario": Decimal(str(raw_pu)) if str(raw_pu).strip() else None,
                    },
                )
                productos_no_reconocidos += 1
                continue

            # Precio unitario
            try:
                precio_unitario = Decimal(str(raw_pu)) if str(raw_pu).strip() != "" else (producto.precio_venta or Decimal("0"))
            except InvalidOperation:
                precio_unitario = producto.precio_venta or Decimal("0")

            # Usar get_or_create para evitar duplicados y sumar cantidades
            detalle, created = DetalleFactura.objects.get_or_create(
                factura=factura,
                producto=producto,
                defaults={
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario,
                }
            )
            
            if not created:
                # Ya existía: SUMAR la cantidad
                detalle.cantidad += cantidad
                detalle.save(update_fields=["cantidad"])
            
            detalles_creados += 1

        # Si hay productos no reconocidos, marcar factura para revisión
        if productos_no_reconocidos > 0:
            factura.requiere_revision_manual = True
            factura.estado_revision = "pendiente"
            factura.save(update_fields=["requiere_revision_manual", "estado_revision"])
        
        if detalles_creados == 0:
            factura.subtotal = subtotal_decimal
            factura.descuento = descuento_decimal
            factura.total = total_decimal
            factura.save(update_fields=["subtotal", "descuento", "total"])
        else:
            # IMPORTANTE: Restaurar subtotal, descuento y total del PDF después de que los signals recalcularon
            # Los signals suman los detalles como subtotal, pero los montos oficiales deben ser los del CFDI
            # Esto mantiene la integridad fiscal y hace que la caja cuadre correctamente
            factura.refresh_from_db()  # Obtener valores recalculados por signals
            
            # Si el PDF no trae subtotal, usar la suma calculada por signals
            if subtotal_decimal > 0:
                factura.subtotal = subtotal_decimal
            # else: mantener el subtotal calculado por signals
            
            factura.descuento = descuento_decimal  # Conservar descuento del PDF
            factura.total = total_decimal  # Restaurar el total del PDF
            factura.save(update_fields=["subtotal", "descuento", "total"])

        return factura
