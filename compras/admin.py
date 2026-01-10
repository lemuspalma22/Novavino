
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import path, reverse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from .models import Compra, Proveedor, CompraProducto, PagoCompra
from inventario.models import Producto, ProductoNoReconocido
from .views_pnr import asignar_pnr_view, crear_producto_pnr_view

# Mostrar productos relacionados dentro del proveedor en el admin
class ProductoInline(admin.TabularInline):
    model = Producto
    extra = 1  # Muestra una línea extra para agregar productos

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("proveedor")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "proveedor":
            if request.resolver_match.kwargs:
                proveedor_id = request.resolver_match.kwargs.get("object_id")
                kwargs["queryset"] = Proveedor.objects.filter(id=proveedor_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Personalización del admin de Proveedor
class ProveedorAdmin(admin.ModelAdmin):
    inlines = [ProductoInline]
    class Meta:
        verbose_name_plural = "Proveedores"

# Personalización del admin de CompraProducto
class CompraProductoAdmin(admin.ModelAdmin):
    list_display = ("compra", "producto", "cantidad", "precio_unitario", "flag_revision", "motivo_revision")
    list_filter = ("requiere_revision_manual",)
    search_fields = ("producto__nombre", "compra__folio", "motivo_revision")
    readonly_fields = ("flag_revision",)
    
    def flag_revision(self, obj):
        """Muestra icono de alerta si requiere revisión."""
        if obj.requiere_revision_manual:
            return format_html('<span style="font-size: 1.5em; color: #f39c12;">⚠️</span>')
        return format_html('<span style="color: #27ae60;">✓</span>')
    flag_revision.short_description = "Estado"


class PagoCompraInline(admin.TabularInline):
    """Inline para mostrar y agregar pagos en el detalle de compra."""
    model = PagoCompra
    extra = 0
    fields = ("fecha_pago", "monto", "metodo_pago", "referencia", "notas")
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

# Personalización del admin de Compra
class CompraAdmin(admin.ModelAdmin):
    list_display = ("folio", "proveedor", "fecha", "total", "total_pagado_display", "saldo_pendiente_display", "estado_pago_display", "pagado", "fecha_pago_display", "estado_detallado")
    list_filter = ("requiere_revision_manual", "estado_revision", "pagado", "proveedor")
    search_fields = ("folio", "uuid", "proveedor__nombre")
    readonly_fields = ("resumen_revision", "info_pagos_display")
    actions = ["marcar_revisado_ok", "marcar_revisado_con_cambios"]
    inlines = [PagoCompraInline]
    fieldsets = (
        ("Información general", {
            "fields": ("folio", "proveedor", "fecha", "total", "uuid", "archivo", "pagado", "fecha_pago", "complemento_pago", "notas", "info_pagos_display")
        }),
        ("Estado de revisión", {
            "fields": ("resumen_revision", "requiere_revision_manual", "estado_revision"),
            "classes": ("wide",),
        }),
    )
    
    def estado_detallado(self, obj):
        """Muestra estado resumido con conteo de líneas con flags."""
        lineas_con_flags = obj.productos.filter(requiere_revision_manual=True).count()
        
        if obj.requiere_revision_manual:
            if obj.estado_revision == "pendiente":
                icono = '<span style="font-size: 1.2em; color: #e74c3c;">⚠️</span>'
                texto = f"Pendiente ({lineas_con_flags} líneas)" if lineas_con_flags > 0 else "Pendiente"
                return format_html(f'{icono} {texto}')
            elif obj.estado_revision == "revisado_con_cambios":
                icono = '<span style="font-size: 1.2em; color: #f39c12;">⚠️</span>'
                return format_html(f'{icono} Revisado con cambios')
            else:
                icono = '<span style="color: #27ae60;">✓</span>'
                return format_html(f'{icono} Revisado OK')
        icono = '<span style="color: #27ae60;">✓</span>'
        return format_html(f'{icono} OK')
    estado_detallado.short_description = "Estado revisión"
    
    def fecha_pago_display(self, obj):
        """Muestra la fecha de pago en formato YYYY-MM-DD o la fecha del último pago."""
        if obj.fecha_pago:
            return obj.fecha_pago.strftime('%Y-%m-%d')
        # Si no tiene fecha_pago pero tiene pagos, mostrar la fecha del último pago
        ultimo_pago = obj.pagos.order_by('-fecha_pago').first()
        if ultimo_pago:
            return ultimo_pago.fecha_pago.strftime('%Y-%m-%d')
        return '-'
    fecha_pago_display.short_description = "Fecha de pago"
    
    # ========== FASE 2: MÉTODOS DISPLAY PARA PAGOS PARCIALES ==========
    
    def total_pagado_display(self, obj):
        """Muestra total pagado al proveedor."""
        total = float(obj.total_pagado)
        if total > 0:
            total_str = f"${total:,.2f}"
            return format_html('<span style="color: #e74c3c;">{}</span>', total_str)
        return format_html('<span style="color: #95a5a6;">$0.00</span>')
    total_pagado_display.short_description = "Pagado"
    total_pagado_display.admin_order_field = "total"
    
    def saldo_pendiente_display(self, obj):
        """Muestra saldo pendiente por pagar."""
        saldo = float(obj.saldo_pendiente)
        if saldo > 0:
            saldo_str = f"${saldo:,.2f}"
            return format_html('<span style="color: #27ae60;">{}</span>', saldo_str)
        return format_html('<span style="color: #95a5a6;">$0.00</span>')
    saldo_pendiente_display.short_description = "Por Pagar"
    
    def estado_pago_display(self, obj):
        """Muestra estado de pago sin fondo de color (solo emoji y texto)."""
        estado = obj.estado_pago
        
        badges = {
            "pagada": ('<span style="color: #27ae60;">✅ PAGADA</span>'),
            "parcial": ('<span style="color: #f39c12;">⚠️ PARCIAL</span>'),
            "pendiente": ('<span style="color: #e74c3c;">🔴 PENDIENTE</span>'),
        }
        
        return format_html(badges.get(estado, estado))
    estado_pago_display.short_description = "Estado Pago"
    
    def info_pagos_display(self, obj):
        """Muestra resumen completo de pagos en el detalle de compra."""
        if not obj.pk:
            return "Guarda la compra primero"
        
        html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
            <h3 style="margin-top: 0; color: #495057;">💰 Resumen de Pagos a Proveedor</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #e9ecef;">
                    <th colspan="2" style="padding: 8px; text-align: left; border-bottom: 2px solid #dee2e6;">COMPRA</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Total compra:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold;">${obj.total:,.2f}</td>
                </tr>
                
                <tr style="background: #e9ecef;">
                    <th colspan="2" style="padding: 8px; text-align: left; border-bottom: 2px solid #dee2e6;">PAGOS REALIZADOS</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Total pagado:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #e74c3c; font-weight: bold;">${obj.total_pagado:,.2f}</td>
                </tr>
                
                <tr style="background: #e9ecef;">
                    <th colspan="2" style="padding: 8px; text-align: left; border-bottom: 2px solid #dee2e6;">POR PAGAR</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Saldo pendiente:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #27ae60; font-weight: bold;">${obj.saldo_pendiente:,.2f}</td>
                </tr>
            </table>
            
            <p style="margin-top: 15px; margin-bottom: 0; font-size: 12px; color: #6c757d;">
                <strong>Estado:</strong> {obj.estado_pago.upper()} | 
                <strong>Pagos registrados:</strong> {obj.pagos.count()}
            </p>
        </div>
        """
        return format_html(html)
    info_pagos_display.short_description = "Información de Pagos"
    
    def get_urls(self):
        """Registrar URLs custom para procesar PNR y procesar facturas Drive."""
        urls = super().get_urls()
        custom_urls = [
            path('procesar-drive/', self.admin_site.admin_view(self.procesar_drive_view), name='compras_compra_procesar_drive'),
            path('<int:object_id>/asignar_pnr/', self.admin_site.admin_view(asignar_pnr_view), name='compras_compra_asignar_pnr'),
            path('<int:object_id>/crear_producto_pnr/', self.admin_site.admin_view(crear_producto_pnr_view), name='compras_compra_crear_producto_pnr'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Agregar botón personalizado en la vista de lista."""
        extra_context = extra_context or {}
        extra_context['show_drive_button'] = True
        return super().changelist_view(request, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Guardar request para que readonly_fields puedan acceder a él."""
        self._current_request = request
        return super().change_view(request, object_id, form_url, extra_context)
    
    def procesar_drive_view(self, request):
        """
        Vista custom para procesar facturas pendientes desde Google Drive.
        No requiere selección de items.
        """
        try:
            from compras.utils.drive_processor import DriveInvoiceProcessor
            
            # Mostrar mensaje de inicio
            self.message_user(
                request,
                "🔄 Iniciando procesamiento de facturas desde Google Drive...",
                level=messages.INFO
            )
            
            # Crear procesador
            processor = DriveInvoiceProcessor(validation_mode="lenient")
            
            # Procesar todas las facturas
            resultado = processor.process_all_invoices(move_files=True)
            
            # Preparar mensaje de resumen
            total = resultado["total"]
            success = resultado["success"]
            duplicate = resultado["duplicate"]
            error = resultado["error"]
            
            if total == 0:
                self.message_user(
                    request,
                    "⚠️ No se encontraron facturas pendientes en Google Drive.",
                    level=messages.WARNING
                )
            else:
                # Mensaje principal de éxito
                if error == 0:
                    nivel = messages.SUCCESS
                    icono = "✅"
                elif success > 0:
                    nivel = messages.WARNING
                    icono = "⚠️"
                else:
                    nivel = messages.ERROR
                    icono = "❌"
                
                mensaje_principal = (
                    f"{icono} Procesamiento completado: "
                    f"{success} registradas, "
                    f"{duplicate} duplicadas, "
                    f"{error} errores "
                    f"(de {total} archivos)"
                )
                self.message_user(request, mensaje_principal, level=nivel)
                
                # Mensajes detallados de errores
                if error > 0:
                    detalles_error = [
                        d for d in resultado["details"] 
                        if d["status"] == "error"
                    ]
                    for detalle in detalles_error[:5]:  # Mostrar max 5 errores
                        error_msg = f"❌ Error en {detalle['file']}: {detalle['error'][:100]}"
                        self.message_user(request, error_msg, level=messages.ERROR)
                    
                    if error > 5:
                        self.message_user(
                            request,
                            f"⚠️ ... y {error - 5} errores más. Revisa la carpeta 'Compras_Errores' en Drive.",
                            level=messages.WARNING
                        )
                
                # Mensaje informativo de duplicadas
                if duplicate > 0:
                    self.message_user(
                        request,
                        f"ℹ️ {duplicate} factura(s) ya existían en la base de datos (omitidas).",
                        level=messages.INFO
                    )
                    
        except ImportError as e:
            self.message_user(
                request,
                f"❌ Error: No se pudo importar el módulo drive_processor. {str(e)}",
                level=messages.ERROR
            )
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            self.message_user(
                request,
                f"❌ Error inesperado al procesar facturas: {str(e)}",
                level=messages.ERROR
            )
            # Log detallado en consola para debugging
            print(f"\n{'='*80}\nERROR EN PROCESAR_DRIVE_VIEW:\n{error_trace}\n{'='*80}\n")
        
        # Redirigir de vuelta a la lista de compras
        return HttpResponseRedirect(reverse('admin:compras_compra_changelist'))
    
    def resumen_revision(self, obj):
        """Widget de resumen de revisión en el detalle de la compra."""
        if not obj.pk:
            return "-"
        
        try:
            return self._render_resumen_widget(obj)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"\n{'='*80}\nERROR EN WIDGET resumen_revision:\n{error_details}\n{'='*80}\n")
            return format_html(
                '<div style="padding: 15px; border: 2px solid #e74c3c; background-color: #ffe6e6; border-radius: 5px;">'
                '<p style="color: #c0392b; font-weight: bold;">⚠️ Error al cargar el widget de revisión</p>'
                f'<p style="color: #666; font-size: 0.9em;">Error: {str(e)}</p>'
                f'<pre style="font-size: 0.75em; background: #f5f5f5; padding: 10px; overflow-x: auto;">{error_details[:1000]}</pre>'
                '</div>'
            )
    resumen_revision.short_description = "Resumen del estado de revisión"
    
    def _render_resumen_widget(self, obj):
        """Renderiza el contenido del widget (separado para mejor debugging)."""
        # Obtener request del change_view
        request = getattr(self, '_current_request', None)
        if not request:
            return format_html('<p style="color: #c0392b;">Error: No se pudo obtener el request para generar el widget.</p>')
        
        # Contar líneas con flags y recolectar motivos
        lineas_con_flags = obj.productos.filter(requiere_revision_manual=True)
        num_lineas_flags = lineas_con_flags.count()
        
        # Contar PNR asociados por UUID
        pnr_pendientes = ProductoNoReconocido.objects.filter(
            uuid_factura=obj.uuid,
            procesado=False
        )
        num_pnr = pnr_pendientes.count()
        
        # Construir HTML del resumen
        estado_class = "error" if (num_lineas_flags > 0 or num_pnr > 0) else "success"
        icono = "⚠️" if (num_lineas_flags > 0 or num_pnr > 0) else "✓"
        
        html_parts = [
            f'<div style="padding: 15px; border: 2px solid {"#e74c3c" if estado_class == "error" else "#27ae60"}; '
            f'border-radius: 5px; background-color: {"#ffe6e6" if estado_class == "error" else "#e8f8f5"}; margin-bottom: 15px;">',
            f'<h3 style="margin-top: 0; color: {"#c0392b" if estado_class == "error" else "#229954"};">{icono} Resumen de revisión</h3>',
        ]
        
        # Líneas con flags
        if num_lineas_flags > 0:
            html_parts.append(f'<p style="margin: 8px 0;"><strong>⚠️ Líneas con flags:</strong> {num_lineas_flags}</p>')
            html_parts.append('<ul style="margin: 5px 0; padding-left: 20px;">')
            for linea in lineas_con_flags[:10]:  # Limitar a 10 para no saturar
                motivos_raw = linea.motivo_revision or "sin motivo especificado"
                # Formatear el motivo para mejor legibilidad
                if motivos_raw == "toda_factura_requiere_revision_por_contener_licor_ieps_30pct_o_53pct":
                    motivos = "Esta factura contiene otro producto con licor (IEPS 30% o 53%), por lo que toda la factura requiere revisión manual"
                else:
                    motivos = motivos_raw.replace("_", " ").capitalize()
                html_parts.append(f'<li>{linea.producto.nombre}: <em style="color: #d32f2f;">{motivos}</em></li>')
            if num_lineas_flags > 10:
                html_parts.append(f'<li><em>... y {num_lineas_flags - 10} más</em></li>')
            html_parts.append('</ul>')
        else:
            html_parts.append('<p style="margin: 8px 0;"><strong>✓ Líneas con flags:</strong> 0</p>')
        
        # PNR pendientes con formularios interactivos
        if num_pnr > 0:
            html_parts.append(f'<p style="margin: 8px 0; margin-top: 15px;"><strong>⚠️ Productos no reconocidos sin procesar:</strong> {num_pnr}</p>')
            
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
                
                # Formulario 1: Asignar a existente (div con JavaScript, NO form anidado)
                csrf_token = get_token(request)
                pnr_id_val = pnr.id
                obj_id_val = obj.id
                html_parts.append(
                    f'<div style="flex: 1; min-width: 250px;">'
                    f'<label style="display: block; font-size: 0.85em; font-weight: bold; margin-bottom: 4px; color: #555;">Asignar a producto existente:</label>'
                    f'<select id="producto_id_{pnr_id_val}" required style="width: 100%; padding: 6px; font-size: 0.85em; margin-bottom: 6px; border: 1px solid #ccc; border-radius: 3px;">'
                    f'<option value="">-- Selecciona producto --</option>'
                )
                
                for prod in productos_disponibles:
                    html_parts.append(f'<option value="{prod.id}">{prod.nombre}</option>')
                
                # Usar atributos data- para evitar problemas de escapado en onclick
                html_parts.append(
                    f'</select>'
                    f'<label style="font-size: 0.8em; display: block; margin: 6px 0; color: #666;">'
                    f'<input type="checkbox" id="crear_alias_{pnr_id_val}" checked style="margin-right: 4px;" /> Crear alias automáticamente'
                    f'</label>'
                    f'<button type="button" '
                    f'data-pnr-id="{pnr_id_val}" '
                    f'data-compra-id="{obj_id_val}" '
                    f'data-csrf="{csrf_token}" '
                    f'onclick="asignarPNR(this)" '
                    f'style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85em; font-weight: bold;">'
                    f'✓ Asignar'
                    f'</button>'
                    f'</div>'
                )
                
                # Formulario 2: Crear nuevo producto
                # Escapar el nombre para HTML (especialmente comillas)
                import html
                nombre_escapado = html.escape(pnr.nombre_detectado or "", quote=True)
                
                html_parts.append(
                    f'<div style="flex: 1; min-width: 250px;">'
                    f'<label style="display: block; font-weight: bold; margin-bottom: 6px; font-size: 0.9em; color: #555;">Crear producto nuevo:</label>'
                    f'<input type="text" id="nombre_{pnr_id_val}" placeholder="Nombre del producto" value="{nombre_escapado}" style="width: 100%; padding: 6px; margin-bottom: 6px; border: 1px solid #ccc; border-radius: 3px; font-size: 0.85em;" />'
                    f'<input type="number" id="precio_compra_{pnr_id_val}" placeholder="Precio compra" value="{float(pnr.precio_unitario or 0):.2f}" step="0.01" style="width: 100%; padding: 6px; margin-bottom: 6px; border: 1px solid #ccc; border-radius: 3px; font-size: 0.85em;" />'
                    f'<input type="number" id="precio_venta_{pnr_id_val}" placeholder="Precio venta" step="0.01" style="width: 100%; padding: 6px; margin-bottom: 6px; border: 1px solid #ccc; border-radius: 3px; font-size: 0.85em;" />'
                    f'<button type="button" '
                    f'data-pnr-id="{pnr_id_val}" '
                    f'data-compra-id="{obj_id_val}" '
                    f'data-csrf="{csrf_token}" '
                    f'onclick="crearProductoPNR(this)" '
                    f'style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85em; font-weight: bold; width: 100%;">'
                    f'+ Crear producto'
                    f'</button>'
                    f'</div>'
                )
                
                html_parts.append('</div></div>')  # Cerrar flex y contenedor PNR
            
            if num_pnr > 10:
                html_parts.append(f'<p style="margin: 10px 0; color: #888; font-size: 0.9em; font-style: italic;">... y {num_pnr - 10} más (procesa estos primero para ver el resto)</p>')
        else:
            html_parts.append('<p style="margin: 8px 0;"><strong>✓ Productos no reconocidos:</strong> 0 pendientes</p>')
        
        # Lista de productos detectados (para verificar que el extractor capturó todo)
        productos_compra = obj.productos.all()
        num_productos = productos_compra.count()
        
        if num_productos > 0:
            html_parts.append(f'<p style="margin: 8px 0; margin-top: 15px;"><strong>✓ Productos detectados:</strong> {num_productos}</p>')
            # Nota explicativa sobre P/U
            prov_nombre = obj.proveedor.nombre if obj.proveedor else ""
            if "secretos" in prov_nombre.lower():
                html_parts.append(
                    '<p style="margin: 4px 0 8px 0; padding: 6px 10px; background-color: #e7f3ff; border-left: 3px solid #2196F3; font-size: 0.8em; color: #0d47a1;">'
                    '<strong>Nota:</strong> Para Secretos de la Vid, el <strong>P/U</strong> mostrado ya incluye IEPS 26.5%, IVA 16% y descuento 24% aplicados.'
                    '</p>'
                )
            html_parts.append('<ul style="margin: 5px 0; padding-left: 20px; font-size: 0.9em; color: #555;">')
            
            # Calcular suma total usando PRECIO DE BD (no precio extraído)
            from decimal import Decimal
            suma_esperada_bd = Decimal("0")
            suma_extraida_pdf = Decimal("0")
            hay_discrepancias_precio = False
            
            for linea in productos_compra[:20]:  # Limitar a 20 para no saturar
                nombre = linea.producto.nombre
                cantidad = linea.cantidad or 0
                
                # Precio extraído del PDF (en CompraProducto.precio_unitario)
                precio_pdf = linea.precio_unitario or Decimal("0")
                
                # Precio de BD (en Producto.precio_compra)
                precio_bd = linea.producto.precio_compra or Decimal("0")
                
                # Calcular importes
                importe_pdf = cantidad * precio_pdf
                importe_bd = cantidad * precio_bd
                
                suma_extraida_pdf += importe_pdf
                suma_esperada_bd += importe_bd
                
                # Detectar si hay diferencia de precio
                diff_precio = abs(precio_pdf - precio_bd)
                diff_precio_pct = (diff_precio / precio_bd * 100) if precio_bd else Decimal("0")
                
                # Clasificar nivel de discrepancia
                if diff_precio_pct > Decimal("1.0"):
                    # Error grande (>1%)
                    hay_discrepancias_precio = True
                    color = "#d32f2f"  # Rojo
                    icono = "⚠"
                elif diff_precio_pct > Decimal("0.1"):
                    # Diferencia notable (>0.1%)
                    hay_discrepancias_precio = True
                    color = "#f57c00"  # Naranja
                    icono = "⚠"
                elif diff_precio > Decimal("0.01"):
                    # Diferencia mínima (redondeo)
                    color = "#888"  # Gris
                    icono = ""
                else:
                    # Sin diferencia
                    color = None
                    icono = ""
                
                # Mostrar SIEMPRE precio BD entre paréntesis si difiere
                if color:
                    html_parts.append(
                        f'<li style="color: {color if diff_precio_pct > 1 else "inherit"};">'
                        f'{nombre} | '
                        f'<strong>{cantidad}</strong> × '
                        f'<strong>${precio_pdf:,.2f}</strong> '
                        f'<span style="color: {color}; font-size: 0.85em;">(BD: ${precio_bd:,.2f})</span> = '
                        f'<strong>${importe_pdf:,.2f}</strong> '
                        f'{icono}</li>'
                    )
                else:
                    html_parts.append(
                        f'<li>{nombre} | '
                        f'<strong>{cantidad}</strong> × '
                        f'<strong>${precio_pdf:,.2f}</strong> = '
                        f'<strong>${importe_pdf:,.2f}</strong></li>'
                    )
            
            if num_productos > 20:
                html_parts.append(f'<li><em>... y {num_productos - 20} más (suma total incluye todos)</em></li>')
                # Sumar los productos restantes
                for linea in productos_compra[20:]:
                    cantidad = linea.cantidad or 0
                    precio_pdf = linea.precio_unitario or Decimal("0")
                    precio_bd = linea.producto.precio_compra or Decimal("0")
                    suma_extraida_pdf += cantidad * precio_pdf
                    suma_esperada_bd += cantidad * precio_bd
                    
                    # Detectar discrepancias en productos no mostrados
                    diff_precio = abs(precio_pdf - precio_bd)
                    diff_precio_pct = (diff_precio / precio_bd * 100) if precio_bd else Decimal("0")
                    if diff_precio_pct > Decimal("0.1"):  # Umbral más sensible
                        hay_discrepancias_precio = True
            
            html_parts.append('</ul>')
            
            # Mostrar suma total y comparar con factura usando PRECIOS DE BD
            total_factura = obj.total or Decimal("0")
            
            # Comparar suma esperada (BD) vs total factura
            diferencia = abs(total_factura - suma_esperada_bd)
            diferencia_pct = (diferencia / total_factura * 100) if total_factura else Decimal("0")
            
            # Determinar color según diferencia
            if diferencia_pct < Decimal("0.5"):
                color_bg = "#d4edda"  # Verde claro
                color_border = "#28a745"  # Verde
                color_text = "#155724"  # Verde oscuro
                icono = "✓"
            elif diferencia_pct < Decimal("1.0"):
                color_bg = "#fff3cd"  # Amarillo claro
                color_border = "#ffc107"  # Amarillo
                color_text = "#856404"  # Amarillo oscuro
                icono = "⚠"
            else:
                color_bg = "#f8d7da"  # Rojo claro
                color_border = "#dc3545"  # Rojo
                color_text = "#721c24"  # Rojo oscuro
                icono = "✗"
            
            html_parts.append(
                f'<div style="margin: 10px 0; padding: 10px; background-color: {color_bg}; '
                f'border-left: 4px solid {color_border}; border-radius: 4px;">'
                f'<p style="margin: 0; font-size: 0.9em; color: {color_text}; font-weight: bold;">'
                f'{icono} <strong>Suma esperada (BD):</strong> ${suma_esperada_bd:,.2f}</p>'
                f'<p style="margin: 4px 0 0 0; font-size: 0.9em; color: {color_text};">'
                f'<strong>Total factura:</strong> ${total_factura:,.2f}</p>'
                f'<p style="margin: 4px 0 0 0; font-size: 0.85em; color: {color_text}; font-style: italic;">'
                f'Diferencia: ${diferencia:,.2f} ({diferencia_pct:.2f}%)'
                f'</p>'
            )
            
            # Mostrar advertencia adicional si hay discrepancias de precio
            if hay_discrepancias_precio:
                html_parts.append(
                    f'<p style="margin: 8px 0 0 0; padding: 6px; background-color: #fff3cd; '
                    f'border-radius: 3px; font-size: 0.85em; color: #856404;">'
                    f'ℹ️ Productos con diferencia de precio BD vs PDF mostrados arriba. '
                    f'Esto puede ser normal por redondeos o indicar error de facturación.'
                    f'</p>'
                )
            
            html_parts.append('</div>')
        
        # Mensaje guía
        if num_lineas_flags > 0 or num_pnr > 0:
            html_parts.append(
                '<p style="margin-top: 15px; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107; color: #856404;">'
                '<strong>Acción requerida:</strong> Resuelve los items marcados con ⚠️ antes de marcar como "Revisado OK". '
                'Usa los formularios arriba para procesar los PNR sin salir de esta página.'
                '</p>'
            )
        else:
            html_parts.append(
                '<p style="margin-top: 15px; padding: 10px; background-color: #d4edda; border-left: 4px solid #28a745; color: #155724;">'
                '<strong>✓ Todo resuelto:</strong> Puedes marcar esta compra como "Revisado OK" usando el dropdown "Estado revisión" más abajo.'
                '</p>'
            )
        
        # Agregar JavaScript para manejar el submit de PNR sin forms anidados
        html_parts.append(
            "<script>"
            "function asignarPNR(btn) {"
                "const pnrId = btn.getAttribute('data-pnr-id');"
                "const compraId = btn.getAttribute('data-compra-id');"
                "const csrfToken = btn.getAttribute('data-csrf');"
                "const productoId = document.getElementById('producto_id_' + pnrId).value;"
                "if (!productoId) { alert('Selecciona un producto'); return; }"
                "const crearAlias = document.getElementById('crear_alias_' + pnrId).checked;"
                "const form = document.createElement('form');"
                "form.method = 'POST';"
                "form.action = '/admin/compras/compra/' + compraId + '/asignar_pnr/';"
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
            "function crearProductoPNR(btn) {"
                "const pnrId = btn.getAttribute('data-pnr-id');"
                "const compraId = btn.getAttribute('data-compra-id');"
                "const csrfToken = btn.getAttribute('data-csrf');"
                "const nombre = document.getElementById('nombre_' + pnrId).value;"
                "const precioCompra = document.getElementById('precio_compra_' + pnrId).value;"
                "const precioVenta = document.getElementById('precio_venta_' + pnrId).value;"
                "if (!nombre || !precioCompra || !precioVenta) {"
                    "alert('Completa todos los campos (nombre, precio compra, precio venta)');"
                    "return;"
                "}"
                "const form = document.createElement('form');"
                "form.method = 'POST';"
                "form.action = '/admin/compras/compra/' + compraId + '/crear_producto_pnr/';"
                "const fields = {"
                    "'csrfmiddlewaretoken': csrfToken,"
                    "'pnr_id': pnrId,"
                    "'nombre': nombre,"
                    "'precio_compra': precioCompra,"
                    "'precio_venta': precioVenta,"
                    "'costo_transporte': '0'"
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
        
        # Usar mark_safe en lugar de format_html porque ya usamos f-strings
        from django.utils.safestring import mark_safe
        return mark_safe(''.join(html_parts))
    
    def marcar_revisado_ok(self, request, queryset):
        """Acción para marcar compras como revisadas OK y limpiar flags de líneas."""
        updated = queryset.update(estado_revision="revisado_ok", requiere_revision_manual=False)
        
        # Limpiar flags de todas las líneas de productos de estas compras
        total_lineas = 0
        for compra in queryset:
            lineas_updated = CompraProducto.objects.filter(compra=compra).update(
                requiere_revision_manual=False,
                motivo_revision=""
            )
            total_lineas += lineas_updated
        
        self.message_user(
            request, 
            f"{updated} compra(s) marcada(s) como 'Revisado OK' y {total_lineas} línea(s) limpiadas."
        )
    marcar_revisado_ok.short_description = "Marcar como Revisado OK"
    
    def marcar_revisado_con_cambios(self, request, queryset):
        """Acción para marcar compras como revisadas con cambios y limpiar flags de líneas."""
        updated = queryset.update(estado_revision="revisado_con_cambios", requiere_revision_manual=False)
        
        # Limpiar flags de todas las líneas de productos de estas compras
        total_lineas = 0
        for compra in queryset:
            lineas_updated = CompraProducto.objects.filter(compra=compra).update(
                requiere_revision_manual=False,
                motivo_revision=""
            )
            total_lineas += lineas_updated
        
        self.message_user(
            request, 
            f"{updated} compra(s) marcada(s) como 'Revisado con cambios' y {total_lineas} línea(s) limpiadas."
        )
    marcar_revisado_con_cambios.short_description = "Marcar como Revisado con cambios"

# Registro de modelos en el admin
admin.site.register(Compra, CompraAdmin)
admin.site.register(Proveedor, ProveedorAdmin)
admin.site.register(CompraProducto, CompraProductoAdmin)
admin.site.register(PagoCompra)  # Fase 2: Pagos parciales
