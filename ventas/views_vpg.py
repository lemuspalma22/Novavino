# ventas/views_vpg.py
"""
Vista dedicada para agregar VPG (Venta Público General) de forma simplificada.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from .models import Factura
from decimal import Decimal
from datetime import datetime, timedelta


@staff_member_required
def agregar_vpg_view(request):
    """Vista simplificada para agregar una VPG."""
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            cliente = request.POST.get('cliente', '').strip()
            fecha_facturacion = request.POST.get('fecha_facturacion')
            total = request.POST.get('total', '0')
            subtotal = request.POST.get('subtotal', '0')
            descuento = request.POST.get('descuento', '0')
            vencimiento = request.POST.get('vencimiento', '')
            notas = request.POST.get('notas', '').strip()
            metodo_pago = request.POST.get('metodo_pago', 'PUE')
            
            # Validaciones
            if not cliente:
                messages.error(request, "El cliente es obligatorio")
                return render(request, 'admin/ventas/agregar_vpg.html', {'form_data': request.POST})
            
            if not fecha_facturacion:
                messages.error(request, "La fecha de facturación es obligatoria")
                return render(request, 'admin/ventas/agregar_vpg.html', {'form_data': request.POST})
            
            # Convertir valores
            try:
                total = Decimal(total)
                subtotal = Decimal(subtotal) if subtotal else total
                descuento = Decimal(descuento) if descuento else Decimal("0.00")
            except:
                messages.error(request, "Los montos deben ser números válidos")
                return render(request, 'admin/ventas/agregar_vpg.html', {'form_data': request.POST})
            
            # Calcular vencimiento si no se proporciona
            if not vencimiento:
                fecha_obj = datetime.strptime(fecha_facturacion, '%Y-%m-%d').date()
                vencimiento = fecha_obj + timedelta(days=15)
            
            # Crear VPG
            vpg = Factura.objects.create(
                es_vpg=True,
                cliente=cliente,
                fecha_facturacion=fecha_facturacion,
                total=total,
                subtotal=subtotal,
                descuento=descuento,
                vencimiento=vencimiento,
                notas=notas,
                metodo_pago=metodo_pago
            )
            
            messages.success(
                request,
                f'✅ VPG creada exitosamente: {vpg.folio_factura} - {cliente} - ${total:,.2f}'
            )
            
            # Redirigir al detalle de la VPG
            return redirect('admin:ventas_factura_change', vpg.id)
            
        except Exception as e:
            messages.error(request, f"Error al crear VPG: {str(e)}")
            return render(request, 'admin/ventas/agregar_vpg.html', {'form_data': request.POST})
    
    # GET request - mostrar formulario
    # Valores por defecto
    context = {
        'fecha_hoy': datetime.now().date().strftime('%Y-%m-%d'),
        'metodo_pago_choices': Factura.METODO_PAGO_CHOICES,
    }
    
    return render(request, 'admin/ventas/agregar_vpg.html', context)
