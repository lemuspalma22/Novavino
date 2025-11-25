# compras/signals.py
"""
Signals para mantener consistencia de stock y PNR al borrar compras.
"""
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import CompraProducto, Compra


@receiver(pre_delete, sender=CompraProducto)
def revertir_stock_al_borrar_compra_producto(sender, instance, **kwargs):
    """
    Al borrar un CompraProducto, resta la cantidad del stock del producto.
    Esto mantiene la consistencia cuando se elimina una compra completa.
    """
    try:
        producto = instance.producto
        cantidad = instance.cantidad or 0
        
        if producto and cantidad > 0:
            # Restar del stock
            producto.stock = max(0, (producto.stock or 0) - cantidad)
            producto.save(update_fields=["stock"])
    except Exception as e:
        # Log error pero no bloquear el borrado
        print(f"Error al revertir stock en CompraProducto {instance.id}: {e}")


@receiver(pre_delete, sender=Compra)
def borrar_pnr_asociados_al_borrar_compra(sender, instance, **kwargs):
    """
    Al borrar una Compra, elimina los ProductoNoReconocido asociados por UUID.
    Esto evita que queden PNR huérfanos que bloqueen el reprocesamiento.
    """
    try:
        from inventario.models import ProductoNoReconocido
        
        uuid = instance.uuid
        if uuid:
            # Borrar todos los PNR con el mismo UUID de factura
            pnr_asociados = ProductoNoReconocido.objects.filter(uuid_factura=uuid)
            count = pnr_asociados.count()
            if count > 0:
                pnr_asociados.delete()
                print(f"Borrados {count} ProductoNoReconocido asociados a Compra {instance.folio} (UUID: {uuid})")
    except Exception as e:
        # Log error pero no bloquear el borrado
        print(f"Error al borrar PNR asociados a Compra {instance.id}: {e}")
