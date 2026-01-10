"""
Script para sincronizar el costo_transporte de todos los productos
con el costo_transporte_unitario de su proveedor.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto
from compras.models import Proveedor
from decimal import Decimal

print("\n" + "="*70)
print("SINCRONIZACION: COSTOS DE TRANSPORTE")
print("="*70)

# Obtener todos los productos
productos = Producto.objects.select_related('proveedor').all()

actualizados = 0
sin_cambios = 0
errores = []

print("\nProcesando productos...")
print("-"*70)

for p in productos:
    try:
        costo_proveedor = p.proveedor.costo_transporte_unitario or Decimal("0.00")
        costo_actual = p.costo_transporte or Decimal("0.00")
        
        if costo_proveedor != costo_actual:
            print(f"  [ACTUALIZANDO] {p.nombre}")
            print(f"    {p.proveedor.nombre}: ${costo_actual} -> ${costo_proveedor}")
            p.costo_transporte = costo_proveedor
            p.save()
            actualizados += 1
        else:
            sin_cambios += 1
    except Exception as e:
        errores.append({
            'producto': p.nombre,
            'error': str(e)
        })

print("\n" + "="*70)
print("RESULTADOS")
print("="*70)
print(f"  Total productos: {productos.count()}")
print(f"  Actualizados: {actualizados}")
print(f"  Sin cambios: {sin_cambios}")
print(f"  Errores: {len(errores)}")

if errores:
    print("\nErrores encontrados:")
    for e in errores:
        print(f"  - {e['producto']}: {e['error']}")

print("\n" + "="*70)

# Verificar específicamente los proveedores principales
print("\nVerificacion de proveedores principales:")
print("-"*70)

vbm = Proveedor.objects.filter(nombre__icontains="Vieja Bodega").first()
sdv = Proveedor.objects.filter(nombre__icontains="Secretos").first()

if vbm:
    productos_vbm = Producto.objects.filter(proveedor=vbm)
    print(f"\nVieja Bodega (${vbm.costo_transporte_unitario}):")
    print(f"  Productos: {productos_vbm.count()}")
    incorrectos_vbm = productos_vbm.exclude(costo_transporte=vbm.costo_transporte_unitario)
    if incorrectos_vbm.exists():
        print(f"  [ADVERTENCIA] {incorrectos_vbm.count()} productos con costo incorrecto")
    else:
        print(f"  [OK] Todos los productos sincronizados")

if sdv:
    productos_sdv = Producto.objects.filter(proveedor=sdv)
    print(f"\nSecretos de la Vid (${sdv.costo_transporte_unitario}):")
    print(f"  Productos: {productos_sdv.count()}")
    incorrectos_sdv = productos_sdv.exclude(costo_transporte=sdv.costo_transporte_unitario)
    if incorrectos_sdv.exists():
        print(f"  [ADVERTENCIA] {incorrectos_sdv.count()} productos con costo incorrecto")
    else:
        print(f"  [OK] Todos los productos sincronizados")

print("\n" + "="*70)
print("COMPLETADO")
print("="*70)
print("\nAhora puedes:")
print("1. Verificar con: python verificar_costos_transporte.py")
print("2. Crear facturas en el admin con costos correctos")
print("3. El corte semanal usara el costo total (precio_compra + transporte)")
print("\n" + "="*70 + "\n")
