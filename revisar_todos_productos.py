"""
Revisar todos los productos y detectar posibles duplicaciones de stock
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto
from compras.models import CompraProducto

print("=== REVISION DE STOCK EN TODOS LOS PRODUCTOS ===\n")

# Buscar productos con posibles problemas
productos_sospechosos = []

for producto in Producto.objects.all():
    # Calcular stock esperado según CompraProducto
    compras = CompraProducto.objects.filter(producto=producto)
    
    if compras.exists():
        stock_compras = sum(cp.cantidad for cp in compras)
        stock_actual = producto.stock or 0
        
        # Si el stock actual es exactamente el doble, es sospechoso
        if stock_actual > 0 and stock_actual == stock_compras * 2:
            productos_sospechosos.append({
                'producto': producto,
                'stock_actual': stock_actual,
                'stock_esperado': stock_compras,
                'diferencia': stock_actual - stock_compras
            })

if productos_sospechosos:
    print(f"Encontrados {len(productos_sospechosos)} productos con stock duplicado:\n")
    
    for item in productos_sospechosos:
        producto = item['producto']
        print(f"[!] {producto.nombre}")
        print(f"    Stock actual: {item['stock_actual']}")
        print(f"    Stock esperado: {item['stock_esperado']}")
        print(f"    Diferencia: +{item['diferencia']}")
        
        # Corregir automáticamente
        producto.stock = item['stock_esperado']
        producto.save(update_fields=['stock'])
        print(f"    [OK] Corregido a {item['stock_esperado']}\n")
    
    print(f"\n=== RESUMEN ===")
    print(f"Total productos corregidos: {len(productos_sospechosos)}")
else:
    print("[OK] No se encontraron productos con stock duplicado")

# Buscar "Anécdota Blend" específicamente
print("\n=== ANECDOTA BLEND ===")
anecdota = Producto.objects.filter(nombre__icontains="anecdota").filter(nombre__icontains="blend").first()

if anecdota:
    compras_anecdota = CompraProducto.objects.filter(producto=anecdota)
    stock_compras_anecdota = sum(cp.cantidad for cp in compras_anecdota)
    
    print(f"Producto: {anecdota.nombre}")
    print(f"Stock actual: {anecdota.stock}")
    print(f"Stock según compras: {stock_compras_anecdota}")
    print(f"Compras registradas: {compras_anecdota.count()}")
    
    if compras_anecdota.exists():
        print("\nDetalles de compras:")
        for cp in compras_anecdota:
            print(f"  - Compra {cp.compra.folio} ({cp.compra.fecha}): {cp.cantidad} unidades")
else:
    print("No se encontró producto 'Anécdota Blend'")
