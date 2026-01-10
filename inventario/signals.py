# inventario/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

PNR = apps.get_model("inventario", "ProductoNoReconocido")

@receiver(post_save, sender=PNR)
def producto_no_reconocido_post_save(sender, instance, created, **kwargs):
    """
    Si se marcó como procesado y tiene producto asignado, ingresa a stock y (si aplica) crea detalle.
    Se protege con movimiento_generado para no duplicar.
    """
    try:
        procesado = getattr(instance, "procesado", False)
        producto_id = getattr(instance, "producto_id", None)
        movimiento = getattr(instance, "movimiento_generado", False)
        
        logger.warning(
            f"[SIGNAL] PNR={instance.id} nombre={instance.nombre_detectado} "
            f"procesado={procesado} producto_id={producto_id} "
            f"movimiento_generado={movimiento} created={created}"
        )
        
        if procesado and producto_id:
            if not movimiento:
                logger.warning(f"[SIGNAL] Llamando procesar_a_stock() para PNR={instance.id}")
                instance.procesar_a_stock()
                logger.warning(f"[SIGNAL] procesar_a_stock() completado para PNR={instance.id}")
            else:
                logger.warning(f"[SIGNAL] Saltando procesar_a_stock() - movimiento ya generado")
    except Exception as e:
        # Evitar romper el guardado del admin; revisa logs si algo no cuadra
        logger.error(f"[SIGNAL] Error en PNR {instance.id}: {e}", exc_info=True)
        pass
