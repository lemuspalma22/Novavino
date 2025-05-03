from compras.models import Compra, CompraProducto
from inventario.models import Producto, ProductoNoReconocido
from datetime import datetime
from django.utils.timezone import now
import re

def es_producto_valido(nombre: str) -> bool:
    nombre = nombre.strip()
    if not nombre:
        return False

    if re.fullmatch(r"[\d,.]+", nombre):
        return False

    patrones_prohibidos = [
        r"^IEPS", r"^IVA", r"^pz$", r"^CP:", r"^\d{5}$", r"Comprobante", r"Pago", r"Emisión",
        r"^Fecha", r"^NOMBRE:", r"^RFC", r"^Uso CFDI", r"^Subtotal", r"^Total", r"^Importe",
        r"[A-Z]{5,}[0-9]{2,}"  # Posibles RFC o certificados
    ]

    for patron in patrones_prohibidos:
        if re.search(patron, nombre, re.IGNORECASE):
            return False

    return True

def registrar_compra_automatizada(datos_extraidos: dict) -> Compra:
    fecha_raw = datos_extraidos["fecha_emision"]
    fecha = fecha_raw if isinstance(fecha_raw, datetime) else datetime.fromisoformat(str(fecha_raw))
    fecha_compra = fecha.date()

    compra = Compra.objects.create(
        folio=datos_extraidos["folio"],
        total=datos_extraidos["total"],
        proveedor=datos_extraidos["proveedor"],
        fecha=fecha_compra
    )

    for prod in datos_extraidos["productos"]:
        nombre = prod["nombre"].strip()
        cantidad = prod["cantidad"]
        precio_unitario = prod["precio_unitario"]

        if not es_producto_valido(nombre):
            continue  # Ignorar líneas no válidas

        producto = Producto.objects.filter(nombre__iexact=nombre).first()

        if producto:
            CompraProducto.objects.create(
                compra=compra,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )
            producto.stock += int(cantidad)
            producto.save()
        else:
            ProductoNoReconocido.objects.create(
                nombre_detectado=nombre,
                fecha_detectado=now(),
                uuid_factura=datos_extraidos["uuid"],
                procesado=False,
                origen="compra"
            )

    return compra
