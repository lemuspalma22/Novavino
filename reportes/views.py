from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from ventas.models import Factura
from compras.models import Compra


class DashboardPrincipalView(TemplateView):
    """Dashboard principal con resumen de todos los reportes."""
    template_name = 'reportes/dashboard_principal.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Resumen de cuentas por cobrar
        # No podemos filtrar por estado_pago (es una propiedad), así que obtenemos todas las no pagadas
        facturas_pendientes = Factura.objects.filter(pagado=False)
        # Filtrar las que realmente tienen saldo pendiente
        facturas_con_saldo = [f for f in facturas_pendientes if f.saldo_pendiente > 0]
        context['total_por_cobrar'] = sum(f.saldo_pendiente for f in facturas_con_saldo)
        context['num_facturas_pendientes'] = len(facturas_con_saldo)
        
        # Resumen de cuentas por pagar
        compras_pendientes = Compra.objects.filter(pagado=False)
        compras_con_saldo = [c for c in compras_pendientes if c.saldo_pendiente > 0]
        context['total_por_pagar'] = sum(c.saldo_pendiente for c in compras_con_saldo)
        context['num_compras_pendientes'] = len(compras_con_saldo)
        
        # Flujo neto proyectado
        context['flujo_neto'] = context['total_por_cobrar'] - context['total_por_pagar']
        
        return context


class CuentasPorCobrarView(TemplateView):
    """Dashboard de cobranza - Cuentas por cobrar."""
    template_name = 'reportes/cuentas_por_cobrar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Facturas pendientes o parciales
        facturas = Factura.objects.filter(
            pagado=False
        ).select_related().prefetch_related('pagos')
        
        # Total por cobrar
        context['total_por_cobrar'] = sum(f.saldo_pendiente for f in facturas)
        context['num_facturas'] = facturas.count()
        
        # Agrupar por cliente
        por_cliente = {}
        for factura in facturas:
            cliente = factura.cliente
            if cliente not in por_cliente:
                por_cliente[cliente] = {
                    'cliente': cliente,
                    'facturas': [],
                    'total_saldo': Decimal('0.00'),
                    'vencidas': 0,
                    'monto_vencido': Decimal('0.00'),
                }
            por_cliente[cliente]['facturas'].append(factura)
            por_cliente[cliente]['total_saldo'] += factura.saldo_pendiente
            
            # Verificar si está vencida
            if factura.vencimiento and timezone.now().date() > factura.vencimiento:
                por_cliente[cliente]['vencidas'] += 1
                por_cliente[cliente]['monto_vencido'] += factura.saldo_pendiente
        
        context['por_cliente'] = sorted(
            por_cliente.values(),
            key=lambda x: x['total_saldo'],
            reverse=True
        )
        
        # Antigüedad de saldos
        hoy = timezone.now().date()
        antiguedad = {
            'dias_0_30': {'facturas': 0, 'monto': Decimal('0.00'), 'label': '0-30'},
            'dias_31_60': {'facturas': 0, 'monto': Decimal('0.00'), 'label': '31-60'},
            'dias_61_90': {'facturas': 0, 'monto': Decimal('0.00'), 'label': '61-90'},
            'dias_mas_90': {'facturas': 0, 'monto': Decimal('0.00'), 'label': '+90'},
        }
        
        for factura in facturas:
            if factura.vencimiento:
                dias = (hoy - factura.vencimiento).days
                if dias <= 0:
                    # No vencida
                    antiguedad['dias_0_30']['facturas'] += 1
                    antiguedad['dias_0_30']['monto'] += factura.saldo_pendiente
                elif dias <= 30:
                    antiguedad['dias_0_30']['facturas'] += 1
                    antiguedad['dias_0_30']['monto'] += factura.saldo_pendiente
                elif dias <= 60:
                    antiguedad['dias_31_60']['facturas'] += 1
                    antiguedad['dias_31_60']['monto'] += factura.saldo_pendiente
                elif dias <= 90:
                    antiguedad['dias_61_90']['facturas'] += 1
                    antiguedad['dias_61_90']['monto'] += factura.saldo_pendiente
                else:
                    antiguedad['dias_mas_90']['facturas'] += 1
                    antiguedad['dias_mas_90']['monto'] += factura.saldo_pendiente
        
        context['antiguedad'] = antiguedad
        
        # Facturas vencidas
        facturas_vencidas = [f for f in facturas if f.vencimiento and hoy > f.vencimiento]
        context['num_vencidas'] = len(facturas_vencidas)
        context['monto_vencido'] = sum(f.saldo_pendiente for f in facturas_vencidas)
        
        return context


