from django.db import models
from django.utils import timezone
from datetime import timedelta
from inventario.models import Producto  # Importamos el modelo Producto
#from .models import Factura  # Importamos las facturas

class Factura(models.Model):
    folio_factura = models.CharField(max_length=20, unique=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    cliente = models.CharField(max_length=100)
    fecha_facturacion = models.DateField()
    vencimiento = models.DateField(null=True, blank=True)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    notas = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.vencimiento:
            self.vencimiento = self.fecha_facturacion + timedelta(days=15)
        super().save(*args, **kwargs)

    @property
    def dias_transcurridos(self):
        dias = (timezone.now().date() - self.fecha_facturacion).days
        return max(dias, 0)  # Evita valores negativos


    @property
    def dias_vencido(self):
        if self.pagado:
            return "Pagado"
        else:
            dias_vencido = (timezone.now().date() - self.vencimiento).days
            return dias_vencido if dias_vencido > 0 else 0

    def calcular_total(self):
        """Recalcula el total de la factura basado en los detalles de factura."""
        self.total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.save()

    def calcular_pagos_proveedores(self):
        pagos_por_proveedor = {}
        for detalle in self.detalles.all():
            proveedor = detalle.producto.proveedor
            if proveedor not in pagos_por_proveedor:
                pagos_por_proveedor[proveedor] = 0
            pagos_por_proveedor[proveedor] += detalle.cantidad * detalle.precio_compra
        return pagos_por_proveedor  # Devuelve un diccionario {proveedor: total_pagado}
    

    def __str__(self):
        return f"Factura {self.folio_factura} - Cliente: {self.cliente} - {'Pagada' if self.pagado else 'Pendiente'}"


class DetalleFactura(models.Model):
    factura = models.ForeignKey("ventas.Factura", on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey("inventario.Producto", on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # Precio de venta unitario
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)  # Precio de compra
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # 🔹 Agregamos un valor por defecto

    def save(self, *args, **kwargs):
        # Obtener el precio de compra del producto
        self.precio_compra = self.producto.precio_compra
        # Calcular subtotal
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        self.factura.calcular_total()  # Recalcular total de la factura

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} - {self.factura.folio_factura}"



class PagoFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name="pagos")
    fecha_pago = models.DateField()  # Fecha del pago
    monto = models.DecimalField(max_digits=10, decimal_places=2)  # Cantidad pagada

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        pagos_realizados = sum(pago.monto for pago in self.factura.pagos.all())
        
        if pagos_realizados >= self.factura.total:
            self.factura.pagado = True
            self.factura.fecha_pago = self.fecha_pago
        else:
            self.factura.pagado = False
        
        self.factura.save()  # Actualizar el estado de la factura

    def __str__(self):
        return f"Pago de {self.monto} para {self.factura.folio_factura} el {self.fecha_pago}"