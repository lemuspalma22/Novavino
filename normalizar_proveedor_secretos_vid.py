"""
Script para normalizar el proveedor de todos los productos de Secretos de la Vid.
Unifica todas las variaciones bajo un solo proveedor estándar.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Proveedor
from inventario.models import Producto

print("="*80)
print(" NORMALIZACION DE PROVEEDOR: SECRETOS DE LA VID")
print("="*80)
print()

# Nombre estándar del proveedor (el que usa el extractor)
NOMBRE_ESTANDAR = "Secretos de la Vid S de RL de CV"

# Variaciones conocidas del nombre
VARIACIONES = [
    "Secretos de la vid",
    "SECRETOS DE LA VID",
    "Secretos de la Vid",
    "Secretos De La Vid",
    "secretos de la vid",
]

print(f"[*] Proveedor estandar: {NOMBRE_ESTANDAR}")
print()

# 1. Obtener o crear el proveedor estándar
print("[1] Verificando proveedor estandar...")
proveedor_estandar, creado = Proveedor.objects.get_or_create(
    nombre=NOMBRE_ESTANDAR
)

if creado:
    print(f"    [NUEVO] Proveedor estandar creado: {NOMBRE_ESTANDAR}")
else:
    print(f"    [OK] Proveedor estandar ya existe (ID: {proveedor_estandar.id})")
print()

# 2. Buscar todas las variaciones del proveedor
print("[2] Buscando variaciones del proveedor...")
proveedores_variaciones = []

for variacion in VARIACIONES:
    provs = Proveedor.objects.filter(nombre__iexact=variacion).exclude(id=proveedor_estandar.id)
    if provs.exists():
        for prov in provs:
            proveedores_variaciones.append(prov)
            print(f"    [ENCONTRADO] '{prov.nombre}' (ID: {prov.id})")

if not proveedores_variaciones:
    print("    [OK] No se encontraron variaciones")
print()

# 3. Contar productos afectados
print("[3] Analizando productos...")
productos_por_actualizar = []

for prov_variacion in proveedores_variaciones:
    productos = Producto.objects.filter(proveedor=prov_variacion)
    count = productos.count()
    
    if count > 0:
        print(f"    [INFO] {count} producto(s) con proveedor '{prov_variacion.nombre}'")
        for prod in productos:
            productos_por_actualizar.append(prod)

# También verificar productos que ya tienen el proveedor estándar
productos_estandar = Producto.objects.filter(proveedor=proveedor_estandar)
print(f"    [INFO] {productos_estandar.count()} producto(s) ya tienen el proveedor estandar")
print()

# 4. Actualizar productos
if productos_por_actualizar:
    print(f"[4] Actualizando {len(productos_por_actualizar)} producto(s)...")
    print()
    
    for i, producto in enumerate(productos_por_actualizar, 1):
        proveedor_anterior = producto.proveedor.nombre
        producto.proveedor = proveedor_estandar
        producto.save(update_fields=['proveedor'])
        print(f"    [{i}/{len(productos_por_actualizar)}] '{producto.nombre}'")
        print(f"         Antes: {proveedor_anterior}")
        print(f"         Ahora: {NOMBRE_ESTANDAR}")
    
    print()
    print(f"[OK] {len(productos_por_actualizar)} producto(s) actualizados")
else:
    print("[4] No hay productos por actualizar")
print()

# 5. Verificar compras con variaciones
print("[5] Verificando compras...")
from compras.models import Compra

for prov_variacion in proveedores_variaciones:
    compras = Compra.objects.filter(proveedor=prov_variacion)
    count = compras.count()
    
    if count > 0:
        print(f"    [ATENCION] {count} compra(s) con proveedor '{prov_variacion.nombre}'")
        print(f"               Considera actualizar tambien las compras si es necesario")

print()

# 6. Resumen final
print("="*80)
print(" RESUMEN")
print("="*80)
print()
print(f"Proveedor estandar:          {NOMBRE_ESTANDAR} (ID: {proveedor_estandar.id})")
print(f"Variaciones encontradas:     {len(proveedores_variaciones)}")
print(f"Productos actualizados:      {len(productos_por_actualizar)}")
print(f"Productos con prov. estandar: {productos_estandar.count()}")
print()

# Total de productos de Secretos de la Vid
total_productos_sv = Producto.objects.filter(proveedor=proveedor_estandar).count()
print(f"[VERIFICACION]")
print(f"Total de productos de Secretos de la Vid: {total_productos_sv}")
print()

print("="*80)
print()
print("[SIGUIENTE PASO]")
print("Verifica en el admin que todos los productos de Secretos de la Vid")
print("ahora tienen el proveedor unificado:")
print()
print(f"  http://localhost:8000/admin/inventario/producto/?proveedor__id__exact={proveedor_estandar.id}")
print()
print("="*80)
print()
