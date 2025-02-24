from django.contrib import admin
from .models import Producto

class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "proveedor", "precio_venta", "stock", "es_personalizado")
    list_filter = ("proveedor", "es_personalizado")  # Agregamos filtro para productos personalizados
    search_fields = ("nombre", "proveedor__nombre")

admin.site.register(Producto, ProductoAdmin)
