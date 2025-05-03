from django.contrib import admin
from .models import Producto, AliasProducto, ProductoNoReconocido


class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "proveedor", "precio_venta", "stock", "es_personalizado")
    list_filter = ("proveedor", "es_personalizado")
    search_fields = ("nombre", "proveedor__nombre")

class AliasProductoAdmin(admin.ModelAdmin):
    list_display = ("alias", "producto")
    search_fields = ("alias", "producto__nombre")

class ProductoNoReconocidoAdmin(admin.ModelAdmin):
    list_display = ("nombre_detectado", "fecha_detectado", "uuid_factura", "procesado")
    list_filter = ("procesado","origen")
    search_fields = ("nombre_detectado", "uuid_factura")

admin.site.register(Producto, ProductoAdmin)
admin.site.register(AliasProducto, AliasProductoAdmin)
admin.site.register(ProductoNoReconocido, ProductoNoReconocidoAdmin)
