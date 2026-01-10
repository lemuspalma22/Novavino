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
    
    folio_factura = models.CharField(max_length=20, unique=True, blank=True, null=True)
    folio_numero = models.IntegerField(null=True, blank=True, help_text="Número extraído del folio para ordenamiento", db_index=True)
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
    
    # Campos para VPG (Venta Público General)
    es_vpg = models.BooleanField(default=False, help_text="Marca si es una Venta Público General (no tiene folio fiscal)")
    folio_vpg_anio = models.IntegerField(null=True, blank=True, help_text="Año del folio VPG (ej: 2025)")
    folio_vpg_numero = models.IntegerField(null=True, blank=True, help_text="Número consecutivo del VPG en el año (ej: 1, 2, 3...)")

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

    def generar_folio_vpg(self):
        """Genera automáticamente el folio VPG con formato VPG{YY}-{N}."""
        from datetime import datetime
        
        anio_actual = datetime.now().year
        anio_corto = anio_actual % 100  # 2025 -> 25
        
        # Buscar el último folio VPG del año actual
        ultimo_vpg = Factura.objects.filter(
            es_vpg=True,
            folio_vpg_anio=anio_actual
        ).order_by('-folio_vpg_numero').first()
        
        if ultimo_vpg and ultimo_vpg.folio_vpg_numero:
            siguiente_numero = ultimo_vpg.folio_vpg_numero + 1
        else:
            siguiente_numero = 1
        
        # Guardar datos del VPG
        self.folio_vpg_anio = anio_actual
        self.folio_vpg_numero = siguiente_numero
        self.folio_factura = f"VPG{anio_corto}-{siguiente_numero}"
    
    @property
    def tipo_venta(self):
        """Retorna 'VPG' o 'Factura' según el tipo."""
        return "VPG" if self.es_vpg else "Factura"
    
    @property
    def folio_display(self):
        """Retorna el folio formateado para mostrar."""
        return self.folio_factura
    
    def clean(self):
        """Validación personalizada."""
        from django.core.exceptions import ValidationError
        
        # Si NO es VPG, el folio es obligatorio
        if not self.es_vpg and not self.folio_factura:
            raise ValidationError({
                'folio_factura': 'El folio es obligatorio para facturas normales.'
            })

    def save(self, *args, **kwargs):
        # Generar folio VPG si es necesario
        if self.es_vpg and not self.folio_vpg_numero:
            self.generar_folio_vpg()
        
        # Extraer número del folio para ordenamiento
        if self.folio_factura:
            import re
            # Intentar extraer números del folio
            numeros = re.findall(r'\d+', self.folio_factura)
            if numeros:
                # Tomar el último número encontrado (para VPG26-1 toma 1, para 1160 toma 1160)
                self.folio_numero = int(numeros[-1])
        
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


class ComplementoPago(models.Model):
    """
    Complemento de Pago (CFDI) - Documento fiscal que certifica el pago de facturas PPD.
    Puede aplicar a una o varias facturas (aunque típicamente es 1:1).
    """
    FORMA_PAGO_CHOICES = [
        ('01', '01 - Efectivo'),
        ('02', '02 - Cheque nominativo'),
        ('03', '03 - Transferencia electrónica de fondos'),
        ('04', '04 - Tarjeta de crédito'),
        ('05', '05 - Monedero electrónico'),
        ('28', '28 - Tarjeta de débito'),
        ('99', '99 - Por definir'),
    ]
    
    # === Identificación fiscal ===
    folio_complemento = models.CharField(max_length=20, unique=True, help_text="Folio del complemento (ej: 1047)")
    uuid_complemento = models.CharField(max_length=100, unique=True, help_text="UUID del CFDI del complemento")
    
    # === Datos del pago ===
    fecha_emision = models.DateField(help_text="Fecha de emisión del complemento CFDI")
    fecha_pago = models.DateField(help_text="Fecha real en que se recibió el pago")
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Monto total del pago")
    forma_pago_sat = models.CharField(
        max_length=2, 
        choices=FORMA_PAGO_CHOICES,
        help_text="Forma de pago según catálogo del SAT"
    )
    
    # === Cliente ===
    cliente = models.CharField(max_length=200, help_text="Nombre del cliente")
    rfc_cliente = models.CharField(max_length=13, blank=True, null=True, help_text="RFC del cliente")
    
    # === Archivo ===
    archivo_pdf = models.FileField(
        upload_to='complementos_pago/',
        null=True,
        blank=True,
        help_text="Archivo PDF del complemento"
    )
    
    # === Revisión y validación ===
    requiere_revision = models.BooleanField(
        default=False,
        help_text="Marca si el complemento requiere revisión manual"
    )
    motivo_revision = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo por el que requiere revisión"
    )
    
    # === Metadata ===
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    notas = models.TextField(blank=True, null=True, help_text="Notas adicionales")
    
    class Meta:
        ordering = ['-fecha_emision', '-folio_complemento']
        verbose_name = "Complemento de Pago"
        verbose_name_plural = "Complementos de Pago"
    
    def __str__(self):
        return f"Complemento {self.folio_complemento} - {self.cliente} - ${self.monto_total}"


