# ventas/admin_pnr_widget.py
"""
Widget de revisión PNR para el admin de Facturas de Ventas.
Separado del admin.py principal para mejor mantenibilidad.
"""
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.middleware.csrf import get_token
from decimal import Decimal
from inventario.models import Producto, ProductoNoReconocido


def render_widget_pnr_ventas(obj, request):
    """
    Renderiza el widget HTML de revisión de PNR para una factura de ventas.
    
    Args:
        obj: Instancia de Factura
        request: HttpRequest
        
    Returns:
        SafeString con HTML del widget
    """
    if not obj.pk:
        return "-"
    
    # Contar PNR asociados por UUID
    pnr_pendientes = ProductoNoReconocido.objects.filter(
        uuid_factura=obj.uuid_factura,
        procesado=False,
        origen="venta"
    ) if obj.uuid_factura else ProductoNoReconocido.objects.none()
    
    num_pnr = pnr_pendientes.count()
    
    # Construir HTML del resumen
    estado_class = "error" if num_pnr > 0 else "success"
    icono = "⚠️" if num_pnr > 0 else "✓"
    
    html_parts = [
        f'<div style="padding: 15px; border: 2px solid {"#e74c3c" if estado_class == "error" else "#27ae60"}; '
        f'border-radius: 5px; background-color: {"#ffe6e6" if estado_class == "error" else "#e8f8f5"}; margin-bottom: 15px;">',
        f'<h3 style="margin-top: 0; color: {"#c0392b" if estado_class == "error" else "#229954"};">{icono} Resumen de revisión de ventas</h3>',
    ]
    
    # PNR pendientes con formularios interactivos
    if num_pnr > 0:
        html_parts.append(f'<p style="margin: 8px 0; margin-top: 15px;"><strong>⚠️ Productos no reconocidos sin procesar:</strong> {num_pnr}</p>')
        html_parts.append('<p style="margin: 4px 0; padding: 8px; background-color: #fff3cd; border-radius: 3px; font-size: 0.9em; color: #856404;">'
                        'ℹ️ <strong>Nota:</strong> En ventas NO se pueden crear productos nuevos. '
                        'Solo puedes asignar a productos existentes y opcionalmente crear un alias.'
                        '</p>')
        
        # Cargar productos para dropdowns (limitado para performance)
        productos_disponibles = list(Producto.objects.all().order_by("nombre")[:500])
        
        for idx, pnr in enumerate(pnr_pendientes[:10], 1):
            cantidad = pnr.cantidad or 0
            precio_u = pnr.precio_unitario or 0
            importe = cantidad * precio_u
            
            # Contenedor del PNR
            html_parts.append(
                f'<div style="border: 1px solid #ddd; padding: 12px; margin: 10px 0; background: #fff; border-radius: 4px;">'
                f'<div style="margin-bottom: 10px;">'
                f'<strong style="color: #333; font-size: 0.95em;">{idx}. {pnr.nombre_detectado}</strong><br>'
                f'<small style="color: #666;">Cant: <strong>{cantidad}</strong> | P/U: <strong>${precio_u:,.2f}</strong> | Importe: <strong>${importe:,.2f}</strong></small>'
                f'</div>'
                f'<div style="display: flex; gap: 15px; flex-wrap: wrap;">'
            )
            
            # Formulario: Asignar a existente
            csrf_token = get_token(request)
            pnr_id_val = pnr.id
            obj_id_val = obj.id
            html_parts.append(
                f'<div style="flex: 1; min-width: 300px;">'
                f'<label style="display: block; font-size: 0.85em; font-weight: bold; margin-bottom: 4px; color: #555;">Asignar a producto existente:</label>'
                f'<select id="producto_id_{pnr_id_val}" required style="width: 100%; padding: 6px; font-size: 0.85em; margin-bottom: 6px; border: 1px solid #ccc; border-radius: 3px;">'
                f'<option value="">-- Selecciona producto --</option>'
            )
            
            for prod in productos_disponibles:
                html_parts.append(f'<option value="{prod.id}">{prod.nombre} (Stock: {prod.stock})</option>')
            
            html_parts.append(
                f'</select>'
                f'<label style="font-size: 0.8em; display: block; margin: 6px 0; color: #666;">'
                f'<input type="checkbox" id="crear_alias_{pnr_id_val}" checked style="margin-right: 4px;" /> Crear alias automáticamente'
                f'</label>'
                f'<button type="button" '
                f'data-pnr-id="{pnr_id_val}" '
                f'data-factura-id="{obj_id_val}" '
                f'data-csrf="{csrf_token}" '
                f'onclick="asignarPNRVenta(this)" '
                f'style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85em; font-weight: bold;">'
                f'✓ Asignar'
                f'</button>'
                f'</div>'
            )
            
            html_parts.append('</div></div>')  # Cerrar flex y contenedor PNR
        
        if num_pnr > 10:
            html_parts.append(f'<p style="margin: 10px 0; color: #888; font-size: 0.9em; font-style: italic;">... y {num_pnr - 10} más (procesa estos primero para ver el resto)</p>')
    else:
        html_parts.append('<p style="margin: 8px 0;"><strong>✓ Productos no reconocidos:</strong> 0 pendientes</p>')
    
    # Lista de productos detectados en la venta
    detalles_venta = obj.detalles.all()
    num_detalles = detalles_venta.count()
    productos_precio_sospechoso = []  # Declarar antes para usar al final
    
    if num_detalles > 0:
        html_parts.append(f'<p style="margin: 8px 0; margin-top: 15px;"><strong>✓ Productos en la factura:</strong> {num_detalles}</p>')
        html_parts.append('<ul style="margin: 5px 0; padding-left: 20px; font-size: 0.9em; color: #555;">')
        
        suma_total = Decimal("0")
        
        for detalle in detalles_venta[:20]:  # Limitar a 20
            nombre = detalle.producto.nombre
            cantidad = detalle.cantidad or 0
            precio_u = detalle.precio_unitario or Decimal("0")
            importe = cantidad * precio_u
            suma_total += importe
            
            # 🔍 GUARDIAN: Validar precio contra BD (precio_venta)
            precio_venta_bd = detalle.producto.precio_venta or Decimal("0")
            precio_sospechoso = False
            motivo_alerta = ""
            
            if precio_venta_bd > 0 and precio_u > 0:
                # Tolerancia: 10% (permitir hasta 90% del precio BD)
                umbral_minimo = precio_venta_bd * Decimal("0.90")
                
                if precio_u < umbral_minimo:
                    # Precio facturado es MENOR al 90% del precio BD
                    diferencia_pct = ((precio_venta_bd - precio_u) / precio_venta_bd) * 100
                    precio_sospechoso = True
                    motivo_alerta = f"Precio {float(diferencia_pct):.0f}% menor a BD (${precio_venta_bd:,.2f})"
                    
                    productos_precio_sospechoso.append({
                        'nombre': nombre,
                        'precio_factura': precio_u,
                        'precio_bd': precio_venta_bd,
                        'diferencia_pct': diferencia_pct
                    })
            
            # Renderizar con color según validación
            if precio_sospechoso:
                html_parts.append(
                    f'<li style="background-color: #fff3cd; padding: 4px; border-left: 3px solid #ffc107; margin: 2px 0;">'
                    f'⚠️ <strong style="color: #856404;">{nombre}</strong> | '
                    f'<strong>{cantidad}</strong> × '
                    f'<strong style="color: #dc3545;">${precio_u:,.2f}</strong> = '
                    f'<strong>${importe:,.2f}</strong><br>'
                    f'<small style="color: #856404; margin-left: 20px;">{motivo_alerta}</small></li>'
                )
            else:
                html_parts.append(
                    f'<li>{nombre} | '
                    f'<strong>{cantidad}</strong> × '
                    f'<strong>${precio_u:,.2f}</strong> = '
                    f'<strong>${importe:,.2f}</strong></li>'
                )
        
        if num_detalles > 20:
            html_parts.append(f'<li><em>... y {num_detalles - 20} más</em></li>')
            # Procesar también los detalles restantes para validación
            for detalle in detalles_venta[20:]:
                cantidad = detalle.cantidad or 0
                precio_u = detalle.precio_unitario or Decimal("0")
                suma_total += cantidad * precio_u
                
                # Validar precios también en los detalles no mostrados
                precio_venta_bd = detalle.producto.precio_venta or Decimal("0")
                if precio_venta_bd > 0 and precio_u > 0:
                    umbral_minimo = precio_venta_bd * Decimal("0.90")
                    if precio_u < umbral_minimo:
                        diferencia_pct = ((precio_venta_bd - precio_u) / precio_venta_bd) * 100
                        productos_precio_sospechoso.append({
                            'nombre': detalle.producto.nombre,
                            'precio_factura': precio_u,
                            'precio_bd': precio_venta_bd,
                            'diferencia_pct': diferencia_pct
                        })
        
        html_parts.append('</ul>')
        
        # 💰 VALIDACIÓN: Suma esperada vs Suma real (según BD)
        suma_esperada_bd = Decimal("0")
        for detalle in detalles_venta:
            cantidad = detalle.cantidad or 0
            precio_venta_bd = detalle.producto.precio_venta or Decimal("0")
            if precio_venta_bd > 0:
                suma_esperada_bd += cantidad * precio_venta_bd
        
        # Solo mostrar si tenemos precios en BD para comparar
        if suma_esperada_bd > 0:
            diferencia_bd = suma_total - suma_esperada_bd
            diferencia_bd_pct = abs((diferencia_bd / suma_esperada_bd) * 100) if suma_esperada_bd else Decimal("0")
            
            # Determinar si hay alerta (verificar mayor primero)
            if abs(diferencia_bd_pct) > Decimal("10"):  # Más del 10% - CRÍTICO
                color_validacion = "#f8d7da"
                border_validacion = "#dc3545"
                text_validacion = "#721c24"
                icono_validacion = "🚨"
            elif abs(diferencia_bd_pct) > Decimal("5"):  # Entre 5-10% - ADVERTENCIA
                color_validacion = "#fff3cd"
                border_validacion = "#ffc107"
                text_validacion = "#856404"
                icono_validacion = "⚠️"
            else:  # Menos del 5% - OK
                color_validacion = "#d4edda"
                border_validacion = "#28a745"
                text_validacion = "#155724"
                icono_validacion = "✓"
            
            html_parts.append(
                f'<div style="margin: 10px 0; padding: 10px; background-color: {color_validacion}; '
                f'border-left: 4px solid {border_validacion}; border-radius: 4px;">'
                f'<p style="margin: 0; font-size: 0.9em; color: {text_validacion}; font-weight: bold;">'
                f'{icono_validacion} <strong>Validación contra BD (Mecanismo de verificación):</strong></p>'
                f'<p style="margin: 4px 0 0 20px; font-size: 0.85em; color: {text_validacion};">'
                f'Suma esperada (BD): <strong>${suma_esperada_bd:,.2f}</strong></p>'
                f'<p style="margin: 2px 0 0 20px; font-size: 0.85em; color: {text_validacion};">'
                f'Suma real (Factura): <strong>${suma_total:,.2f}</strong></p>'
                f'<p style="margin: 2px 0 0 20px; font-size: 0.85em; color: {text_validacion}; font-style: italic;">'
            )
            
            if diferencia_bd > 0:
                html_parts.append(f'Diferencia: <strong style="color: #28a745;">+${diferencia_bd:,.2f}</strong> (+{diferencia_bd_pct:.1f}%) - Facturado MÁS de lo esperado')
            elif diferencia_bd < 0:
                html_parts.append(f'Diferencia: <strong style="color: #dc3545;">${diferencia_bd:,.2f}</strong> ({diferencia_bd_pct:.1f}%) - Facturado MENOS de lo esperado')
            else:
                html_parts.append(f'Diferencia: $0.00 (0.00%) - Precios correctos')
            
            html_parts.append('</p></div>')
        
        # 🚨 ALERTA: Productos con precios sospechosos
        if productos_precio_sospechoso:
            num_sospechosos = len(productos_precio_sospechoso)
            html_parts.append(
                f'<div style="margin: 15px 0; padding: 12px; background-color: #fff3cd; '
                f'border-left: 4px solid #ffc107; border-radius: 4px;">'
                f'<p style="margin: 0 0 8px 0; color: #856404; font-weight: bold; font-size: 0.95em;">'
                f'⚠️ GUARDIAN: {num_sospechosos} producto(s) con precio menor al esperado</p>'
                f'<p style="margin: 0; font-size: 0.85em; color: #856404;">'
                f'Los siguientes productos tienen precio de venta <strong>menor al 90%</strong> '
                f'del precio registrado en la BD. Esto podría indicar un error de facturación o un descuento especial:'
                f'</p>'
                f'<ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 0.85em; color: #856404;">'
            )
            
            for prod in productos_precio_sospechoso[:5]:  # Mostrar máximo 5
                html_parts.append(
                    f'<li><strong>{prod["nombre"]}</strong><br>'
                    f'Facturado: <strong>${prod["precio_factura"]:,.2f}</strong> | '
                    f'BD: <strong>${prod["precio_bd"]:,.2f}</strong> | '
                    f'Diferencia: <strong style="color: #dc3545;">-{float(prod["diferencia_pct"]):.0f}%</strong></li>'
                )
            
            if num_sospechosos > 5:
                html_parts.append(f'<li><em>... y {num_sospechosos - 5} más</em></li>')
            
            html_parts.append(
                f'</ul>'
                f'<p style="margin: 8px 0 0 0; font-size: 0.8em; color: #856404; font-style: italic;">'
                f'💡 <strong>Sugerencia:</strong> Verifica con el cliente si estos precios son correctos o si hubo un error al facturar.'
                f'</p>'
                f'</div>'
            )
        
        # Mostrar suma total, descuento y comparar con factura
        total_factura = obj.total or Decimal("0")
        subtotal_factura = obj.subtotal or Decimal("0")
        descuento_factura = obj.descuento or Decimal("0")
        
        # Si hay subtotal registrado, usarlo; si no, la suma de productos
        subtotal_esperado = subtotal_factura if subtotal_factura > 0 else suma_total
        
        # Calcular total esperado (subtotal - descuento)
        total_esperado_con_descuento = subtotal_esperado - descuento_factura
        
        # Validar: comparar suma_total con subtotal, y total_factura con total_esperado
        diferencia_subtotal = abs(suma_total - subtotal_esperado)
        diferencia_total = abs(total_factura - total_esperado_con_descuento)
        
        # Determinar si cuadra (tolerancia < 0.5%)
        diferencia_pct = (diferencia_total / total_factura * 100) if total_factura else Decimal("0")
        
        if diferencia_pct < Decimal("0.5"):
            color_bg = "#d4edda"
            color_border = "#28a745"
            color_text = "#155724"
            icono_total = "✓"
        else:
            color_bg = "#f8d7da"
            color_border = "#dc3545"
            color_text = "#721c24"
            icono_total = "✗"
        
        html_parts.append(
            f'<div style="margin: 10px 0; padding: 10px; background-color: {color_bg}; '
            f'border-left: 4px solid {color_border}; border-radius: 4px;">'
            f'<p style="margin: 0; font-size: 0.9em; color: {color_text}; font-weight: bold;">'
            f'{icono_total} <strong>Validación de totales:</strong></p>'
            f'<p style="margin: 4px 0 0 20px; font-size: 0.85em; color: {color_text};">'
            f'Suma productos: <strong>${suma_total:,.2f}</strong></p>'
        )
        
        # Mostrar descuento si existe
        if descuento_factura > 0:
            descuento_pct = (descuento_factura / subtotal_esperado * 100) if subtotal_esperado > 0 else Decimal("0")
            html_parts.append(
                f'<p style="margin: 2px 0 0 20px; font-size: 0.85em; color: {color_text};">'
                f'Descuento: <strong style="color: #dc3545;">-${descuento_factura:,.2f}</strong> '
                f'({descuento_pct:.1f}%)</p>'
            )
        
        html_parts.append(
            f'<p style="margin: 2px 0 0 20px; font-size: 0.85em; color: {color_text};">'
            f'Total factura: <strong>${total_factura:,.2f}</strong></p>'
        )
        
        if diferencia_total > Decimal("0.10"):
            html_parts.append(
                f'<p style="margin: 4px 0 0 20px; font-size: 0.85em; color: {color_text}; font-style: italic;">'
                f'Diferencia: ${diferencia_total:,.2f} ({diferencia_pct:.2f}%)</p>'
            )
        
        html_parts.append('</div>')
    
    # Mensaje guía
    tiene_precios_sospechosos = len(productos_precio_sospechoso) > 0
    
    if num_pnr > 0:
        html_parts.append(
            '<p style="margin-top: 15px; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107; color: #856404;">'
            '<strong>Acción requerida:</strong> Asigna los productos no reconocidos a productos existentes. '
            'Usa los formularios arriba para procesar los PNR sin salir de esta página.'
        )
        if tiene_precios_sospechosos:
            html_parts.append(' Además, <strong>revisa los precios sospechosos</strong> detectados por el guardian.')
        html_parts.append('</p>')
    elif tiene_precios_sospechosos:
        html_parts.append(
            '<p style="margin-top: 15px; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107; color: #856404;">'
            '<strong>⚠️ Revisión recomendada:</strong> El guardian detectó productos con precios menores al 90% del precio esperado. '
            'Verifica que los precios sean correctos antes de marcar como "Revisado OK".'
            '</p>'
        )
    else:
        html_parts.append(
            '<p style="margin-top: 15px; padding: 10px; background-color: #d4edda; border-left: 4px solid #28a745; color: #155724;">'
            '<strong>✓ Todo resuelto:</strong> Puedes marcar esta factura como "Revisado OK" usando el dropdown "Estado revisión" más abajo.'
            '</p>'
        )
    
    # Agregar JavaScript para manejar el submit de PNR
    html_parts.append(
        "<script>"
        "function asignarPNRVenta(btn) {"
            "const pnrId = btn.getAttribute('data-pnr-id');"
            "const facturaId = btn.getAttribute('data-factura-id');"
            "const csrfToken = btn.getAttribute('data-csrf');"
            "const productoId = document.getElementById('producto_id_' + pnrId).value;"
            "if (!productoId) { alert('Selecciona un producto'); return; }"
            "const crearAlias = document.getElementById('crear_alias_' + pnrId).checked;"
            "const form = document.createElement('form');"
            "form.method = 'POST';"
            "form.action = '/admin/ventas/factura/' + facturaId + '/asignar_pnr/';"
            "const fields = {"
                "'csrfmiddlewaretoken': csrfToken,"
                "'pnr_id': pnrId,"
                "'producto_id': productoId,"
                "'crear_alias': crearAlias ? 'on' : ''"
            "};"
            "for (const key in fields) {"
                "const input = document.createElement('input');"
                "input.type = 'hidden';"
                "input.name = key;"
                "input.value = fields[key];"
                "form.appendChild(input);"
            "}"
            "document.body.appendChild(form);"
            "form.submit();"
        "}"
        "</script>"
    )
    
    html_parts.append('</div>')
    
    return mark_safe(''.join(html_parts))
