"""
Extraer texto crudo del PDF para análisis
"""
from pdfminer.high_level import extract_text
import re

pdf_path = "VBM041202DD1FB25078.pdf"

text = extract_text(pdf_path) or ""
raw_lines = text.splitlines()
lines = [re.sub(r"\s+", " ", l).strip() for l in raw_lines]
lines = [l for l in lines if l]

print("="*80)
print(" TEXTO COMPLETO DEL PDF (lineas no vacias)")
print("="*80)
print()

for i, line in enumerate(lines, 1):
    print(f"{i:3d}: {line}")

print()
print("="*80)
print(" BUSCAR '141' EN EL TEXTO")
print("="*80)
print()

for i, line in enumerate(lines, 1):
    if '141' in line:
        print(f"Linea {i}: {line}")

print()
print("="*80)
print(" BUSCAR 'VALLE OCULTO' EN EL TEXTO")
print("="*80)
print()

for i, line in enumerate(lines, 1):
    if 'VALLE OCULTO' in line.upper() or 'MERLOT' in line.upper() or 'MALBEC' in line.upper():
        # Mostrar contexto (3 lineas antes y despues)
        start = max(0, i-3)
        end = min(len(lines), i+3)
        print(f"\nContexto de linea {i}:")
        print("-" * 40)
        for j in range(start, end):
            marker = ">>>" if j == i-1 else "   "
            print(f"{marker} {j+1:3d}: {lines[j]}")
