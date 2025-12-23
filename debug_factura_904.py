"""
Debug para revisar extracción de VBM041202DD1FB24904
"""
from extractors.vieja_bodega import ExtractorViejaBodega
import json

result = ExtractorViejaBodega(None, 'VBM041202DD1FB24904.pdf').parse()

print("=== DATOS EXTRAIDOS ===")
print(f"Proveedor: {result.get('proveedor')}")
print(f"Folio: {result.get('folio')}")
print(f"UUID: {result.get('uuid', 'N/A')[:20]}...")
print(f"Subtotal: {result.get('subtotal')}")
print(f"IVA: {result.get('iva')}")
print(f"Total: {result.get('total')}")

conceptos = result.get('conceptos', [])
print(f"\n=== CONCEPTOS ({len(conceptos)}) ===")
for i, c in enumerate(conceptos, 1):
    print(f"\n{i}. {c['descripcion']}")
    print(f"   Cantidad: {c['cantidad']}")
    print(f"   P.U.: ${c['precio_unitario']}")
    print(f"   Importe: ${c['importe']}")

# Buscar específicamente el producto mencionado
print("\n=== BUSQUEDA: BACALAUH ===")
for c in conceptos:
    if 'BACALAUH' in c['descripcion'].upper() or 'SAUVIGNON' in c['descripcion'].upper():
        print(f"ENCONTRADO: {c['descripcion']}")
        print(f"  Cantidad extraída: {c['cantidad']}")
        print(f"  P.U.: ${c['precio_unitario']}")
