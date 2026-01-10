"""Limpiar compras de prueba y re-procesar"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra
from inventario.models import ProductoNoReconocido

# Eliminar compras de prueba
folios = ['2326', '2334']
for folio in folios:
    compras = Compra.objects.filter(folio=folio)
    count = compras.count()
    if count > 0:
        compras.delete()
        print(f"Eliminada compra {folio} ({count} registros)")
    else:
        print(f"Compra {folio} no existe")

# Limpiar PNRs de estas facturas
uuids = [
    '4CE504E1-52E2-4A6D-A6CF-B002D80529D2',  # 2326
    '92C70A32-EC9F-4924-B8BE-309C3E171515'   # 2334
]
for uuid in uuids:
    pnrs = ProductoNoReconocido.objects.filter(uuid_factura=uuid)
    count = pnrs.count()
    if count > 0:
        pnrs.delete()
        print(f"Eliminados {count} PNRs del UUID {uuid[:8]}...")

print("\nListo para re-procesar facturas")
