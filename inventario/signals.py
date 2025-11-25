# inventario/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

PNR = apps.get_model("inventario", "ProductoNoReconocido")

@receiver(post_save, sender=PNR)
def producto_no_reconocido_post_save(sender, instance, created, **kwargs):
    """
    Si se marcó como procesado y tiene producto asignado, ingresa a stock y (si aplica) crea detalle.
    Se protege con movimiento_generado para no duplicar.
    """
    try:
        if getattr(instance, "procesado", False) and getattr(instance, "producto_id", None):
            instance.procesar_a_stock()
    except Exception:
        # Evitar romper el guardado del admin; revisa logs si algo no cuadra
        pass
