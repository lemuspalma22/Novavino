from django.contrib import admin
from django.contrib.admin import TabularInline
from .models import Factura, DetalleFactura

class DetalleFacturaInline(admin.TabularInline):  
    model = DetalleFactura
    extra = 1  # Número de filas vacías para añadir nuevos detalles
    fields = ("producto", "cantidad", "precio_unitario", "precio_compra", "subtotal")  # Agregamos precio_compra
    readonly_fields = ("subtotal",)  # El subtotal se calcula automáticamente y no debe editarse manualmente

    class Media:
        js = ("js/admin_detalle_factura.js",)  # Importa el script en Django Admin para autocompletar y calcular

class FacturaAdmin(admin.ModelAdmin):
    list_display = ("folio_factura", "cliente", "total", "costo_total", "ganancia", "pagado", "fecha_facturacion")
    list_filter = ("pagado", "fecha_facturacion")
    search_fields = ("folio_factura", "cliente")
    inlines = [DetalleFacturaInline]  # Agregar detalles dentro de la factura

    # **Función para calcular el costo total de la factura**
    def costo_total(self, obj):
        return sum(detalle.precio_compra * detalle.cantidad for detalle in obj.detalles.all())

    # **Función para calcular la ganancia**
    def ganancia(self, obj):
        return obj.total - self.costo_total(obj)

    # Configurar nombres en Django Admin
    costo_total.short_description = "Costo Total"
    ganancia.short_description = "Ganancia Estimada"

admin.site.register(Factura, FacturaAdmin)