"""
Test detallado del extractor con la factura 1127
"""
import re
from decimal import Decimal
from compras.extractors.pdf_reader import extract_text_from_pdf

UNIT_RE = re.compile(r"^[A-Z0-9]{1,}(?:\s*-\s*[A-Z0-9]{1,})?$")

pdf_path = "LEPR970522CD0_Factura_1127_E9DA14FE-E047-465F-A7B0-314647B8D87C.pdf"
texto = extract_text_from_pdf(pdf_path)
lines = [ln.rstrip() for ln in texto.splitlines()]

print("="*80)
print("DEBUG EXTRACTOR - Factura 1127")
print("="*80)

# Buscar sección CONCEPTOS
i_start = None
for i, ln in enumerate(lines):
    if "CONCEPTOS" in ln:
        i_start = i
        break

if i_start is None:
    print("ERROR: No se encontró sección CONCEPTOS")
    exit()

print(f"\nSección CONCEPTOS encontrada en línea {i_start}")
print(f"\nProcesando líneas desde {i_start+1}...")
print("="*80)

i = i_start + 1
productos_encontrados = 0

while i < len(lines):
    ln = lines[i].strip()
    
    # Intentar detectar cantidad
    m_qty = re.match(r"^(\d+(?:\.\d+)?)$", ln)
    
    if m_qty:
        print(f"\n[OK] CANTIDAD DETECTADA en linea {i}: '{ln}'")
        print(f"  Valor: {m_qty.group(1)}")
        
        # Verificar siguiente línea (unidad)
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            print(f"  Siguiente linea ({i+1}): '{next_line}'")
            
            if UNIT_RE.match(next_line):
                print(f"  [OK] ES UNIDAD VALIDA")
                
                # Verificar nombre de producto
                if i + 2 < len(lines):
                    nombre_line = lines[i + 2].strip()
                    print(f"  Linea nombre ({i+2}): '{nombre_line}'")
                    
                    # Buscar más líneas
                    print(f"\n  Siguientes 10 líneas:")
                    for j in range(i+2, min(i+12, len(lines))):
                        print(f"    {j}: {lines[j]}")
                    
                productos_encontrados += 1
            else:
                print(f"  [X] NO ES UNIDAD (no coincide con UNIT_RE)")
                print(f"    Regex esperaba: ^[A-Z0-9]{{1,}}(?:\\s*-\\s*[A-Z0-9]{{1,}})?$")
        else:
            print(f"  [X] No hay siguiente linea")
    
    i += 1
    
    if i > i_start + 50:  # Limitar búsqueda
        break

print(f"\n{'='*80}")
print(f"Total productos detectados: {productos_encontrados}")
print(f"{'='*80}")
