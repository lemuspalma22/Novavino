"""Limpiar compra 2334 para re-test"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra
from inventario.models import ProductoNoReconocido

# Eliminar compra
compras = Compra.objects.filter(folio='2334')
if compras.exists():
    compras.delete()
    print("Compra 2334 eliminada")
else:
    print("Compra 2334 no existe")

# Limpiar PNRs
uuid = '92C70A32-EC9F-4924-B8BE-309C3E171515'
pnrs = ProductoNoReconocido.objects.filter(uuid_factura=uuid)
if pnrs.exists():
    count = pnrs.count()
    pnrs.delete()
    print(f"Eliminados {count} PNRs")

print("\nListo para re-procesar")
