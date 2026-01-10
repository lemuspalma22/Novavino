# ventas/signals.py
from decimal import Decimal
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from django.core.mail import send_mail
from django.conf import settings

from ventas.models import DetalleFactura, Factura, PagoFactura
from inventario.models import Producto

def _recalc_factura_total(factura):
    expr = ExpressionWrapper(
        F("cantidad") * F("precio_unitario"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    agg = factura.detalles.aggregate(s=Sum(expr))
    factura.total = agg["s"] or Decimal("0.00")
    factura.save(update_fields=["total"])

@receiver(pre_save, sender=DetalleFactura)
def _cache_old_qty(sender, instance, **kwargs):
    # Guarda la cantidad previa para calcular deltas en updates
    if instance.pk:
        old = sender.objects.filter(pk=instance.pk).values_list("cantidad", flat=True).first()
        instance._old_qty = old or 0
    else:
        instance._old_qty = 0

@receiver(post_save, sender=DetalleFactura)
def _on_detalle_save(sender, instance, created, **kwargs):
    # Ajuste de stock (venta => descuenta)
    producto = getattr(instance, "producto", None)
    if isinstance(producto, Producto):
        nueva = (instance.cantidad or 0)
        vieja = getattr(instance, "_old_qty", 0) or 0
        delta = nueva if created else (nueva - vieja)
        if delta:
            p = producto
            p.stock = max(0, (p.stock or 0) - delta)
            p.save(update_fields=["stock"])

    # Recalcular total de la factura
    _recalc_factura_total(instance.factura)

@receiver(post_delete, sender=DetalleFactura)
def _on_detalle_delete(sender, instance, **kwargs):
    # Restaurar stock al eliminar el detalle
    producto = getattr(instance, "producto", None)
    if isinstance(producto, Producto):
        qty = instance.cantidad or 0
        if qty:
            p = producto
            p.stock = (p.stock or 0) + qty
            p.save(update_fields=["stock"])

    # Recalcular total
    _recalc_factura_total(instance.factura)


@receiver(pre_delete, sender=Factura)
def borrar_pnr_asociados_al_borrar_factura(sender, instance, **kwargs):
    """
    Al borrar una Factura, elimina los ProductoNoReconocido asociados por UUID.
    Esto evita que queden PNR huérfanos que bloqueen el reprocesamiento.
    Similar al signal en compras/signals.py para Compra.
    """
    try:
        from inventario.models import ProductoNoReconocido
        
        uuid = instance.uuid_factura
        if uuid:
            # Borrar todos los PNR con el mismo UUID de factura
            pnr_asociados = ProductoNoReconocido.objects.filter(
                uuid_factura=uuid,
                origen="venta"
            )
            count = pnr_asociados.count()
            if count > 0:
                pnr_asociados.delete()
                print(f"Borrados {count} ProductoNoReconocido asociados a Factura {instance.folio_factura} (UUID: {uuid})")
    except Exception as e:
        # Log error pero no bloquear el borrado
        print(f"Error al borrar PNR asociados a Factura {instance.id}: {e}")


@receiver(post_save, sender=PagoFactura)
def notificar_pago_ppd_a_contabilidad(sender, instance, created, **kwargs):
    """
    Envía email al equipo de contabilidad cuando se registra un pago
    para una factura con método PPD (Pago en Parcialidades o Diferido).
    
    Esto alerta al contador para que genere el Complemento de Pago correspondiente.
    """
    if not created:
        return  # Solo notificar en creación, no en ediciones
    
    factura = instance.factura
    
    # Solo notificar si la factura es PPD
    if factura.metodo_pago != 'PPD':
        return
    
    # Preparar destinatarios según ambiente
    if getattr(settings, 'DEBUG', True):
        # Ambiente de pruebas
        destinatarios = [
            'mariolnovavino@gmail.com',
            'rlemusnovavino@gmail.com'
        ]
    else:
        # Producción
        destinatarios = [
            'despacho.cg@hotmail.com',
            'mariolnovavino@gmail.com'
        ]
    
    # Preparar mensaje
    asunto = f'⚠️ Generar Complemento de Pago - Factura {factura.folio_factura}'
    
    mensaje = f"""
Hola equipo de contabilidad,

Se ha registrado un pago para una factura con método PPD que requiere la emisión de un Complemento de Pago.

📄 DATOS DE LA FACTURA:
   • Folio: {factura.folio_factura}
   • Cliente: {factura.cliente}
   • Total factura: ${factura.total:,.2f}
   • Método de pago: PPD (Pago en Parcialidades o Diferido)
   • UUID: {factura.uuid_factura or 'N/A'}

💰 PAGO REGISTRADO:
   • Monto: ${instance.monto:,.2f}
   • Fecha: {instance.fecha_pago.strftime('%d/%m/%Y')}
   • Método: {instance.get_metodo_pago_display()}
   • Referencia: {instance.referencia or 'N/A'}

📊 ESTADO DE LA FACTURA:
   • Total pagado: ${factura.total_pagado:,.2f}
   • Saldo pendiente: ${factura.saldo_pendiente:,.2f}
   • Estado: {factura.estado_pago.upper()}

⚡ ACCIÓN REQUERIDA:
   Por favor, generar el Complemento de Pago correspondiente en el sistema del SAT
   y posteriormente subirlo al sistema para su vinculación.

---
Sistema Novavino CRM
Este es un mensaje automático, no responder.
    """.strip()
    
    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@novavino.com'),
            recipient_list=destinatarios,
            fail_silently=False,
        )
        print(f"✅ Email enviado a contabilidad para factura PPD {factura.folio_factura}")
    except Exception as e:
        # Log error pero no bloquear el guardado del pago
        print(f"⚠️ Error al enviar email de notificación: {e}")
