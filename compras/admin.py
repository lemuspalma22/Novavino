from django.contrib import admin
from .models import Compra, Proveedor, CompraProducto
from inventario.models import Producto  # Importamos Producto para manejarlo en el admin

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
    list_display = ("compra", "producto", "cantidad", "precio_unitario")
    search_fields = ("producto__nombre", "compra__folio")

# Registro de modelos en el admin
admin.site.register(Compra)
admin.site.register(Proveedor, ProveedorAdmin)
admin.site.register(CompraProducto, CompraProductoAdmin)  
