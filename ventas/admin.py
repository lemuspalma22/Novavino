from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from .models import Factura, DetalleFactura, PagoFactura, ComplementoPago, DocumentoRelacionado
from inventario.models import ProductoNoReconocido
from .views_pnr import asignar_pnr_venta_view
from .admin_pnr_widget import render_widget_pnr_ventas
from .admin_filters import EstadoPagoFilter, VencimientoFilter, TipoVentaFilter, MetodoPagoRegistradoFilter
from django.db.models import Sum, F
from datetime import datetime
from decimal import Decimal


class DetalleFacturaInline(admin.TabularInline):  
    model = DetalleFactura
    extra = 1
    fields = ("producto", "cantidad", "precio_unitario", "precio_compra", "subtotal")
    readonly_fields = ("subtotal",)

    def subtotal(self, obj):
        if not obj or obj.cantidad is None or obj.precio_unitario is None:
            return 0
        return obj.cantidad * obj.precio_unitario
    subtotal.short_description = "Subtotal"
    
    class Media:
        js = ("js/admin_detalle_factura.js",)


class PagoFacturaInline(admin.TabularInline):
    """Inline para mostrar y agregar pagos en el detalle de factura."""
    model = PagoFactura
    extra = 0
    fields = ("fecha_pago", "monto", "metodo_pago", "referencia", "monto_costo_display", "monto_ganancia_display", "notas")
    readonly_fields = ("monto_costo_display", "monto_ganancia_display")
    
    def monto_costo_display(self, obj):
        if obj.pk:
            return f"${obj.monto_costo:,.2f}"
        return "-"
    monto_costo_display.short_description = "→ Costo"
    
    def monto_ganancia_display(self, obj):
        if obj.pk:
            return f"${obj.monto_ganancia:,.2f}"
        return "-"
    monto_ganancia_display.short_description = "→ Ganancia"

