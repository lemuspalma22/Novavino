"""
Eliminar alias redundantes (alias con el mismo nombre que el producto)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import AliasProducto

print("=== LIMPIEZA DE ALIAS REDUNDANTES ===\n")

alias_redundantes = []

for alias in AliasProducto.objects.select_related('producto').all():
    if alias.alias.strip().lower() == alias.producto.nombre.strip().lower():
        alias_redundantes.append({
            'id': alias.id,
            'alias': alias.alias,
            'producto': alias.producto.nombre
        })

if alias_redundantes:
    print(f"Encontrados {len(alias_redundantes)} alias redundantes:")
    for item in alias_redundantes:
        print(f"  - ID {item['id']}: '{item['alias']}' => {item['producto']}")
    
    print(f"\nEliminando...")
    for item in alias_redundantes:
        AliasProducto.objects.filter(id=item['id']).delete()
    
    print(f"\n[OK] {len(alias_redundantes)} alias redundantes eliminados")
else:
    print("[OK] No se encontraron alias redundantes")

# Corregir stock de EPICO si está duplicado
print("\n=== CORRECCION STOCK EPICO ===")
from inventario.models import Producto
from compras.models import CompraProducto

epico = Producto.objects.filter(nombre__icontains="EPICO").first()
if epico:
    compras = CompraProducto.objects.filter(producto=epico)
    stock_esperado = sum(cp.cantidad for cp in compras)
    
    print(f"Producto: {epico.nombre}")
    print(f"Stock actual: {epico.stock}")
    print(f"Stock esperado: {stock_esperado}")
    
    if epico.stock != stock_esperado:
        epico.stock = stock_esperado
        epico.save(update_fields=['stock'])
        print(f"[OK] Stock corregido a {stock_esperado}")
    else:
        print("[OK] Stock correcto")
