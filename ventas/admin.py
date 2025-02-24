from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import Factura, DetalleFactura

class DetalleFacturaInline(admin.TabularInline):  
    model = DetalleFactura
    extra = 1  # Número de filas vacías para añadir nuevos detalles
    fields = ("producto", "cantidad", "precio_unitario", "precio_compra", "subtotal")  # Agregamos precio_compra
    readonly_fields = ("subtotal",)  # El subtotal se calcula automáticamente y no debe editarse manualmente

    class Media:
        js = ("js/admin_detalle_factura.js",)  # Importa el script en Django Admin para autocompletar y calcular

class FacturaAdmin(admin.ModelAdmin):
    list_display = ("folio_factura", "cliente", "total", "costo_total", "ganancia", "pagado", "fecha_facturacion", "ver_corte_semanal")
    list_filter = ("pagado", "fecha_facturacion")
    search_fields = ("folio_factura", "cliente")
    inlines = [DetalleFacturaInline]  # Agregar detalles dentro de la factura

    # ✅ Función para calcular el costo total de la factura
    def costo_total(self, obj):
        return sum(detalle.precio_compra * detalle.cantidad for detalle in obj.detalles.all())

    # ✅ Función para calcular la ganancia
    def ganancia(self, obj):
        return obj.total - self.costo_total(obj)

    # ✅ Configurar nombres en Django Admin
    costo_total.short_description = "Costo Total"
    ganancia.short_description = "Ganancia Estimada"

    # ✅ Agregar columna con enlace al Corte Semanal en cada factura
    def ver_corte_semanal(self, obj):
        url = reverse("admin:corte_semanal")  # Usa el nombre de la URL de Django
        return format_html('<a href="{}" target="_blank">🔍 Ver Corte</a>', url)

    ver_corte_semanal.short_description = "Corte Semanal"

    # ✅ Agregar URL personalizada para ver el Corte Semanal en el Django Admin
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("corte-semanal/", self.admin_site.admin_view(self.corte_semanal_view), name="corte_semanal"),
        ]
        return custom_urls + urls

    # ✅ Redirigir a la vista de Corte Semanal
    def corte_semanal_view(self, request):
        return redirect("/ventas/corte-semanal/")  # Redirigir a la vista de corte semanal

# ✅ Registrar FacturaAdmin con Factura
admin.site.register(Factura, FacturaAdmin)

admin.site.index_title = "Sistema Novavino - Administración"
admin.site.site_header = "Novavino CRM"
admin.site.site_title = "Novavino Admin"