"""
Corrección manual del stock de BACALAUH
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto
from compras.models import CompraProducto

# Buscar el producto
producto = Producto.objects.filter(nombre__icontains="BACALAUH").first()

if not producto:
    print("No se encontró el producto BACALAUH")
else:
    print(f"=== {producto.nombre} ===")
    print(f"Stock actual: {producto.stock}")
    
    # Buscar CompraProducto asociados
    compras = CompraProducto.objects.filter(producto=producto)
    
    print(f"\nCompras asociadas: {compras.count()}")
    for cp in compras:
        print(f"  - Compra {cp.compra.folio}: {cp.cantidad} unidades")
    
    # Calcular stock correcto
    stock_correcto = sum(cp.cantidad for cp in compras)
    
    print(f"\nStock correcto debería ser: {stock_correcto}")
    
    if producto.stock != stock_correcto:
        print(f"\n[!] Diferencia detectada: {producto.stock} vs {stock_correcto}")
        print(f"[>] Corrigiendo automaticamente...")
        
        producto.stock = stock_correcto
        producto.save(update_fields=['stock'])
        print(f"[OK] Stock corregido a {stock_correcto}")
    else:
        print("\n[OK] El stock es correcto")
