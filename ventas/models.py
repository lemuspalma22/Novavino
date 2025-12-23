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
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), help_text="Subtotal antes de descuentos")
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), help_text="Monto de descuento aplicado")
    cliente = models.CharField(max_length=100)
    fecha_facturacion = models.DateField()
    vencimiento = models.DateField(null=True, blank=True)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    metodo_pago = models.CharField(max_length=3, choices=METODO_PAGO_CHOICES, null=True, blank=True, help_text="Método de pago según el CFDI")
    notas = models.TextField(null=True, blank=True)
    
    # Campos de revisión (para productos no reconocidos)
    requiere_revision_manual = models.BooleanField(default=False, help_text="Indica si la factura requiere revisión manual por productos no reconocidos")
    estado_revision = models.CharField(
        max_length=30,
        choices=[
            ("pendiente", "Pendiente de revisión"),
            ("revisado_ok", "Revisado OK"),
            ("revisado_con_cambios", "Revisado con cambios"),
        ],
        default="pendiente",
        help_text="Estado de revisión de la factura"
    )
    uuid_factura = models.CharField(max_length=100, null=True, blank=True, help_text="UUID del CFDI para vincular con PNR")

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
        """Calcula el total de la factura: suma de productos - descuento."""
        suma_productos = sum(detalle.subtotal for detalle in self.detalles.all())
        self.subtotal = suma_productos
        # Total = subtotal - descuento
        self.total = max(Decimal("0.00"), suma_productos - (self.descuento or Decimal("0.00")))
        self.save(update_fields=["total", "subtotal"])

    def calcular_pagos_proveedores(self):
        pagos_por_proveedor = {}
        for detalle in self.detalles.all():
            proveedor = detalle.producto.proveedor
            pagos_por_proveedor[proveedor] = pagos_por_proveedor.get(proveedor, 0) + (
                detalle.cantidad * detalle.precio_compra
            )
        return pagos_por_proveedor
    
    # ========== FASE 1: PROPIEDADES PARA PAGOS PARCIALES ==========
    
    @property
    def costo_total(self):
        """Suma de costos de todos los productos incluyendo transporte (siempre recalcula)."""
        total = sum(
            detalle.cantidad * detalle.costo_con_transporte
            for detalle in self.detalles.all()
        )
        return Decimal(total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def ganancia_total(self):
        """Ganancia total de la factura (total - costo_total)."""
        return (self.total - self.costo_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def porcentaje_costo(self):
        """Porcentaje del total que representa el costo (para distribución proporcional)."""
        if self.total == 0:
            return Decimal("0.00")
        return (self.costo_total / self.total).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    
    @property
    def porcentaje_ganancia(self):
        """Porcentaje del total que representa la ganancia."""
        return (Decimal("1.00") - self.porcentaje_costo).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    
    @property
    def total_pagado(self):
        """Total de pagos recibidos hasta el momento.
        
        Compatible con sistema antiguo: si pagado=True pero no hay pagos, retorna el total.
        """
        total = sum(pago.monto for pago in self.pagos.all())
        
        # Compatibilidad: si está pagada con el sistema antiguo pero no tiene pagos registrados
        if self.pagado and total == 0:
            return self.total
        
        return Decimal(total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def saldo_pendiente(self):
        """Saldo que falta por pagar."""
        saldo = self.total - self.total_pagado
        return max(Decimal("0.00"), saldo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def estado_pago(self):
        """Estado del pago: pendiente, parcial, pagada, vencida.
        
        Compatible con sistema antiguo: si pagado=True, retorna 'pagada' directamente.
        """
        # Compatibilidad: si está marcada como pagada con el sistema antiguo
        if self.pagado:
            return "pagada"
        
        # Sistema nuevo: basado en pagos parciales
        if self.total_pagado == 0:
            # Sin pagos
            if self.vencimiento and timezone.now().date() > self.vencimiento:
                return "vencida"
            return "pendiente"
        elif self.total_pagado >= self.total:
            # Pagada completamente
            return "pagada"
        else:
            # Pago parcial
            if self.vencimiento and timezone.now().date() > self.vencimiento:
                return "vencida_parcial"  # Vencida pero con pagos parciales
            return "parcial"
    
    @property
    def costo_pagado(self):
        """Parte de los pagos destinada a cubrir costos (distribución proporcional)."""
        return (self.total_pagado * self.porcentaje_costo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def ganancia_pagada(self):
        """Parte de los pagos que es ganancia real (distribución proporcional)."""
        return (self.total_pagado * self.porcentaje_ganancia).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def costo_pendiente(self):
        """Costo que falta por recuperar en pagos pendientes."""
        return (self.saldo_pendiente * self.porcentaje_costo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def ganancia_pendiente(self):
        """Ganancia que falta por recibir en pagos pendientes."""
        return (self.saldo_pendiente * self.porcentaje_ganancia).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def __str__(self):
        return f"Factura {self.folio_factura} - {self.cliente} - {'Pagada' if self.pagado else 'Pendiente'}"


class DetalleFactura(models.Model):
    factura = models.ForeignKey("ventas.Factura", on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey("inventario.Producto", on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # Precio de venta
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)    # Costo
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['factura', 'producto'],
                name='unique_factura_producto'
            )
        ]
    
    @property
    def costo_con_transporte(self):
        """Costo real del producto incluyendo transporte (siempre recalcula desde el producto actual)."""
        precio_base = self.producto.precio_compra or Decimal("0.00")
        transporte = self.producto.costo_transporte or Decimal("0.00")
        return (precio_base + transporte).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

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
    """
    Registro de un pago (total o parcial) aplicado a una factura de venta.
    Permite trazabilidad completa y distribución proporcional de costos/ganancias.
    """
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta de crédito/débito'),
        ('deposito', 'Depósito bancario'),
        ('otro', 'Otro'),
    ]
    
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name="pagos")
    fecha_pago = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        default='efectivo',
        help_text="Método de pago utilizado"
    )
    referencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Número de transferencia, cheque, etc."
    )
    notas = models.TextField(
        blank=True,
        null=True,
        help_text="Notas adicionales sobre el pago"
    )
    creado_en = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_pago', '-creado_en']
        verbose_name = "Pago de Factura"
        verbose_name_plural = "Pagos de Facturas"
    
    # ========== FASE 4: DISTRIBUCIÓN PROPORCIONAL ==========
    
    @property
    def monto_costo(self):
        """Parte del pago destinada a cubrir costos (distribución proporcional)."""
        return (self.monto * self.factura.porcentaje_costo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def monto_ganancia(self):
        """Parte del pago que es ganancia neta (distribución proporcional)."""
        return (self.monto * self.factura.porcentaje_ganancia).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def clean(self):
        """Validaciones del pago."""
        if self.monto <= 0:
            raise ValidationError("El monto del pago debe ser mayor a cero.")
        
        # Validar que el pago no exceda el saldo pendiente (con warning)
        if self.factura_id:
            saldo = self.factura.saldo_pendiente
            # Si estamos editando, excluir este pago del cálculo
            if self.pk:
                pagos_otros = self.factura.pagos.exclude(pk=self.pk)
                total_otros = sum(p.monto for p in pagos_otros)
                saldo = self.factura.total - total_otros
            
            if self.monto > saldo:
                # Permitir sobrepago pero advertir
                pass  # Podrías lanzar un warning aquí si Django lo soporta

    def save(self, *args, **kwargs):
        # Validar antes de guardar
        self.full_clean()
        
        super().save(*args, **kwargs)
        
        # Actualizar estado de la factura
        pagado_total = sum(p.monto for p in self.factura.pagos.all())
        if pagado_total >= self.factura.total:
            self.factura.pagado = True
            self.factura.fecha_pago = self.fecha_pago  # Última fecha de pago
        else:
            self.factura.pagado = False
            self.factura.fecha_pago = None
        
        # No llamar full_clean de factura para evitar validación de pagado/fecha_pago
        # porque estamos en medio de actualizar esos campos
        self.factura.save(update_fields=["pagado", "fecha_pago"])

    def __str__(self):
        return f"Pago ${self.monto} - {self.factura.folio_factura} ({self.fecha_pago})"
