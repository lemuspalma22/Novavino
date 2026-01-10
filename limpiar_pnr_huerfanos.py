"""
Limpiar ProductoNoReconocido huérfanos (sin factura/compra asociada)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import ProductoNoReconocido
from compras.models import Compra
from ventas.models import Factura

print("=== LIMPIEZA DE PNR HUERFANOS ===\n")

# Buscar PNR huérfanos
pnr_con_uuid = ProductoNoReconocido.objects.exclude(uuid_factura__isnull=True).exclude(uuid_factura='')
huerfanos_eliminar = []

for pnr in pnr_con_uuid:
    existe = False
    
    if pnr.origen == "compra":
        # Buscar en Compra
        existe = Compra.objects.filter(uuid=pnr.uuid_factura).exists() or \
                 Compra.objects.filter(uuid_sat=pnr.uuid_factura).exists()
    elif pnr.origen == "venta":
        # Buscar en Factura
        existe = Factura.objects.filter(uuid_factura=pnr.uuid_factura).exists()
    
    if not existe:
        huerfanos_eliminar.append(pnr)

if not huerfanos_eliminar:
    print("[OK] No hay PNR huerfanos para eliminar")
else:
    print(f"Encontrados {len(huerfanos_eliminar)} PNR huerfanos:\n")
    
    for pnr in huerfanos_eliminar:
        print(f"  - ID {pnr.id}: {pnr.nombre_detectado}")
        print(f"    Origen: {pnr.origen}, UUID: {pnr.uuid_factura[:40]}...")
        print(f"    Procesado: {pnr.procesado}, Producto: {pnr.producto_id}")
    
    print(f"\nEliminando {len(huerfanos_eliminar)} PNR huerfanos...")
    
    for pnr in huerfanos_eliminar:
        pnr.delete()
    
    print(f"[OK] {len(huerfanos_eliminar)} PNR huerfanos eliminados")

print("\n=== ESTADISTICAS FINALES ===")
total_pnr = ProductoNoReconocido.objects.count()
pnr_procesados = ProductoNoReconocido.objects.filter(procesado=True).count()
pnr_pendientes = ProductoNoReconocido.objects.filter(procesado=False).count()

print(f"Total PNR restantes: {total_pnr}")
print(f"  - Procesados: {pnr_procesados}")
print(f"  - Pendientes: {pnr_pendientes}")
