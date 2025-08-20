# inventario/utils.py
from inventario.models import Producto, AliasProducto

def encontrar_producto(nombre_detectado: str):
    """
    Intenta encontrar un producto por nombre directo o por alias.
    Devuelve el objeto Producto o None si no encuentra coincidencias.
    """
    nombre = (nombre_detectado or "").strip().lower()
    if not nombre:
        return None

    # 1) Coincidencia por nombre
    producto = Producto.objects.filter(nombre__icontains=nombre).first()
    if producto:
        return producto

    # 2) Coincidencia por alias
    alias = AliasProducto.objects.filter(alias__icontains=nombre).first()
    if alias:
        return alias.producto

    # 3) No encontrado
    return None
