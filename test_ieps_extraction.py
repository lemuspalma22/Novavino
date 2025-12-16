"""Test para verificar extracción de IEPS"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.extractors.pdf_reader import extract_text_from_pdf
from extractors.secretos_delavid import ExtractorSecretosDeLaVid

import sys
pdf_path = sys.argv[1] if len(sys.argv) > 1 else "SVI180726AHAFS2334.pdf"

print(f"\nProbando extracción de IEPS en: {pdf_path}\n")

text = extract_text_from_pdf(pdf_path)
extractor = ExtractorSecretosDeLaVid(text, pdf_path)
datos = extractor.parse()

print(f"IEPS 1 (26.5%): ${datos.get('ieps_1_importe', 0):.2f}")
print(f"IEPS 2 (30%):   ${datos.get('ieps_2_importe', 0):.2f}")
print(f"IEPS 3 (53%):   ${datos.get('ieps_3_importe', 0):.2f}")

print(f"\n¿Contiene licores (IEPS 2 o 3 > 0)? ", end="")
if datos.get('ieps_2_importe', 0) > 0 or datos.get('ieps_3_importe', 0) > 0:
    print("SI - Requiere revision manual")
else:
    print("NO - Auto-validar")
