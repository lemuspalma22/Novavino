"""Investigar por qué TRES RIBERAS no se asigna/guarda"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import Producto, AliasProducto, ProductoNoReconocido
from inventario.utils import encontrar_producto_unico
from compras.models import Proveedor

print("\n" + "="*70)
print("INVESTIGAR: Por que TRES RIBERAS no se guarda")
print("="*70)

nombre_detectado = 'TRES RIBERAS "HA PASADO UN ÁNGEL" SEMIDU20.00'

print(f"\nNombre detectado por extractor:")
print(f"  '{nombre_detectado}'")

# Paso 1: Buscar si existe en BD
print("\n[1/3] Buscando en base de datos...")
print("-"*70)

# Buscar por nombre
productos = Producto.objects.filter(nombre__icontains="tres riberas")
if productos.exists():
    print(f"[OK] Encontrado {productos.count()} producto(s):")
    for prod in productos:
        print(f"  - {prod.nombre}")
        print(f"    Precio: ${prod.precio_compra:,.2f}")
        print(f"    Proveedor: {prod.proveedor.nombre if prod.proveedor else 'N/A'}")
else:
    print("[INFO] NO encontrado en BD por nombre")

# Buscar por alias
alias_encontrados = AliasProducto.objects.filter(alias__icontains="tres riberas")
if alias_encontrados.exists():
    print(f"\n[OK] Encontrado por alias ({alias_encontrados.count()}):")
    for alias in alias_encontrados:
        print(f"  - Alias: '{alias.alias}'")
        print(f"    Producto: {alias.producto.nombre}")
else:
    print("\n[INFO] NO encontrado por alias")

# Paso 2: Usar la función de búsqueda del sistema
print("\n[2/3] Probando función de búsqueda del sistema...")
print("-"*70)

try:
    producto, error = encontrar_producto_unico(nombre_detectado)
    
    if error == "found":
        print(f"[OK] ENCONTRADO:")
        print(f"  Producto: {producto.nombre}")
        print(f"  Precio: ${producto.precio_compra:,.2f}")
    elif error == "not_found":
        print("[INFO] NO ENCONTRADO - Se crearia ProductoNoReconocido (PNR)")
    elif error == "multiple":
        print("[ALERTA] MULTIPLES COINCIDENCIAS - Ambiguo")
    else:
        print(f"[INFO] Error: {error}")
        
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

# Paso 3: Verificar PNR
print("\n[3/3] Verificando Productos No Reconocidos...")
print("-"*70)

pnrs = ProductoNoReconocido.objects.filter(
    nombre_detectado__icontains="tres riberas",
    procesado=False
)

if pnrs.exists():
    print(f"[INFO] Encontrados {pnrs.count()} PNR pendientes:")
    for pnr in pnrs:
        print(f"  - '{pnr.nombre_detectado}'")
        print(f"    UUID: {pnr.uuid_factura}")
        print(f"    Fecha: {pnr.fecha_detectado}")
else:
    print("[INFO] No hay PNR para TRES RIBERAS")

print("\n" + "="*70)
print("DIAGNOSTICO:")
print("-"*70)

if not productos.exists() and not alias_encontrados.exists():
    print("\n[PROBLEMA] TRES RIBERAS no existe en la base de datos")
    print("\nCausas:")
    print("  1. Es un producto nuevo que nunca se ha registrado")
    print("  2. No se ha creado ni se ha agregado como alias")
    print("\nSoluciones:")
    print("  A. Crear el producto en BD con precio correcto")
    print("  B. Agregar alias para que se detecte automaticamente")
    print("  C. Dejarlo como PNR y asignarlo manualmente desde admin")
    print("\nRecomendacion:")
    print("  - Crear producto 'TRES RIBERAS HA PASADO UN ANGEL'")
    print("  - Proveedor: Secretos de la Vid")
    print("  - Precio: $117.80 (con impuestos y descuento)")
    
    # Calcular precio sin impuestos
    precio_con_todo = 117.80
    # El precio en la factura ya tiene: IEPS 26.5% + IVA 16% - Descuento 24%
    # Para obtener el precio base: P_base * 1.265 * 1.16 * 0.76 = 117.80
    # P_base = 117.80 / (1.265 * 1.16 * 0.76)
    precio_base = precio_con_todo / (1.265 * 1.16 * 0.76)
    
    print(f"  - Precio base (sin impuestos): ${precio_base:.4f}")
    print(f"  - O simplemente usar: ${precio_con_todo} (ya con impuestos)")

else:
    print("\n[INFO] El producto SI existe en BD")
    print("       El problema puede estar en la busqueda o nombre muy diferente")

print("="*70 + "\n")

# Opción: Crear el producto automáticamente
print("=" * 70)
print("OPCION: CREAR PRODUCTO AUTOMATICAMENTE")
print("="*70)

print("\n¿Quieres que cree el producto TRES RIBERAS en BD?")
print("  (Ejecuta: python crear_producto_tres_riberas.py)")

print("="*70 + "\n")
