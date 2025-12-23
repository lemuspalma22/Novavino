"""
Debug de la extracción de la factura 25078 de Vieja Bodega
"""
import os
os.environ['NV_DEBUG'] = '1'  # Activar modo DEBUG

from extractors.vieja_bodega import ExtractorViejaBodega

print("="*80)
print(" DEBUG: Factura 25078 - Vieja Bodega")
print("="*80)
print()

pdf_path = "VBM041202DD1FB25078.pdf"

if not os.path.exists(pdf_path):
    print(f"ERROR: No se encuentra el archivo {pdf_path}")
    exit(1)

print(f"Procesando: {pdf_path}")
print("="*80)
print()

extractor = ExtractorViejaBodega(pdf_path)
resultado = extractor.parse()

print()
print("="*80)
print(" RESULTADO DE EXTRACCIÓN")
print("="*80)
print()

print(f"Proveedor: {resultado.get('proveedor')}")
print(f"Folio: {resultado.get('folio')}")
print(f"Fecha: {resultado.get('fecha_emision')}")
print(f"Subtotal: ${resultado.get('subtotal', 0):,.2f}")
print(f"IVA: ${resultado.get('iva', 0):,.2f}")
print(f"Total: ${resultado.get('total', 0):,.2f}")
print()

print("CONCEPTOS:")
print("-" * 80)
for i, concepto in enumerate(resultado.get('conceptos', []), 1):
    print(f"\n{i}. {concepto['descripcion']}")
    print(f"   Cantidad: {concepto['cantidad']}")
    print(f"   P/U: ${concepto['precio_unitario']:,.2f}")
    print(f"   Importe: ${concepto['importe']:,.2f}")
    print(f"   Verificación: {concepto['cantidad']} × ${concepto['precio_unitario']:,.2f} = ${float(concepto['cantidad']) * float(concepto['precio_unitario']):,.2f}")

print()
print("="*80)
print(" ANÁLISIS")
print("="*80)
print()

# Buscar los productos problemáticos
problemas = []
for concepto in resultado.get('conceptos', []):
    desc = concepto['descripcion'].upper()
    if 'VALLE OCULTO' in desc and ('MERLOT' in desc or 'MALBEC' in desc):
        precio = float(concepto['precio_unitario'])
        if precio < 100:  # Precio sospechoso
            problemas.append(concepto)
            print(f"⚠️ PROBLEMA DETECTADO:")
            print(f"   {concepto['descripcion']}")
            print(f"   Precio extraído: ${precio:,.2f}")
            print(f"   Precio esperado: $141.00")
            print(f"   Diferencia: ${141.00 - precio:,.2f}")
            print()

if not problemas:
    print("No se detectaron problemas con Valle Oculto")
else:
    print(f"\nTotal de productos con precios incorrectos: {len(problemas)}")

print()
print("="*80)
