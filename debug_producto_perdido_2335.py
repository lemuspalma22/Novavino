"""Debug: Encontrar el producto perdido en 2335"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.extractors.pdf_reader import extract_text_from_pdf
import re

print("\n" + "="*70)
print("DEBUG: PRODUCTO PERDIDO EN 2335")
print("="*70)

pdf_path = "SVI180726AHAFS2335.pdf"
text = extract_text_from_pdf(pdf_path)

# Buscar la sección de productos
match_seccion = re.search(r"FACTURA.*?\n(.*?)\nTotal", text, re.DOTALL | re.IGNORECASE)

if match_seccion:
    seccion_productos = match_seccion.group(1)
    
    # Buscar todos los bloques que terminan con "pz"
    bloques_patron = r"(\d+\.\d{3,4})\s+.*?(pz|PZ)\s+\d{8}"
    
    print("\nBloques encontrados en el PDF:")
    print("-"*70)
    
    for i, bloque_match in enumerate(re.finditer(bloques_patron, seccion_productos, re.DOTALL | re.IGNORECASE), 1):
        bloque_texto = bloque_match.group(0)
        
        print(f"\n[BLOQUE {i}]")
        print("="*70)
        print(bloque_texto[:300])  # Primeros 300 chars
        print("...")
        
        # Intentar extraer cantidad
        cantidad_match = re.search(r"(\d+\.\d{3,4})", bloque_texto)
        if cantidad_match:
            print(f"\nCantidad: {cantidad_match.group(1)}")
        
        # Intentar extraer descripciones
        lineas = bloque_texto.split('\n')
        print(f"\nLineas del bloque:")
        for j, linea in enumerate(lineas[:10], 1):
            if linea.strip():
                print(f"  {j}: {linea.strip()}")
    
    print("\n" + "="*70)
    print("ANALISIS:")
    print("-"*70)
    
    # Contar bloques
    total_bloques = len(list(re.finditer(bloques_patron, seccion_productos, re.DOTALL | re.IGNORECASE)))
    print(f"\nTotal de bloques encontrados: {total_bloques}")
    print(f"Productos detectados por extractor: 3")
    print(f"Diferencia: {total_bloques - 3} producto(s) perdido(s)")
    
    print("\n" + "="*70)

else:
    print("\n[ERROR] No se encontro seccion de productos")