class FacturaAdmin(admin.ModelAdmin):
    list_display = ("tipo_venta_display", "folio_display_ordenable", "cliente", "total", "total_pagado_display", "saldo_pendiente_display", "estado_pago_display", "fecha_facturacion_display", "vencimiento_display", "metodo_pago", "estado_detallado")
    list_filter = (TipoVentaFilter, EstadoPagoFilter, VencimientoFilter, "metodo_pago", MetodoPagoRegistradoFilter, "fecha_facturacion", "requiere_revision_manual", "estado_revision")
    search_fields = ("folio_factura", "cliente", "uuid_factura", "notas")
    readonly_fields = ("total_display", "info_pagos_display", "resumen_revision")
    actions = ["marcar_revisado_ok", "marcar_revisado_con_cambios", "marcar_como_pagadas"]
    ordering = ["-fecha_facturacion", "-id"]
    
    def get_queryset(self, request):
        """Personaliza el queryset para ordenamiento."""
        qs = super().get_queryset(request)
        return qs
    fieldsets = (
        (None, {
            "fields": (
                "es_vpg",
                "folio_factura",
                "cliente",
                "fecha_facturacion",
                "vencimiento",
                "metodo_pago",
                "pagado",
                "fecha_pago",
                "notas",
            )
        }),
        ("Montos", {
            "fields": ("subtotal", "descuento", "total_display", "info_pagos_display"),
            "description": "El total se calcula automáticamente como: Subtotal - Descuento",
        }),
        ("Estado de revisión", {
            "fields": ("resumen_revision", "requiere_revision_manual", "estado_revision"),
            "classes": ("wide",),
        }),
    )
    inlines = [DetalleFacturaInline, PagoFacturaInline]
 
    def total_display(self, obj):
        # Si aún no existe en BD o no tiene total, muéstralo como 0.00
        val = getattr(obj, "total", None)
        if val is None:
            val = 0
        # Span con id para que el JS lo actualice en vivo
        return format_html('<span id="total-display">{:.2f}</span>', val)
    total_display.short_description = "Total"
    
    # ========== COLUMNA FOLIO ORDENABLE ==========
    
    def folio_display_ordenable(self, obj):
        """Muestra el folio y permite ordenamiento numérico."""
        return obj.folio_factura
    folio_display_ordenable.short_description = "Folio Factura"
    folio_display_ordenable.admin_order_field = "folio_numero"
    
    # ========== COLUMNA TIPO DE VENTA (VPG / FACTURA) ==========
    
    def tipo_venta_display(self, obj):
        """Muestra badge de tipo de venta."""
        if obj.es_vpg:
            return format_html(
                '<span style="background: #27ae60; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">VPG</span>'
            )
        else:
            return format_html(
                '<span style="background: #3498db; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">Factura</span>'
            )
    tipo_venta_display.short_description = "Tipo"
    tipo_venta_display.admin_order_field = "es_vpg"
    
    # ========== FASE 1: COLUMNAS DE PAGOS PARCIALES EN LISTADO ==========
    
    def total_pagado_display(self, obj):
        """Muestra total pagado."""
        total = float(obj.total_pagado)
        if total > 0:
            total_str = f"${total:,.2f}"
            return format_html('<span style="color: #27ae60;">{}</span>', total_str)
        return format_html('<span style="color: #95a5a6;">$0.00</span>')
    total_pagado_display.short_description = "Pagado"
    total_pagado_display.admin_order_field = "total"
    
    def saldo_pendiente_display(self, obj):
        """Muestra saldo pendiente."""
        saldo = float(obj.saldo_pendiente)
        if saldo > 0:
            saldo_str = f"${saldo:,.2f}"
            return format_html('<span style="color: #e74c3c;">{}</span>', saldo_str)
        return format_html('<span style="color: #27ae60;">$0.00</span>')
    saldo_pendiente_display.short_description = "Saldo"
    
    def estado_pago_display(self, obj):
        """Muestra estado de pago sin fondo de color (solo emoji y texto)."""
        estado = obj.estado_pago
        
        badges = {
            "pagada": ('<span style="color: #27ae60;">✅ PAGADA</span>'),
            "parcial": ('<span style="color: #f39c12;">⚠️ PARCIAL</span>'),
            "pendiente": ('<span style="color: #95a5a6;">⏳ PENDIENTE</span>'),
            "vencida": ('<span style="color: #e74c3c;">🔴 VENCIDA</span>'),
            "vencida_parcial": ('<span style="color: #e67e22;">🔴 VENC.PARCIAL</span>'),
        }
        
        return format_html(badges.get(estado, estado))
    estado_pago_display.short_description = "Estado Pago"
    
    def fecha_pago_display(self, obj):
        """Muestra fecha de pago formateada o fecha del último pago si hay pagos parciales."""
        if obj.fecha_pago:
            return obj.fecha_pago.strftime("%d/%m/%y")
        # Si no tiene fecha_pago pero tiene pagos, mostrar la fecha del último pago
        ultimo_pago = obj.pagos.order_by('-fecha_pago').first()
        if ultimo_pago:
            return ultimo_pago.fecha_pago.strftime("%d/%m/%y")
        return "-"
    fecha_pago_display.short_description = "Fecha de Pago"
    fecha_pago_display.admin_order_field = "fecha_pago"
    
    def fecha_facturacion_display(self, obj):
        """Muestra fecha de facturación en formato YYYY-MM-DD."""
        if obj.fecha_facturacion:
            return obj.fecha_facturacion.strftime("%Y-%m-%d")
        return "-"
    fecha_facturacion_display.short_description = "Fecha Emisión"
    fecha_facturacion_display.admin_order_field = "fecha_facturacion"
    
    def vencimiento_display(self, obj):
        """Muestra fecha de vencimiento en formato YYYY-MM-DD."""
        if obj.vencimiento:
            return obj.vencimiento.strftime("%Y-%m-%d")
        return "-"
    vencimiento_display.short_description = "Vencimiento"
    vencimiento_display.admin_order_field = "vencimiento"
    
    def info_pagos_display(self, obj):
        """Muestra resumen completo de pagos en el detalle de factura."""
        if not obj.pk:
            return "Guarda la factura primero"
        
        html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
            <h3 style="margin-top: 0; color: #495057;">📊 Resumen de Pagos y Distribución</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #e9ecef;">
                    <th colspan="2" style="padding: 8px; text-align: left; border-bottom: 2px solid #dee2e6;">FACTURA</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Total factura:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: bold;">${obj.total:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Costo total:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #e74c3c;">${obj.costo_total:,.2f} ({obj.porcentaje_costo * 100:.1f}%)</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 2px solid #dee2e6;">Ganancia total:</td>
                    <td style="padding: 8px; border-bottom: 2px solid #dee2e6; color: #27ae60; font-weight: bold;">${obj.ganancia_total:,.2f} ({obj.porcentaje_ganancia * 100:.1f}%)</td>
                </tr>
                
                <tr style="background: #e9ecef;">
                    <th colspan="2" style="padding: 8px; text-align: left; border-bottom: 2px solid #dee2e6;">PAGOS RECIBIDOS</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Total pagado:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #27ae60; font-weight: bold;">${obj.total_pagado:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; padding-left: 25px;">💰 Para proveedores:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #e74c3c;">${obj.costo_pagado:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 2px solid #dee2e6; padding-left: 25px;">✅ Ganancia realizada:</td>
                    <td style="padding: 8px; border-bottom: 2px solid #dee2e6; color: #27ae60; font-weight: bold;">${obj.ganancia_pagada:,.2f}</td>
                </tr>
                
                <tr style="background: #e9ecef;">
                    <th colspan="2" style="padding: 8px; text-align: left; border-bottom: 2px solid #dee2e6;">PENDIENTE POR COBRAR</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">Saldo pendiente:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #e74c3c; font-weight: bold;">${obj.saldo_pendiente:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; padding-left: 25px;">💰 Para proveedores:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #e74c3c;">${obj.costo_pendiente:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; padding-left: 25px;">✅ Ganancia por recibir:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #27ae60;">${obj.ganancia_pendiente:,.2f}</td>
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

    # ✅ Función para mostrar estado detallado con conteo de PNR
    def estado_detallado(self, obj):
        """Muestra estado resumido con conteo de PNR pendientes."""
        pnr_pendientes = ProductoNoReconocido.objects.filter(
            uuid_factura=obj.uuid_factura,
            procesado=False,
            origen="venta"
        ).count() if obj.uuid_factura else 0
        
        if obj.requiere_revision_manual or pnr_pendientes > 0:
            if obj.estado_revision == "pendiente":
                icono = '<span style="font-size: 1.2em; color: #e74c3c;">⚠️</span>'
                texto = f"Pendiente ({pnr_pendientes} PNR)" if pnr_pendientes > 0 else "Pendiente"
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

    # ✅ Agregar URLs personalizadas
    def get_urls(self):
        from .views_vpg import agregar_vpg_view
        urls = super().get_urls()
        custom_urls = [
            path("corte-semanal/", self.admin_site.admin_view(self.corte_semanal_view), name="corte_semanal"),
            path('procesar-drive/', self.admin_site.admin_view(self.procesar_drive_view), name='ventas_factura_procesar_drive'),
            path('<int:object_id>/asignar_pnr/', self.admin_site.admin_view(asignar_pnr_venta_view), name='ventas_factura_asignar_pnr'),
            path('reporte-diferencias/', self.admin_site.admin_view(self.reporte_diferencias_view), name='ventas_factura_reporte_diferencias'),
            path('agregar-vpg/', self.admin_site.admin_view(agregar_vpg_view), name='ventas_factura_agregar_vpg'),
        ]
        return custom_urls + urls

    # ✅ Agregar botón personalizado en la vista de lista
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_drive_button'] = True
        return super().changelist_view(request, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Guardar request para que readonly_fields puedan acceder a él."""
        self._current_request = request
        return super().change_view(request, object_id, form_url, extra_context)
    
    # ✅ Redirigir a la vista de Corte Semanal
    def corte_semanal_view(self, request):
        return redirect("/ventas/corte-semanal/")  # Redirigir a la vista de corte semanal
    
    # ✅ Vista custom para procesar facturas de Drive
    def procesar_drive_view(self, request):
        """
        Vista custom para procesar facturas de ventas desde Google Drive.
        No requiere selección de items.
        """
        try:
            from ventas.utils.drive_processor import DriveVentasProcessor
            
            # Mostrar mensaje de inicio
            self.message_user(
                request,
                "🔄 Iniciando procesamiento de facturas de ventas desde Google Drive...",
                level=messages.INFO
            )
            
            # Crear procesador
            processor = DriveVentasProcessor()
            
            # Procesar todas las facturas
            resultado = processor.process_all_invoices(move_files=True)
            
            # Preparar mensaje de resumen
            total = resultado["total"]
            success = resultado["success"]
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
                            f"⚠️ ... y {error - 5} errores más. Revisa la carpeta 'Facturas Ventas Errores' en Drive.",
                            level=messages.WARNING
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
            print(f"\n{'='*80}\nERROR EN PROCESAR_DRIVE_VIEW (VENTAS):\n{error_trace}\n{'='*80}\n")
        
        # Redirigir de vuelta a la lista de facturas
        return HttpResponseRedirect(reverse('admin:ventas_factura_changelist'))
    
    # ✅ Widget de resumen de revisión (PNR)
    def resumen_revision(self, obj):
        """Widget de resumen de revisión en el detalle de la factura."""
        if not obj.pk:
            return "-"
        
        try:
            request = getattr(self, '_current_request', None)
            if not request:
                return format_html('<p style="color: #c0392b;">Error: No se pudo obtener el request para generar el widget.</p>')
            
            return render_widget_pnr_ventas(obj, request)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"\n{'='*80}\nERROR EN WIDGET resumen_revision (VENTAS):\n{error_details}\n{'='*80}\n")
            return format_html(
                '<div style="padding: 15px; border: 2px solid #e74c3c; background-color: #ffe6e6; border-radius: 5px;">'
                '<p style="color: #c0392b; font-weight: bold;">⚠️ Error al cargar el widget de revisión</p>'
                f'<p style="color: #666; font-size: 0.9em;">Error: {str(e)}</p>'
                f'<pre style="font-size: 0.75em; background: #f5f5f5; padding: 10px; overflow-x: auto;">{error_details[:1000]}</pre>'
                '</div>'
            )
    resumen_revision.short_description = "Resumen del estado de revisión"
    
    # Acciones en masa
    def marcar_revisado_ok(self, request, queryset):
        """Acción para marcar facturas como revisadas OK."""
        updated = queryset.update(estado_revision="revisado_ok", requiere_revision_manual=False)
        self.message_user(
            request, 
            f"{updated} factura(s) marcada(s) como 'Revisado OK'."
        )
    marcar_revisado_ok.short_description = "Marcar como Revisado OK"
    
    def marcar_revisado_con_cambios(self, request, queryset):
        """Acción para marcar facturas como revisadas con cambios."""
        updated = queryset.update(estado_revision="revisado_con_cambios", requiere_revision_manual=False)
        self.message_user(
            request, 
            f"{updated} factura(s) marcada(s) como 'Revisado con cambios'."
        )
    marcar_revisado_con_cambios.short_description = "Marcar como Revisado con cambios"
    
    def marcar_como_pagadas(self, request, queryset):
        """Acción para marcar múltiples facturas como pagadas con una fecha específica."""
        from django import forms
        from datetime import date
        
        # Formulario para seleccionar la fecha de pago
        class FechaPagoForm(forms.Form):
            fecha_pago = forms.DateField(
                label="Fecha de pago",
                initial=date.today(),
                widget=forms.DateInput(attrs={
                    'type': 'date',
                    'class': 'vDateField'
                }),
                help_text="Selecciona la fecha en que se realizaron los pagos"
            )
        
        # Si ya se envió el formulario
        if 'apply' in request.POST:
            form = FechaPagoForm(request.POST)
            
            if form.is_valid():
                fecha_pago = form.cleaned_data['fecha_pago']
                facturas_actualizadas = 0
                facturas_ya_pagadas = 0
                
                for factura in queryset:
                    if factura.pagado:
                        facturas_ya_pagadas += 1
                    else:
                        factura.pagado = True
                        factura.fecha_pago = fecha_pago
                        factura.save(update_fields=['pagado', 'fecha_pago'])
                        facturas_actualizadas += 1
                
                # Mensaje de éxito
                mensaje_partes = []
                if facturas_actualizadas > 0:
                    mensaje_partes.append(f"{facturas_actualizadas} factura(s) marcada(s) como pagadas el {fecha_pago.strftime('%d/%m/%Y')}")
                if facturas_ya_pagadas > 0:
                    mensaje_partes.append(f"{facturas_ya_pagadas} factura(s) ya estaban pagadas")
                
                self.message_user(request, ". ".join(mensaje_partes))
                return HttpResponseRedirect(request.get_full_path())
        
        # Mostrar formulario
        else:
            form = FechaPagoForm()
        
        # Preparar contexto
        facturas_pendientes = queryset.filter(pagado=False)
        facturas_ya_pagadas = queryset.filter(pagado=True)
        
        context = {
            'title': 'Marcar facturas como pagadas',
            'form': form,
            'queryset': queryset,
            'facturas_pendientes': facturas_pendientes,
            'facturas_ya_pagadas': facturas_ya_pagadas,
            'opts': self.model._meta,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        }
        
        return render(request, 'admin/ventas/marcar_como_pagadas.html', context)
    
    marcar_como_pagadas.short_description = "Marcar como pagadas (con fecha)"
    
    # ✅ Vista para reporte de diferencias por redondeo
    def reporte_diferencias_view(self, request):
        """
        Vista para mostrar reporte mensual de diferencias por redondeo.
        """
        # Obtener mes y año del request
        mes = int(request.GET.get('mes', datetime.now().month))
        año = int(request.GET.get('año', datetime.now().year))
        
        # Obtener facturas del período
        facturas = Factura.objects.filter(
            fecha_facturacion__month=mes,
            fecha_facturacion__year=año
        ).order_by('folio_factura')
        
        # Calcular diferencias
        total_diferencias = Decimal("0")
        facturas_con_diferencia = 0
        detalles_list = []
        
        for factura in facturas:
            num_detalles = factura.detalles.count()
            if num_detalles == 0:
                continue
            
            suma_detalles = sum(
                det.cantidad * det.precio_unitario 
                for det in factura.detalles.all()
            )
            
            diferencia = factura.total - suma_detalles
            
            if abs(diferencia) > Decimal("0.01"):
                facturas_con_diferencia += 1
                total_diferencias += diferencia
                
                detalles_list.append({
                    'folio': factura.folio_factura,
                    'cliente': factura.cliente,
                    'total': factura.total,
                    'suma': suma_detalles,
                    'diferencia': diferencia,
                })
        
        # Contexto para el template
        context = {
            **self.admin_site.each_context(request),
            'title': 'Reporte de Diferencias por Redondeo',
            'mes': mes,
            'año': año,
            'total_facturas': facturas.count(),
            'facturas_con_diferencia': facturas_con_diferencia,
            'total_diferencias': total_diferencias,
            'detalles_list': detalles_list,
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/ventas/reporte_diferencias.html', context)
    
    class Media:
        js = ('js/admin_vpg_form.js',)

# ✅ Registrar FacturaAdmin con Factura
admin.site.register(Factura, FacturaAdmin)


# ========== ADMIN PARA COMPLEMENTOS DE PAGO ==========

class DocumentoRelacionadoInline(admin.TabularInline):
    """Inline para mostrar documentos relacionados en el complemento."""
    model = DocumentoRelacionado
    extra = 0
    fields = (
        "factura",
        "num_parcialidad",
        "saldo_anterior",
        "importe_pagado",
        "saldo_insoluto",
        "pago_factura_display",
        "iva_desglosado",
        "ieps_desglosado"
    )
    readonly_fields = ("pago_factura_display",)
    
    def pago_factura_display(self, obj):
        """Muestra el PagoFactura vinculado con enlace."""
        if obj.pago_factura:
            url = reverse('admin:ventas_pagofactura_change', args=[obj.pago_factura.pk])
            return format_html(
                '<a href="{}" target="_blank">✅ Ver Pago #{} (${:,.2f})</a>',
                url,
                obj.pago_factura.pk,
                obj.pago_factura.monto
            )
        return format_html('<span style="color: #e74c3c;">⚠️ Sin vincular</span>')
    pago_factura_display.short_description = "Pago Interno Vinculado"


class ComplementoRelacionadoInline(admin.TabularInline):
    """Inline para mostrar complementos en el detalle de Factura."""
    model = DocumentoRelacionado
    extra = 0
    fields = (
        "complemento_link",
        "num_parcialidad",
        "importe_pagado",
        "saldo_insoluto",
        "fecha_emision_display"
    )
    readonly_fields = ("complemento_link", "fecha_emision_display")
    verbose_name = "Complemento de Pago Recibido"
    verbose_name_plural = "Complementos de Pago Recibidos"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def complemento_link(self, obj):
        """Enlace al complemento con folio."""
        if obj.complemento:
            url = reverse('admin:ventas_complementopago_change', args=[obj.complemento.pk])
            return format_html(
                '<a href="{}" target="_blank">💰 Complemento {} [Ver PDF]</a>',
                url,
                obj.complemento.folio_complemento
            )
        return "-"
    complemento_link.short_description = "Folio Complemento"
    
    def fecha_emision_display(self, obj):
        """Fecha de emisión del complemento."""
        if obj.complemento:
            return obj.complemento.fecha_emision.strftime("%d/%m/%Y")
        return "-"
    fecha_emision_display.short_description = "Fecha Emisión"


class ComplementoPagoAdmin(admin.ModelAdmin):
    list_display = (
        "folio_complemento",
        "cliente",
        "monto_total_display",
        "fecha_pago_display",
        "forma_pago_display",
        "facturas_pagadas_display",
        "estado_vinculacion_display"
    )
    list_filter = ("forma_pago_sat", "fecha_emision", "requiere_revision")
    search_fields = ("folio_complemento", "uuid_complemento", "cliente", "rfc_cliente")
    readonly_fields = ("creado_en", "actualizado_en", "facturas_relacionadas_info")
    
    fieldsets = (
        ("Identificación Fiscal", {
            "fields": ("folio_complemento", "uuid_complemento")
        }),
        ("Datos del Pago", {
            "fields": (
                "fecha_emision",
                "fecha_pago",
                "monto_total",
                "forma_pago_sat"
            )
        }),
        ("Cliente", {
            "fields": ("cliente", "rfc_cliente")
        }),
        ("Archivo", {
            "fields": ("archivo_pdf",)
        }),
        ("Facturas Relacionadas", {
            "fields": ("facturas_relacionadas_info",),
            "classes": ("wide",)
        }),
        ("Revisión y Notas", {
            "fields": (
                "requiere_revision",
                "motivo_revision",
                "notas",
                "creado_en",
                "actualizado_en"
            ),
            "classes": ("collapse",)
        })
    )
    
    inlines = [DocumentoRelacionadoInline]
    
    def monto_total_display(self, obj):
        """Muestra el monto con formato."""
        return format_html('<strong>${:,.2f}</strong>', obj.monto_total)
    monto_total_display.short_description = "Monto"
    monto_total_display.admin_order_field = "monto_total"
    
    def fecha_pago_display(self, obj):
        """Muestra la fecha de pago."""
        return obj.fecha_pago.strftime("%d/%m/%Y")
    fecha_pago_display.short_description = "Fecha de Pago"
    fecha_pago_display.admin_order_field = "fecha_pago"
    
    def forma_pago_display(self, obj):
        """Muestra la forma de pago."""
        return obj.get_forma_pago_sat_display()
    forma_pago_display.short_description = "Forma de Pago"
    
    def facturas_pagadas_display(self, obj):
        """Muestra las facturas que este complemento paga."""
        docs = obj.documentos_relacionados.all()
        if not docs:
            return format_html('<span style="color: #e74c3c;">⚠️ Sin facturas</span>')
        
        facturas = [f"#{doc.factura.folio_factura}" for doc in docs]
        return format_html(
            '<span style="color: #27ae60;">{}</span>',
            ", ".join(facturas)
        )
    facturas_pagadas_display.short_description = "Facturas Pagadas"
    
    def estado_vinculacion_display(self, obj):
        """Muestra si los pagos internos están vinculados."""
        docs = obj.documentos_relacionados.all()
        if not docs:
            return "-"
        
        total = docs.count()
        vinculados = sum(1 for doc in docs if doc.pago_factura)
        
        if vinculados == total:
            return format_html('<span style="color: #27ae60;">✅ Completo ({}/{})</span>', vinculados, total)
        elif vinculados > 0:
            return format_html('<span style="color: #f39c12;">⚠️ Parcial ({}/{})</span>', vinculados, total)
        else:
            return format_html('<span style="color: #e74c3c;">❌ Sin vincular</span>')
    estado_vinculacion_display.short_description = "Vinculación"
    
    def facturas_relacionadas_info(self, obj):
        """Muestra información detallada de las facturas relacionadas."""
        if not obj.pk:
            return "Guarda el complemento primero"
        
        docs = obj.documentos_relacionados.all()
        if not docs:
            return format_html('<p style="color: #e74c3c;">⚠️ Este complemento no tiene facturas relacionadas</p>')
        
        html = '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">'
        html += '<h3 style="margin-top: 0;">📄 Facturas Relacionadas</h3>'
        
        for doc in docs:
            factura_url = reverse('admin:ventas_factura_change', args=[doc.factura.pk])
            
            html += f'''
            <div style="border: 1px solid #dee2e6; padding: 10px; margin-bottom: 10px; border-radius: 4px; background: white;">
                <h4 style="margin: 0 0 10px 0;">
                    <a href="{factura_url}" target="_blank">Factura {doc.factura.folio_factura}</a>
                    - Parcialidad {doc.num_parcialidad}
                </h4>
                <table style="width: 100%;">
                    <tr>
                        <td><strong>Saldo anterior:</strong></td>
                        <td>${doc.saldo_anterior:,.2f}</td>
                    </tr>
                    <tr style="background: #d4edda;">
                        <td><strong>Importe pagado:</strong></td>
                        <td><strong>${doc.importe_pagado:,.2f}</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Saldo insoluto:</strong></td>
                        <td>${doc.saldo_insoluto:,.2f}</td>
                    </tr>
            '''
            
            if doc.pago_factura:
                pago_url = reverse('admin:ventas_pagofactura_change', args=[doc.pago_factura.pk])
                html += f'''
                    <tr style="background: #cfe2ff;">
                        <td><strong>Pago vinculado:</strong></td>
                        <td>
                            <a href="{pago_url}" target="_blank">
                                ✅ Pago #{doc.pago_factura.pk} (${doc.pago_factura.monto:,.2f})
                            </a>
                        </td>
                    </tr>
                '''
            else:
                html += '''
                    <tr style="background: #f8d7da;">
                        <td><strong>Pago vinculado:</strong></td>
                        <td>⚠️ Sin vincular al registro interno</td>
                    </tr>
                '''
            
            html += '</table></div>'
        
        html += '</div>'
        return format_html(html)
    facturas_relacionadas_info.short_description = "Detalle de Facturas"


# Agregar inline de complementos a FacturaAdmin
FacturaAdmin.inlines.append(ComplementoRelacionadoInline)

# Registrar ComplementoPago
admin.site.register(ComplementoPago, ComplementoPagoAdmin)

admin.site.index_title = "Sistema Novavino - Administración"
admin.site.site_header = "Novavino CRM"
admin.site.site_title = "Novavino Admin"