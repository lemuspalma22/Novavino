import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra

compra = Compra.objects.filter(folio='2334').first()
print(f"\nCompra: {compra.folio}")
print(f"Requiere revision manual: {compra.requiere_revision_manual}")
print(f"Estado revision: {compra.estado_revision}")

if compra.requiere_revision_manual:
    print(f"\n[!] CORRECTO - Factura marcada para revision")
    print(f"     Motivo: Contiene productos con IEPS 30% (licor)")
else:
    print(f"\n[X] ERROR - Factura NO marcada (deberia estarlo)")
