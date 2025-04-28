from inventario.models import Producto, AliasProducto

def encontrar_producto(nombre_detectado):
    """
    Intenta encontrar un producto por nombre directo o por alias.
    Devuelve el objeto Producto o None si no encuentra coincidencias.
    """
    nombre = nombre_detectado.lower()

    # 1. Buscar coincidencia parcial en nombre del producto
    producto = Producto.objects.filter(nombre__icontains=nombre).first()
    if producto:
        return producto

    # 2. Buscar coincidencia parcial en alias
    alias = AliasProducto.objects.filter(alias__icontains=nombre).first()
    if alias:
        return alias.producto

    # 3. No encontrado
    return None
