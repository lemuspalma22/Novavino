"""
Analizar extracción de total en factura 1106
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.extractors.novavino import extraer_factura_novavino
from compras.extractors.pdf_reader import extract_text_from_pdf
from extractors.utils_extractores import extraer_total
from decimal import Decimal

pdf_path = "LEPR970522CD0_Factura_1106_E234D345-D60D-4576-9301-2EC0B1405A53.pdf"

print("=== ANALISIS FACTURA 1106 ===\n")

# Extraer texto completo
texto = extract_text_from_pdf(pdf_path)

# Usar el extractor principal
datos = extraer_factura_novavino(texto)

print(f"Folio extraído: {datos.get('folio')}")
print(f"Total extraído por extractor: {datos.get('total')}")

# Probar la función extraer_total directamente
total_directo = extraer_total(texto)
print(f"Total extraído por utils: {total_directo}")

# Calcular suma de productos
suma_productos = Decimal("0")
print(f"\nProductos extraídos: {len(datos.get('productos', []))}")
for i, prod in enumerate(datos.get('productos', []), 1):
    nombre = prod.get('nombre')
    cantidad = prod.get('cantidad', 0)
    precio = prod.get('precio_unitario', 0)
    importe = Decimal(str(cantidad)) * Decimal(str(precio))
    suma_productos += importe
    print(f"{i}. {cantidad} × ${precio} = ${importe}")

print(f"\n=== COMPARACION ===")
print(f"Total PDF (esperado):     $14,651.08")
print(f"Total extraído:           ${datos.get('total'):,.2f}")
print(f"Suma de productos:        ${suma_productos:,.2f}")
print(f"Diferencia:               ${abs(Decimal('14651.08') - datos.get('total')):,.2f}")

# Buscar la palabra TOTAL en el texto para ver qué hay
print(f"\n=== BUSCAR 'TOTAL' EN EL TEXTO ===")
lines = texto.split('\n')
for i, line in enumerate(lines):
    if 'TOTAL' in line.upper():
        # Mostrar contexto (línea anterior, actual, siguiente)
        start = max(0, i-1)
        end = min(len(lines), i+3)
        for j in range(start, end):
            prefix = ">>>" if j == i else "   "
            print(f"{prefix} Línea {j}: {lines[j][:100]}")
        print()
