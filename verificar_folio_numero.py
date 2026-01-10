# verificar_folio_numero.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura

# Ver las facturas recientes con sus folio_numero
facturas = Factura.objects.filter(
    folio_factura__in=['1159', '1160', '1157', '1158', '1156', '1150', 'VPG26-2']
).order_by('-folio_numero')

print("Folios y sus folio_numero:")
print(f"{'Folio':<15} {'folio_numero':<15} {'Tipo':<10}")
print("-" * 40)
for f in facturas:
    tipo = "VPG" if f.es_vpg else "Factura"
    print(f"{f.folio_factura:<15} {f.folio_numero:<15} {tipo:<10}")
