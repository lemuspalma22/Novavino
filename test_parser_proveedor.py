"""Test para verificar que factura_parser identifica correctamente el proveedor"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from factura_parser import extract_invoice_data

pdf_path = "SVI180726AHAFS2326.pdf"

print(f"\nProbando identificación de proveedor en: {pdf_path}\n")

datos = extract_invoice_data(pdf_path)

proveedor = datos.get("proveedor")
if hasattr(proveedor, "nombre"):
    nombre_prov = proveedor.nombre
else:
    nombre_prov = str(proveedor)

print(f"Proveedor detectado: {nombre_prov}")
print(f"Folio: {datos.get('folio')}")
print(f"Total: ${datos.get('total')}")
print(f"Productos: {len(datos.get('productos', []))}")

if "secretos" in nombre_prov.lower() and "vid" in nombre_prov.lower():
    print("\n[OK] CORRECTO - Identificado como Secretos de la Vid")
elif "vieja" in nombre_prov.lower() and "bodega" in nombre_prov.lower():
    print("\n[ERROR] Identificado incorrectamente como Vieja Bodega")
else:
    print(f"\n[?] INESPERADO - Proveedor: {nombre_prov}")
