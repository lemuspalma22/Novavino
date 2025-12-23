from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    costo_transporte_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Costo de transporte por unidad/botella. Ej: $15.00 para Secretos de la Vid"
    )

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='productos_compras')
    precio = models.DecimalField(max_digits=10, decimal_places=2)  # Precio unitario del producto

    def __str__(self):
        return f"{self.nombre} - {self.proveedor.nombre}"

class Compra(models.Model):
    uuid = models.CharField(max_length=100, unique=True)
    folio = models.CharField(max_length=20)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    revision = models.BooleanField(default=False)
    archivo = models.FileField(upload_to='compras_archivos/', null=True, blank=True)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    complemento_pago = models.CharField(max_length=100, null=True, blank=True)
    notas = models.TextField(null=True, blank=True)
    
    # Campos de revisión manual
    requiere_revision_manual = models.BooleanField(default=False, help_text="Indica si la compra requiere revisión humana")
    estado_revision = models.CharField(
        max_length=20,
        choices=[
            ("pendiente", "Pendiente"),
            ("revisado_ok", "Revisado OK"),
            ("revisado_con_cambios", "Revisado con cambios")
        ],
        default="pendiente",
        help_text="Estado de la revisión manual"
    )

    @property
    def estado(self):
        return "Viva" if not self.pagado else "Muerta"
    
    # ========== FASE 2: PROPIEDADES PARA PAGOS PARCIALES ==========
    
    @property
    def total_pagado(self):
        """Total de pagos realizados hasta el momento.
        
        Compatible con sistema antiguo: si pagado=True pero no hay pagos, retorna el total.
        """
        total = sum(pago.monto for pago in self.pagos.all())
        
        # Compatibilidad: si está pagada con el sistema antiguo pero no tiene pagos registrados
        if self.pagado and total == 0:
            return self.total
        
        return Decimal(total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def saldo_pendiente(self):
        """Saldo que falta por pagar al proveedor."""
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
            # Sin pagos - todas las compras son "pendientes" (no hay vencimiento)
            return "pendiente"
        elif self.total_pagado >= self.total:
            # Pagada completamente
            return "pagada"
        else:
            # Pago parcial
            return "parcial"

    def __str__(self):
        return f"Compra {self.folio} - Proveedor: {self.proveedor} - Estado: {self.estado}"

from django.apps import apps

class CompraProducto(models.Model):
    compra = models.ForeignKey("Compra", on_delete=models.CASCADE, related_name='productos')
    producto = models.ForeignKey("inventario.Producto", on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    detectado_como = models.CharField(max_length=200, null=True, blank=True)
    
    # Campos de revisión manual
    requiere_revision_manual = models.BooleanField(default=False, help_text="Indica si esta línea requiere revisión")
    motivo_revision = models.CharField(max_length=255, blank=True, help_text="Motivos por los que requiere revisión")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['compra', 'producto'],
                name='unique_compra_producto'
            )
        ]

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en Compra {self.compra.folio}"


class PagoCompra(models.Model):
    """
    Registro de un pago (total o parcial) realizado a un proveedor por una compra.
    Permite trazabilidad completa de pagos a proveedores.
    """
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta'),
        ('deposito', 'Depósito'),
        ('otro', 'Otro'),
    ]
    
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='pagos')
    fecha_pago = models.DateField(help_text="Fecha en que se realizó el pago")
    monto = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto del pago")
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        default='transferencia',
        help_text="Método utilizado para el pago"
    )
    referencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Número de cheque, referencia de transferencia, etc."
    )
    notas = models.TextField(
        blank=True,
        null=True,
        help_text="Notas adicionales sobre el pago"
    )
    creado_en = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_pago']
        verbose_name = "Pago de Compra"
        verbose_name_plural = "Pagos de Compras"
    
    def clean(self):
        """Validaciones del pago."""
        if self.monto <= 0:
            raise ValidationError("El monto del pago debe ser mayor a 0")
        
        # Validar que no se sobrepase el total (opcional - permitir sobrepago para casos especiales)
        # if self.compra:
        #     total_pagos = sum(p.monto for p in self.compra.pagos.exclude(pk=self.pk))
        #     if total_pagos + self.monto > self.compra.total:
        #         raise ValidationError(f"El total de pagos (${total_pagos + self.monto}) sobrepasa el total de la compra (${self.compra.total})")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Actualizar estado de la compra
        if self.compra:
            total_pagado = sum(p.monto for p in self.compra.pagos.all())
            if total_pagado >= self.compra.total:
                # Marcar como pagada si se completó el pago
                self.compra.pagado = True
                if not self.compra.fecha_pago:
                    self.compra.fecha_pago = self.fecha_pago
                self.compra.save(update_fields=['pagado', 'fecha_pago'])
    
    def __str__(self):
        return f"Pago de ${self.monto} - Compra {self.compra.folio} ({self.fecha_pago})"

