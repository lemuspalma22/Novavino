import re
from compras.extractors.pdf_reader import extract_text_from_pdf

text = extract_text_from_pdf("SVI180726AHAFS2334.pdf")

# Buscar el patrón (los IEPS aparecen en orden 3→2→1 en el PDF)
patron_tabla = r"I\.E\.P\.S\.\s*3\s+53%.*?I\.E\.P\.S\.\s*2\s+30%.*?I\.E\.P\.S\.\s*1\s+26\.5%.*?Descuento\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})"
match = re.search(patron_tabla, text, re.DOTALL | re.IGNORECASE)

if match:
    print("MATCH encontrado!")
    print(f"Grupo 1: {match.group(1)}")
    print(f"Grupo 2: {match.group(2)}")
    print(f"Grupo 3: {match.group(3)}")
    print(f"\nTexto completo matched:")
    print(match.group(0)[:200])
else:
    print("NO match")
    # Buscar partes individuales
    print("\nBuscando partes:")
    if re.search(r"I\.E\.P\.S\.\s*1\s+26\.5%", text, re.IGNORECASE):
        print("  - Encontrado IEPS 1")
    if re.search(r"I\.E\.P\.S\.\s*2\s+30%", text, re.IGNORECASE):
        print("  - Encontrado IEPS 2")
    if re.search(r"I\.E\.P\.S\.\s*3\s+53%", text, re.IGNORECASE):
        print("  - Encontrado IEPS 3")
    if re.search(r"Descuento", text, re.IGNORECASE):
        print("  - Encontrado Descuento")
