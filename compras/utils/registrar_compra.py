from compras.models import Compra, CompraProducto
from inventario.models import Producto, ProductoNoReconocido
from django.utils.timezone import now
from datetime import datetime
from utils.utils_validacion import es_producto_valido


def registrar_compra_automatizada(datos_extraidos: dict) -> Compra:
    fecha_raw = datos_extraidos["fecha_emision"]
    fecha = fecha_raw if isinstance(fecha_raw, datetime) else datetime.fromisoformat(str(fecha_raw))
    fecha_compra = fecha.date()

    compra = Compra.objects.create(
        folio=datos_extraidos["folio"],
        total=datos_extraidos["total"],
        proveedor=datos_extraidos["proveedor"],
        fecha=fecha_compra,
        uuid=datos_extraidos["uuid"],
    )

    for prod in datos_extraidos["productos"]:
        nombre = prod.get("nombre") or prod.get("nombre_detectado")
        if not nombre:
            continue
        nombre = nombre.strip()

        cantidad = prod["cantidad"]
        precio_unitario = prod["precio_unitario"]

        if not es_producto_valido(nombre):
            continue

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