class DocumentoRelacionado(models.Model):
    """
    Relación entre un ComplementoPago y las Facturas que paga.
    Contiene el desglose por factura: saldo anterior, pagado, saldo insoluto.
    """
    complemento = models.ForeignKey(
        ComplementoPago,
        on_delete=models.CASCADE,
        related_name='documentos_relacionados',
        help_text="Complemento de pago"
    )
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='complementos_relacionados',
        help_text="Factura que se está pagando"
    )
    
    # === Datos del PDF (información del documento relacionado) ===
    uuid_factura_relacionada = models.CharField(
        max_length=100,
        help_text="UUID de la factura relacionada (para validación)"
    )
    num_parcialidad = models.IntegerField(
        default=1,
        help_text="Número de parcialidad de este pago (1, 2, 3...)"
    )
    saldo_anterior = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Saldo antes de este pago"
    )
    importe_pagado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto pagado en esta parcialidad"
    )
    saldo_insoluto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Saldo restante después de este pago"
    )
    
    # === Vinculación con sistema interno ===
    pago_factura = models.OneToOneField(
        PagoFactura,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documento_relacionado',
        help_text="PagoFactura interno vinculado a este complemento"
    )
    
    # === Impuestos (para referencia) ===
    iva_desglosado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="IVA desglosado en el complemento"
    )
    ieps_desglosado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="IEPS desglosado en el complemento"
    )
    
    class Meta:
        ordering = ['num_parcialidad']
        verbose_name = "Documento Relacionado"
        verbose_name_plural = "Documentos Relacionados"
        constraints = [
            models.UniqueConstraint(
                fields=['complemento', 'factura'],
                name='unique_complemento_factura'
            )
        ]
    
    def clean(self):
        """Validaciones del documento relacionado."""
        # Validar que el UUID coincida con la factura
        if self.factura and self.uuid_factura_relacionada:
            if self.factura.uuid_factura != self.uuid_factura_relacionada:
                raise ValidationError(
                    f"El UUID del complemento ({self.uuid_factura_relacionada}) "
                    f"no coincide con el UUID de la factura ({self.factura.uuid_factura})"
                )
        
        # Validar montos
        if self.saldo_anterior < self.importe_pagado:
            raise ValidationError(
                f"El importe pagado (${self.importe_pagado}) no puede ser mayor "
                f"que el saldo anterior (${self.saldo_anterior})"
            )
        
        # Validar cálculo de saldo insoluto
        saldo_calculado = self.saldo_anterior - self.importe_pagado
        if abs(saldo_calculado - self.saldo_insoluto) > Decimal("0.01"):
            raise ValidationError(
                f"Saldo insoluto incorrecto. Esperado: ${saldo_calculado}, "
                f"Recibido: ${self.saldo_insoluto}"
            )
    
    def __str__(self):
        return (f"Comp. {self.complemento.folio_complemento} → "
                f"Fact. {self.factura.folio_factura} "
                f"(Parcialidad {self.num_parcialidad})")
