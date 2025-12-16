"""Verificar qué nombre tiene guardado el PNR de TRES RIBERAS"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import ProductoNoReconocido
from compras.models import Compra

print("\n" + "="*70)
print("VERIFICAR: NOMBRE GUARDADO EN PNR - TRES RIBERAS")
print("="*70)

try:
    compra = Compra.objects.get(folio="2445")
    uuid = compra.uuid
    
    print(f"\nFactura: {compra.folio}")
    print(f"UUID: {uuid}")
    
    # Buscar PNR
    pnrs = ProductoNoReconocido.objects.filter(
        uuid_factura=uuid,
        procesado=False
    )
    
    print(f"\nPNRs encontrados: {pnrs.count()}")
    print("-"*70)
    
    for pnr in pnrs:
        print(f"\nID: {pnr.id}")
        print(f"Nombre detectado: '{pnr.nombre_detectado}'")
        print(f"Longitud: {len(pnr.nombre_detectado)} caracteres")
        
        # Verificar si es TRES RIBERAS
        if "TRES" in pnr.nombre_detectado.upper():
            print(f"\n[DIAGNOSTICO]")
            print(f"  Este es el PNR de TRES RIBERAS")
            print(f"  Nombre completo esperado: 'TRES RIBERAS \"HA PASADO UN ANGEL\"'")
            print(f"  Nombre guardado:          '{pnr.nombre_detectado}'")
            
            if "ANGEL" in pnr.nombre_detectado.upper():
                print(f"  [OK] Tiene el nombre completo")
            else:
                print(f"  [ERROR] El nombre está truncado!")
                print(f"  CAUSA: El PNR se creó con nombre incompleto")
                print(f"\n  SOLUCION:")
                print(f"    1. Editar el PNR en el admin")
                print(f"    2. Cambiar 'nombre_detectado' a: TRES RIBERAS HA PASADO UN ANGEL")
                print(f"    3. Guardar")
                print(f"    4. Crear el producto con ese nombre")
    
    print("\n" + "="*70 + "\n")

except Compra.DoesNotExist:
    print("\n[ERROR] Factura 2445 no encontrada")
    print("="*70 + "\n")
