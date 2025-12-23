"""
Script para corregir stock duplicado en productos creados desde PNR
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto, ProductoNoReconocido
from compras.models import CompraProducto
from decimal import Decimal

print("=== CORRECCIÓN DE STOCK DUPLICADO ===\n")

# Buscar PNR que tienen movimiento_generado=True y procesado=True
pnrs_procesados = ProductoNoReconocido.objects.filter(
    movimiento_generado=True,
    procesado=True,
    producto__isnull=False
)

print(f"Encontrados {pnrs_procesados.count()} PNR procesados\n")

productos_corregidos = []

for pnr in pnrs_procesados:
    producto = pnr.producto
    cantidad_pnr = int(pnr.cantidad or 0)
    
    # Buscar CompraProducto asociados a este producto
    compras_producto = CompraProducto.objects.filter(
        producto=producto,
        compra__uuid=pnr.uuid_factura
    )
    
    if compras_producto.exists():
        # Suma total de cantidades en CompraProducto
        cantidad_compras = sum(cp.cantidad for cp in compras_producto)
        
        # Stock esperado
        stock_esperado = cantidad_compras
        
        # Stock actual
        stock_actual = producto.stock or 0
        
        # Si el stock actual es el doble del esperado, corregir
        if stock_actual == stock_esperado * 2:
            print(f"❌ {producto.nombre}")
            print(f"   Stock actual: {stock_actual}")
            print(f"   Stock esperado: {stock_esperado}")
            print(f"   Cantidad en CompraProducto: {cantidad_compras}")
            print(f"   → CORRIGIENDO...")
            
            producto.stock = stock_esperado
            producto.save(update_fields=['stock'])
            
            productos_corregidos.append(producto.nombre)
            print(f"   ✓ Stock corregido a {stock_esperado}\n")

if productos_corregidos:
    print(f"\n=== RESUMEN ===")
    print(f"Productos corregidos: {len(productos_corregidos)}")
    for nombre in productos_corregidos:
        print(f"  - {nombre}")
else:
    print("No se encontraron productos con stock duplicado")
