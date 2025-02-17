from django.http import JsonResponse
from inventario.models import Producto

def get_producto_precio(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
        return JsonResponse({"precio_unitario": str(producto.precio_venta)})
    except Producto.DoesNotExist:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)
