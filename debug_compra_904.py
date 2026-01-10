"""
Debug para verificar CompraProducto de la factura 904
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto
from inventario.models import Producto

# Buscar la compra
uuid = "bea97df9-35b3-4d7f-92d2-2ef0b4fb948f"
compra = Compra.objects.filter(uuid__istartswith="bea97df9").first()

if not compra:
    print("No se encontró la compra")
else:
    print(f"=== COMPRA {compra.folio} ===")
    print(f"UUID: {compra.uuid}")
    print(f"Fecha: {compra.fecha}")
    print(f"Total: ${compra.total}")
    
    print(f"\n=== PRODUCTOS EN COMPRA ({compra.productos.count()}) ===")
    for cp in compra.productos.all():
        print(f"\n{cp.producto.nombre}")
        print(f"  Cantidad en CompraProducto: {cp.cantidad}")
        print(f"  P.U.: ${cp.precio_unitario}")
        print(f"  Stock actual del producto: {cp.producto.stock}")

# Buscar el producto específico
print("\n=== BUSCAR: BACALAUH ===")
productos = Producto.objects.filter(nombre__icontains="BACALAUH")
if productos.exists():
    for p in productos:
        print(f"\nProducto: {p.nombre}")
        print(f"  ID: {p.id}")
        print(f"  Stock: {p.stock}")
        print(f"  Proveedor: {p.proveedor}")
        
        # Contar cuántas veces aparece en compras
        compras_count = CompraProducto.objects.filter(producto=p).count()
        print(f"  Aparece en {compras_count} CompraProducto(s)")
        
        if compras_count > 0:
            print(f"\n  Detalles de CompraProductos:")
            for cp in CompraProducto.objects.filter(producto=p):
                print(f"    - Compra {cp.compra.folio}: {cp.cantidad} unidades")
else:
    print("No se encontró el producto")
