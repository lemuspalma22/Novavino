from django.contrib import admin
from django.contrib import messages
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from .models import Factura, DetalleFactura
from django.db.models import Sum, F


class DetalleFacturaInline(admin.TabularInline):  
    model = DetalleFactura
    extra = 1  # Número de filas vacías para añadir nuevos detalles
    fields = ("producto", "cantidad", "precio_unitario", "precio_compra", "subtotal")  # Agregamos precio_compra
    readonly_fields = ("subtotal",)  # El subtotal se calcula automáticamente y no debe editarse manualmente

    def subtotal(self, obj):
        if not obj or obj.cantidad is None or obj.precio_unitario is None:
            return 0
        return obj.cantidad * obj.precio_unitario
    subtotal.short_description = "Subtotal"
    
    class Media:
        js = ("js/admin_detalle_factura.js",)  # Importa el script en Django Admin para autocompletar y calcular

class FacturaAdmin(admin.ModelAdmin):
    list_display = ("folio_factura", "cliente", "total", "costo_total", "ganancia", "metodo_pago", "pagado", "fecha_pago_display", "fecha_facturacion")
    list_filter = ("pagado", "metodo_pago", "fecha_facturacion")
    search_fields = ("folio_factura", "cliente")
    readonly_fields = ("total_display",)
    fieldsets = (
        (None, {
            "fields": (
                "folio_factura",
                "cliente",
                "fecha_facturacion",
                "vencimiento",
                "metodo_pago",
                "pagado",
                "fecha_pago",
                "notas",
                "total_display",   # <- etiqueta "Total"
            )
        }),
    )
    inlines = [DetalleFacturaInline]  # Agregar detalles dentro de la factura
 
    def total_display(self, obj):
        # Si aún no existe en BD o no tiene total, muéstralo como 0.00
        val = getattr(obj, "total", None)
        if val is None:
            val = 0
        # Span con id para que el JS lo actualice en vivo
        return format_html('<span id="total-display">{:.2f}</span>', val)
    total_display.short_description = "Total"
    
    # ✅ Función para calcular el costo total de la factura
    def costo_total(self, obj):
        return sum(detalle.precio_compra * detalle.cantidad for detalle in obj.detalles.all())

    # ✅ Función para calcular la ganancia
    def ganancia(self, obj):
        return obj.total - self.costo_total(obj)

    # ✅ Configurar nombres en Django Admin
    costo_total.short_description = "Costo Total"
    ganancia.short_description = "Ganancia Estimada"

    # ✅ Función para mostrar fecha de pago formateada
    def fecha_pago_display(self, obj):
        if obj.fecha_pago:
            return obj.fecha_pago.strftime("%Y-%m-%d")
        return "-"
    fecha_pago_display.short_description = "Fecha de Pago"
    fecha_pago_display.admin_order_field = "fecha_pago"  # Permite ordenar por esta columna

    # ✅ Agregar URLs personalizadas
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("corte-semanal/", self.admin_site.admin_view(self.corte_semanal_view), name="corte_semanal"),
            path('procesar-drive/', self.admin_site.admin_view(self.procesar_drive_view), name='ventas_factura_procesar_drive'),
        ]
        return custom_urls + urls

    # ✅ Agregar botón personalizado en la vista de lista
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_drive_button'] = True
        return super().changelist_view(request, extra_context)
    
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

# ✅ Registrar FacturaAdmin con Factura
admin.site.register(Factura, FacturaAdmin)

admin.site.index_title = "Sistema Novavino - Administración"
admin.site.site_header = "Novavino CRM"
admin.site.site_title = "Novavino Admin"