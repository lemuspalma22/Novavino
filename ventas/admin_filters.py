# ventas/admin_filters.py
"""
Filtros personalizados para el admin de Facturas.
"""
from django.contrib import admin
from django.utils import timezone
from django.db.models import Q, Sum
from datetime import timedelta


class EstadoPagoFilter(admin.SimpleListFilter):
    """Filtro por estado de pago: PAGADA, PARCIAL, PENDIENTE, VENCIDA."""
    title = 'Estado de Pago'
    parameter_name = 'estado_pago'

    def lookups(self, request, model_admin):
        return (
            ('pagada', 'PAGADA'),
            ('parcial', 'PARCIAL'),
            ('pendiente', 'PENDIENTE'),
            ('vencida', 'VENCIDA'),
        )

    def queryset(self, request, queryset):
        hoy = timezone.now().date()
        
        if self.value() == 'pagada':
            # Pagadas: pagado=True O total_pagado >= total
            return queryset.filter(
                Q(pagado=True) | 
                Q(pagos__isnull=False)
            ).annotate(
                total_pagos=Sum('pagos__monto')
            ).filter(
                total_pagos__gte=models.F('total')
            ).distinct()
        
        elif self.value() == 'parcial':
            # Parcial: tiene pagos pero no está completamente pagada
            return queryset.filter(
                pagado=False,
                pagos__isnull=False
            ).annotate(
                total_pagos=Sum('pagos__monto')
            ).filter(
                total_pagos__lt=models.F('total'),
                total_pagos__gt=0
            ).distinct()
        
        elif self.value() == 'pendiente':
            # Pendiente: sin pagos y no vencida
            return queryset.filter(
                pagado=False,
                pagos__isnull=True,
                vencimiento__gte=hoy
            ).distinct()
        
        elif self.value() == 'vencida':
            # Vencida: sin pagar completamente y vencimiento pasado
            return queryset.filter(
                pagado=False,
                vencimiento__lt=hoy
            ).distinct()
        
        return queryset


class VencimientoFilter(admin.SimpleListFilter):
    """Filtro por vencimiento."""
    title = 'Vencimiento'
    parameter_name = 'vencimiento_estado'

    def lookups(self, request, model_admin):
        return (
            ('vencidas', 'Vencidas'),
            ('7dias', 'Por vencer en 7 días'),
            ('15dias', 'Por vencer en 15 días'),
            ('30dias', 'Por vencer en 30 días'),
        )

    def queryset(self, request, queryset):
        hoy = timezone.now().date()
        
        if self.value() == 'vencidas':
            return queryset.filter(
                pagado=False,
                vencimiento__lt=hoy
            )
        
        elif self.value() == '7dias':
            fecha_limite = hoy + timedelta(days=7)
            return queryset.filter(
                pagado=False,
                vencimiento__gte=hoy,
                vencimiento__lte=fecha_limite
            )
        
        elif self.value() == '15dias':
            fecha_limite = hoy + timedelta(days=15)
            return queryset.filter(
                pagado=False,
                vencimiento__gte=hoy,
                vencimiento__lte=fecha_limite
            )
        
        elif self.value() == '30dias':
            fecha_limite = hoy + timedelta(days=30)
            return queryset.filter(
                pagado=False,
                vencimiento__gte=hoy,
                vencimiento__lte=fecha_limite
            )
        
        return queryset


class TipoVentaFilter(admin.SimpleListFilter):
    """Filtro por tipo de venta: Factura o VPG."""
    title = 'Tipo de Venta'
    parameter_name = 'tipo_venta'

    def lookups(self, request, model_admin):
        return (
            ('factura', 'Factura'),
            ('vpg', 'VPG'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'factura':
            return queryset.filter(es_vpg=False)
        elif self.value() == 'vpg':
            return queryset.filter(es_vpg=True)
        return queryset


class MetodoPagoRegistradoFilter(admin.SimpleListFilter):
    """Filtro por método de pago de los pagos registrados."""
    title = 'Método de Pago (Pagos)'
    parameter_name = 'metodo_pago_registrado'

    def lookups(self, request, model_admin):
        return (
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia'),
            ('cheque', 'Cheque'),
            ('tarjeta', 'Tarjeta'),
            ('deposito', 'Depósito'),
            ('otro', 'Otro'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                pagos__metodo_pago=self.value()
            ).distinct()
        return queryset


# Importar models para usar en los filtros
from django.db import models
