from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from django.utils import timezone

from inventario.models import Producto


class Factura(models.Model):
    METODO_PAGO_CHOICES = [
        ('PUE', 'PUE - Pago en una sola exhibición'),
        ('PPD', 'PPD - Pago en parcialidades o diferido'),
    ]
    
    folio_factura = models.CharField(max_length=20, unique=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    cliente = models.CharField(max_length=100)
    fecha_facturacion = models.DateField()
    vencimiento = models.DateField(null=True, blank=True)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    metodo_pago = models.CharField(max_length=3, choices=METODO_PAGO_CHOICES, null=True, blank=True, help_text="Método de pago según el CFDI")
    notas = models.TextField(null=True, blank=True)

    # --- Validación de consistencia pagado/fecha_pago ---
    def clean(self):
        # Ambos vacíos -> ok (pendiente)
        # Ambos llenos -> ok (pagado)
        # Solo uno -> inválido
        if bool(self.pagado) != bool(self.fecha_pago):
            raise ValidationError(
                "Para marcar como pagada, 'Pagado' y 'Fecha de pago' deben ir ambos llenos; "
                "o ambos vacíos si está pendiente."
            )

    # --- Utilidades ya existentes / compatibles ---
    def recalc_total(self):
        expr = ExpressionWrapper(
            F("cantidad") * F("precio_unitario"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        agg = self.detalles.aggregate(s=Sum(expr))
        self.total = agg["s"] or Decimal("0.00")

    def save(self, *args, **kwargs):
        if not self.vencimiento:
            self.vencimiento = self.fecha_facturacion + timedelta(days=15)
        super().save(*args, **kwargs)

    @property
    def dias_transcurridos(self):
        dias = (timezone.now().date() - self.fecha_facturacion).days
        return max(dias, 0)

    @property
    def dias_vencido(self):
        if self.pagado:
            return "Pagado"
        dias_vencido = (timezone.now().date() - self.vencimiento).days
        return dias_vencido if dias_vencido > 0 else 0

    def calcular_total(self):
        self.total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.save(update_fields=["total"])

    def calcular_pagos_proveedores(self):
        pagos_por_proveedor = {}
        for detalle in self.detalles.all():
            proveedor = detalle.producto.proveedor
            pagos_por_proveedor[proveedor] = pagos_por_proveedor.get(proveedor, 0) + (
                detalle.cantidad * detalle.precio_compra
            )
        return pagos_por_proveedor

    def __str__(self):
        return f"Factura {self.folio_factura} - {self.cliente} - {'Pagada' if self.pagado else 'Pendiente'}"


class DetalleFactura(models.Model):
    factura = models.ForeignKey("ventas.Factura", on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey("inventario.Producto", on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # Precio de venta
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)    # Costo
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        # Si no viene costo, calcúlalo desde el producto (precio_compra + costo_transporte)
        if self.producto and (self.precio_compra is None or Decimal(self.precio_compra) == 0):
            precio_base = self.producto.precio_compra or Decimal("0.00")
            transporte = self.producto.costo_transporte or Decimal("0.00")
            # Costo total = precio de compra + transporte
            self.precio_compra = precio_base + transporte

        cant = Decimal(self.cantidad or 0)
        pvu = Decimal(self.precio_unitario or 0)
        self.subtotal = (cant * pvu).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        super().save(*args, **kwargs)
        if hasattr(self.factura, "calcular_total"):
            self.factura.calcular_total()

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} - {self.factura.folio_factura}"


class PagoFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name="pagos")
    fecha_pago = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        pagado_total = sum(p.monto for p in self.factura.pagos.all())
        if pagado_total >= self.factura.total:
            self.factura.pagado = True
            self.factura.fecha_pago = self.fecha_pago
        else:
            self.factura.pagado = False
            self.factura.fecha_pago = None
        self.factura.full_clean()
        self.factura.save(update_fields=["pagado", "fecha_pago"])

    def __str__(self):
        return f"Pago de {self.monto} para {self.factura.folio_factura} el {self.fecha_pago}"
