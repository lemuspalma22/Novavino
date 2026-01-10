"""
Script para verificar que los productos tengan el costo de transporte configurado.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto
from compras.models import Proveedor
from decimal import Decimal

print("\n" + "="*70)
print("VERIFICACION: COSTOS DE TRANSPORTE")
print("="*70)

# Verificar proveedores
print("\n[1/3] Proveedores y sus costos de transporte:")
print("-"*70)
proveedores = Proveedor.objects.all()
for p in proveedores:
    costo = p.costo_transporte_unitario or Decimal("0.00")
    print(f"  {p.nombre}: ${costo}")

# Verificar productos sin costo_transporte
print("\n[2/3] Productos SIN costo de transporte configurado:")
print("-"*70)
productos_sin_costo = Producto.objects.filter(costo_transporte=0)
if productos_sin_costo.exists():
    print(f"  [ADVERTENCIA] Hay {productos_sin_costo.count()} productos sin costo de transporte:")
    for p in productos_sin_costo[:10]:
        print(f"    - {p.nombre} (Proveedor: {p.proveedor.nombre})")
    if productos_sin_costo.count() > 10:
        print(f"    ... y {productos_sin_costo.count() - 10} mas")
else:
    print("  [OK] Todos los productos tienen costo de transporte configurado")

# Verificar productos con costo incorrecto
print("\n[3/3] Verificar productos vs. costo del proveedor:")
print("-"*70)
productos = Producto.objects.select_related('proveedor').all()
discrepancias = []

for p in productos:
    costo_proveedor = p.proveedor.costo_transporte_unitario or Decimal("0.00")
    costo_producto = p.costo_transporte or Decimal("0.00")
    
    if costo_proveedor != costo_producto:
        discrepancias.append({
            'producto': p.nombre,
            'proveedor': p.proveedor.nombre,
            'costo_proveedor': costo_proveedor,
            'costo_producto': costo_producto
        })

if discrepancias:
    print(f"  [ADVERTENCIA] Hay {len(discrepancias)} productos con costos diferentes al proveedor:")
    for d in discrepancias[:10]:
        print(f"    - {d['producto']} ({d['proveedor']})")
        print(f"      Proveedor: ${d['costo_proveedor']} | Producto: ${d['costo_producto']}")
    if len(discrepancias) > 10:
        print(f"    ... y {len(discrepancias) - 10} mas")
else:
    print("  [OK] Todos los productos tienen el costo correcto del proveedor")

print("\n" + "="*70)
print("RESUMEN")
print("="*70)

# Verificar específicamente Vieja Bodega y Secretos de la Vid
vbm = Proveedor.objects.filter(nombre__icontains="Vieja Bodega").first()
sdv = Proveedor.objects.filter(nombre__icontains="Secretos").first()

if vbm:
    costo_vbm = vbm.costo_transporte_unitario or Decimal("0.00")
    esperado_vbm = Decimal("28.00")
    if costo_vbm == esperado_vbm:
        print(f"  [OK] Vieja Bodega: ${costo_vbm} (correcto)")
    else:
        print(f"  [ERROR] Vieja Bodega: ${costo_vbm} (esperado: $28.00)")
else:
    print("  [ADVERTENCIA] No se encontro proveedor 'Vieja Bodega'")

if sdv:
    costo_sdv = sdv.costo_transporte_unitario or Decimal("0.00")
    esperado_sdv = Decimal("15.00")
    if costo_sdv == esperado_sdv:
        print(f"  [OK] Secretos de la Vid: ${costo_sdv} (correcto)")
    else:
        print(f"  [ERROR] Secretos de la Vid: ${costo_sdv} (esperado: $15.00)")
else:
    print("  [ADVERTENCIA] No se encontro proveedor 'Secretos de la Vid'")

print("\n" + "="*70)
print("ACCION NECESARIA")
print("="*70)

if productos_sin_costo.exists() or discrepancias:
    print("\nSi hay productos con costo incorrecto, ejecuta:")
    print("  python sincronizar_costos_transporte.py")
    print("\nEsto sincronizara todos los productos con el costo del proveedor.")
else:
    print("\n[OK] Todo esta configurado correctamente.")
    print("El corte semanal calculara los costos correctamente.")

print("\n" + "="*70 + "\n")
