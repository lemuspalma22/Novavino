"""Verificar si se creó PNR para TRES RIBERAS en factura 2445"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import ProductoNoReconocido
from compras.models import Compra

print("\n" + "="*70)
print("VERIFICAR: PNR de TRES RIBERAS - Factura 2445")
print("="*70)

# Buscar factura
try:
    compra = Compra.objects.get(folio="2445")
    uuid = compra.uuid
    
    print(f"\nFactura: {compra.folio}")
    print(f"UUID: {uuid}")
    
    # Buscar PNR con ese UUID
    pnrs = ProductoNoReconocido.objects.filter(uuid_factura=uuid)
    
    print(f"\nPNRs encontrados: {pnrs.count()}")
    print("-"*70)
    
    if pnrs.exists():
        for pnr in pnrs:
            print(f"\n[PNR] {pnr.nombre_detectado}")
            print(f"  ID: {pnr.id}")
            print(f"  Cantidad: {pnr.cantidad}")
            print(f"  Precio: ${pnr.precio_unitario:,.2f}" if pnr.precio_unitario else "  Precio: N/A")
            print(f"  Procesado: {pnr.procesado}")
            print(f"  Origen: {pnr.origen}")
            
            # Verificar si es TRES RIBERAS
            if "TRES" in pnr.nombre_detectado.upper() or "RIBERA" in pnr.nombre_detectado.upper():
                print(f"  [OK] ES TRES RIBERAS!")
    else:
        print("\n[INFO] No se encontraron PNRs")
    
    # Buscar TODOS los PNR con TRES RIBERAS
    print(f"\n{'='*70}")
    print("Todos los PNR con 'TRES RIBERAS':")
    print("-"*70)
    
    todos_tres_riberas = ProductoNoReconocido.objects.filter(
        nombre_detectado__icontains="TRES"
    )
    
    if todos_tres_riberas.exists():
        for pnr in todos_tres_riberas:
            print(f"\n- {pnr.nombre_detectado}")
            print(f"  UUID: {pnr.uuid_factura}")
            print(f"  Procesado: {pnr.procesado}")
    else:
        print("\n[INFO] No hay PNR con TRES en el nombre")
    
    print("\n" + "="*70)
    
except Compra.DoesNotExist:
    print("\n[ERROR] Factura 2445 no encontrada")
    print("="*70 + "\n")
