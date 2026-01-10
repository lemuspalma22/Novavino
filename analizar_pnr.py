"""
Analizar ProductoNoReconocido en la base de datos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import ProductoNoReconocido
from compras.models import Compra
from ventas.models import Factura

print("=== ANALISIS DE PRODUCTOS NO RECONOCIDOS ===\n")

# Estadísticas generales
total_pnr = ProductoNoReconocido.objects.count()
pnr_procesados = ProductoNoReconocido.objects.filter(procesado=True).count()
pnr_pendientes = ProductoNoReconocido.objects.filter(procesado=False).count()
pnr_compras = ProductoNoReconocido.objects.filter(origen="compra").count()
pnr_ventas = ProductoNoReconocido.objects.filter(origen="venta").count()

print(f"Total PNR: {total_pnr}")
print(f"  - Procesados: {pnr_procesados}")
print(f"  - Pendientes: {pnr_pendientes}")
print(f"  - De compras: {pnr_compras}")
print(f"  - De ventas: {pnr_ventas}")

# Verificar PNR huérfanos (sin factura/compra asociada)
print("\n=== PNR HUERFANOS (sin factura/compra asociada) ===")

pnr_con_uuid = ProductoNoReconocido.objects.exclude(uuid_factura__isnull=True).exclude(uuid_factura='')
huerfanos_compra = 0
huerfanos_venta = 0

for pnr in pnr_con_uuid:
    if pnr.origen == "compra":
        # Buscar en Compra
        existe = Compra.objects.filter(uuid=pnr.uuid_factura).exists() or \
                 Compra.objects.filter(uuid_sat=pnr.uuid_factura).exists()
        if not existe:
            huerfanos_compra += 1
    elif pnr.origen == "venta":
        # Buscar en Factura
        existe = Factura.objects.filter(uuid_factura=pnr.uuid_factura).exists()
        if not existe:
            huerfanos_venta += 1

print(f"PNR de compras sin Compra asociada: {huerfanos_compra}")
print(f"PNR de ventas sin Factura asociada: {huerfanos_venta}")

# PNR procesados que podrían limpiarse
print("\n=== PNR PROCESADOS (pueden limpiarse) ===")
pnr_limpiables = ProductoNoReconocido.objects.filter(
    procesado=True,
    movimiento_generado=True
)
print(f"PNR procesados y con movimiento generado: {pnr_limpiables.count()}")

# Mostrar algunos ejemplos
if pnr_limpiables.exists():
    print("\nEjemplos:")
    for pnr in pnr_limpiables[:5]:
        print(f"  - ID {pnr.id}: {pnr.nombre_detectado} (origen: {pnr.origen}, producto: {pnr.producto_id})")

print("\n=== RECOMENDACIONES ===")
if huerfanos_compra > 0 or huerfanos_venta > 0:
    print(f"[!] Hay {huerfanos_compra + huerfanos_venta} PNR huerfanos que deben eliminarse")
if pnr_limpiables.count() > 0:
    print(f"[i] Hay {pnr_limpiables.count()} PNR procesados que pueden limpiarse automaticamente")