class CuentasPorPagarView(TemplateView):
    """Dashboard de pagos a proveedores - Cuentas por pagar."""
    template_name = 'reportes/cuentas_por_pagar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Compras pendientes o parciales
        compras = Compra.objects.filter(
            pagado=False
        ).select_related('proveedor').prefetch_related('pagos')
        
        # Total por pagar
        context['total_por_pagar'] = sum(c.saldo_pendiente for c in compras)
        context['num_compras'] = compras.count()
        
        # Agrupar por proveedor
        por_proveedor = {}
        for compra in compras:
            proveedor = str(compra.proveedor) if compra.proveedor else 'Sin proveedor'
            if proveedor not in por_proveedor:
                por_proveedor[proveedor] = {
                    'proveedor': proveedor,
                    'compras': [],
                    'total_saldo': Decimal('0.00'),
                }
            por_proveedor[proveedor]['compras'].append(compra)
            por_proveedor[proveedor]['total_saldo'] += compra.saldo_pendiente
        
        context['por_proveedor'] = sorted(
            por_proveedor.values(),
            key=lambda x: x['total_saldo'],
            reverse=True
        )
        
        return context


class FlujoCajaView(TemplateView):
    """Dashboard de flujo de caja proyectado."""
    template_name = 'reportes/flujo_caja.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Entradas proyectadas (por cobrar)
        facturas_pendientes = Factura.objects.filter(pagado=False)
        entradas = sum(f.saldo_pendiente for f in facturas_pendientes)
        
        # Salidas proyectadas (por pagar)
        compras_pendientes = Compra.objects.filter(pagado=False)
        salidas = sum(c.saldo_pendiente for c in compras_pendientes)
        
        # Flujo neto
        flujo_neto = entradas - salidas
        
        context.update({
            'entradas_proyectadas': entradas,
            'salidas_proyectadas': salidas,
            'flujo_neto': flujo_neto,
            'num_facturas_cobrar': facturas_pendientes.count(),
            'num_compras_pagar': compras_pendientes.count(),
        })
        
        # Datos para gráfica (próximas 4 semanas)
        hoy = timezone.now().date()
        semanas = []
        
        for i in range(5):  # Hoy + 4 semanas
            fecha_inicio = hoy + timedelta(weeks=i)
            fecha_fin = fecha_inicio + timedelta(days=6)
            
            # Facturas que vencen esta semana
            facturas_semana = [
                f for f in facturas_pendientes 
                if f.vencimiento and fecha_inicio <= f.vencimiento <= fecha_fin
            ]
            
            semana_data = {
                'label': f"Sem {i+1}" if i > 0 else "Hoy",
                'entradas': sum(f.saldo_pendiente for f in facturas_semana),
                'salidas': Decimal('0.00'),  # Por ahora, compras no tienen vencimiento
            }
            semanas.append(semana_data)
        
        context['semanas'] = semanas
        
        return context


class DistribucionFondosView(TemplateView):
    """Dashboard avanzado de distribución de fondos."""
    template_name = 'reportes/distribucion_fondos.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Facturas pendientes
        facturas_pendientes = Factura.objects.filter(pagado=False)
        
        # De las facturas pendientes, calcular:
        # - Costos por recuperar (dinero que debemos a proveedores)
        # - Ganancia por recibir (ganancia neta)
        costos_por_recuperar = sum(f.costo_pendiente for f in facturas_pendientes)
        ganancia_por_recibir = sum(f.ganancia_pendiente for f in facturas_pendientes)
        
        # Compras pendientes (dinero comprometido)
        compras_pendientes = Compra.objects.filter(pagado=False)
        dinero_comprometido = sum(c.saldo_pendiente for c in compras_pendientes)
        
        # Ganancia neta proyectada (ganancia por recibir menos obligaciones pendientes)
        ganancia_neta_proyectada = ganancia_por_recibir - dinero_comprometido
        
        context.update({
            'costos_por_recuperar': costos_por_recuperar,
            'ganancia_por_recibir': ganancia_por_recibir,
            'dinero_comprometido': dinero_comprometido,
            'total_pendiente_cobro': costos_por_recuperar + ganancia_por_recibir,
            'ganancia_neta_proyectada': ganancia_neta_proyectada,
        })
        
        return context
