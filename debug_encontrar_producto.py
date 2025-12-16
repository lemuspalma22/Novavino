"""Debug: Ver qué devuelve encontrar_producto_unico para TRES RIBERAS"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.utils import encontrar_producto_unico

print("\n" + "="*70)
print("DEBUG: encontrar_producto_unico()")
print("="*70)

nombres_prueba = [
    'TRES RIBERAS "HA PASADO UN ÁNGEL" SEMIDU20.00',
    'TRES RIBERAS',
    'FLUMEN PROSECCO EXTRA DRY',
    'SAN ANTONIO HIDA BIANCO 750 ML',
]

for nombre in nombres_prueba:
    print(f"\nBuscando: '{nombre}'")
    print("-"*70)
    
    producto, error = encontrar_producto_unico(nombre)
    
    print(f"  Producto: {producto}")
    print(f"  Error: '{error}'")
    
    if producto:
        print(f"  [OK] ENCONTRADO: {producto.nombre}")
        print(f"       Precio: ${producto.precio_compra:,.2f}")
    else:
        if error == "not_found":
            print(f"  [INFO] NO ENCONTRADO - Crearia PNR")
        elif error == "multiple":
            print(f"  [ALERTA] MULTIPLES COINCIDENCIAS")
        else:
            print(f"  [INFO] Otro error: {error}")

print("\n" + "="*70 + "\n")
