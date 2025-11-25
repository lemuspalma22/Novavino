import dotenv
dotenv.load_dotenv()
import os
import django
import re
from ventas.extractors.novavino import extraer_factura_novavino

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

from compras.extractors.pdf_reader import extract_text_from_pdf
from extractors.utils_extractores import (
    extraer_folio,
    extraer_uuid,
    extraer_fecha_emision,
    extraer_total,
)

# Cambia el nombre si pruebas otro archivo
pdf_path = "VBM041202DD1FB24554.pdf"

text = extract_text_from_pdf(pdf_path)

print("📄 Texto extraído del PDF:")
print("=" * 60)
print(text)
print("=" * 60)

# PRUEBAS DE EXTRACCIÓN
try:
    folio_match = re.search(r"Folio\s*:\s*(\d+)", text, re.IGNORECASE)
    if folio_match:
        folio = folio_match.group(1)
        print(f"✅ Folio encontrado (OLI Corp): {folio}")
    else:
        raise ValueError("Folio no detectado.")

except Exception as e:
    print(f"❌ Error al extraer folio: {e}")

try:
    uuid = extraer_uuid(text)
    print(f"✅ UUID encontrado: {uuid}")
except Exception as e:
    print(f"❌ Error al extraer UUID: {e}")

try:
    fecha = extraer_fecha_emision(text)
    print(f"✅ Fecha de emisión encontrada: {fecha}")
except Exception as e:
    print(f"❌ Error al extraer fecha de emisión: {e}")

try:
    total = extraer_total(text)
    print(f"✅ Total encontrado: {total}")
except Exception as e:
    print(f"❌ Error al extraer total: {e}")
