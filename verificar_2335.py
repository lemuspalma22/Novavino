"""Verificar por qué la factura 2335 no detectó IEPS 2 (30%)"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra
from factura_parser import extract_invoice_data

print("\n" + "="*70)
print("VERIFICAR FACTURA 2335 - IEPS 2 (30%) NO DETECTADO")
print("="*70)

# 1. Verificar extracción
print("\n[1/3] Extrayendo datos del PDF...")
try:
    datos = extract_invoice_data("SVI180726AHAFS2335.pdf")
    print(f"   Folio: {datos.get('folio')}")
    print(f"   Total: ${datos.get('total')}")
    print(f"   IEPS 1 (26.5%): ${datos.get('ieps_1_importe', 'NO EXTRAIDO')}")
    print(f"   IEPS 2 (30%):   ${datos.get('ieps_2_importe', 'NO EXTRAIDO')}")
    print(f"   IEPS 3 (53%):   ${datos.get('ieps_3_importe', 'NO EXTRAIDO')}")
    
    if datos.get('ieps_2_importe', 0) > 0:
        print(f"\n   [OK] IEPS 2 SI se extrajo: ${datos.get('ieps_2_importe')}")
    else:
        print(f"\n   [ERROR] IEPS 2 NO se extrajo o es cero")
except Exception as e:
    print(f"   [ERROR] No se pudo extraer: {e}")
    datos = None

# 2. Verificar estado en BD
print("\n[2/3] Verificando estado en BD...")
compra = Compra.objects.filter(folio='2335').first()
if compra:
    print(f"   Compra existe: ID {compra.id}")
    print(f"   Requiere revision: {compra.requiere_revision_manual}")
    print(f"   Estado: {compra.estado_revision}")
    
    if compra.requiere_revision_manual:
        print(f"\n   [OK] Compra SI marcada para revision")
    else:
        print(f"\n   [ERROR] Compra NO marcada (deberia estarlo)")
else:
    print(f"   [ERROR] Compra 2335 no existe en BD")

# 3. Verificar lógica de validación
print("\n[3/3] Verificando logica de validacion...")
if datos:
    ieps_2 = datos.get('ieps_2_importe', 0)
    ieps_3 = datos.get('ieps_3_importe', 0)
    
    print(f"   IEPS 2 extraido: ${ieps_2}")
    print(f"   IEPS 3 extraido: ${ieps_3}")
    
    if ieps_2 > 0 or ieps_3 > 0:
        print(f"\n   [ESPERADO] Deberia marcar para revision")
        print(f"   Motivo: contiene_licor_ieps_{'30pct' if ieps_2 > 0 else '53pct'}")
    else:
        print(f"\n   [OK] No tiene IEPS especial, no marca")

print("\n" + "="*70)
