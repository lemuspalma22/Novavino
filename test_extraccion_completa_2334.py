"""Verificar que extract_invoice_data incluye los campos IEPS"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from factura_parser import extract_invoice_data

pdf_path = "SVI180726AHAFS2334.pdf"

print(f"\nExtrayendo datos de: {pdf_path}\n")

datos = extract_invoice_data(pdf_path)

print(f"Folio: {datos.get('folio')}")
print(f"Proveedor: {datos.get('proveedor')}")
print(f"Total: ${datos.get('total')}")
print(f"\nCampos IEPS:")
print(f"  ieps_1_importe: ${datos.get('ieps_1_importe', 'NO EXISTE')}")
print(f"  ieps_2_importe: ${datos.get('ieps_2_importe', 'NO EXISTE')}")
print(f"  ieps_3_importe: ${datos.get('ieps_3_importe', 'NO EXISTE')}")

if datos.get('ieps_3_importe', 0) > 0:
    print(f"\n[OK] IEPS 3 detectado: ${datos.get('ieps_3_importe')}")
    print(f"     Esta factura DEBE marcarse para revision")
else:
    print(f"\n[ERROR] IEPS 3 NO detectado o es cero")
