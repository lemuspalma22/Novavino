"""
Corregir stock de EPICO
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto, ProductoNoReconocido
from compras.models import CompraProducto

print("=== CORRECCION EPICO ===")

epico = Producto.objects.filter(nombre__icontains="EPICO").first()

if epico:
    print(f"Producto: {epico.nombre}")
    print(f"Stock actual: {epico.stock}")
    
    compras = CompraProducto.objects.filter(producto=epico)
    stock_compras = sum(cp.cantidad for cp in compras)
    
    print(f"Stock esperado: {stock_compras}")
    print(f"Diferencia: {epico.stock - stock_compras}")
    
    if epico.stock != stock_compras:
        epico.stock = stock_compras
        epico.save(update_fields=['stock'])
        print(f"\n[OK] Stock corregido a {stock_compras}")
    
    # Marcar PNR como movimiento_generado=True para evitar re-procesamiento
    pnrs = ProductoNoReconocido.objects.filter(
        producto=epico,
        movimiento_generado=False
    )
    
    if pnrs.exists():
        print(f"\n[!] Encontrados {pnrs.count()} PNR sin marcar movimiento_generado")
        for pnr in pnrs:
            pnr.movimiento_generado = True
            pnr.save(update_fields=['movimiento_generado'])
            print(f"    - PNR {pnr.id} marcado como generado")
else:
    print("No se encontro EPICO")
