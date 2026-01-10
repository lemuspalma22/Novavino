"""
Extraer texto raw del PDF para debugging
"""
from compras.extractors.pdf_reader import extract_text_from_pdf

pdf_path = "LEPR970522CD0_Factura_1127_E9DA14FE-E047-465F-A7B0-314647B8D87C.pdf"

print("Extrayendo texto del PDF...")
texto = extract_text_from_pdf(pdf_path)

# Guardar a archivo
with open("factura_1127_texto.txt", "w", encoding="utf-8") as f:
    f.write(texto)

print(f"Texto guardado en: factura_1127_texto.txt")
print(f"Total de caracteres: {len(texto)}")
print(f"Total de líneas: {texto.count(chr(10))}")

# Mostrar primeras 100 líneas
lineas = texto.split('\n')
print(f"\nPrimeras 50 lineas:")
print("="*80)
for i, linea in enumerate(lineas[:50], 1):
    print(f"{i:3}. {linea}")
print("="*80)

# Buscar sección CONCEPTOS
print("\nBuscando seccion CONCEPTOS...")
for i, linea in enumerate(lineas):
    if "CONCEPTOS" in linea:
        print(f"Encontrada en linea {i+1}")
        print(f"\nLineas {i} a {i+30}:")
        for j in range(i, min(i+30, len(lineas))):
            print(f"{j:3}. {lineas[j]}")
        break
