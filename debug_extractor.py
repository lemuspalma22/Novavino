#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from extractors.vieja_bodega import ExtractorViejaBodega
from decimal import Decimal

def debug_extractor():
    ext = ExtractorViejaBodega('VBM041202DD1FB24468.pdf')
    result = ext.parse()
    
    print("=== DEBUG EXTRACTOR ===")
    print(f"Folio: {result.get('folio', 'NO ENCONTRADO')}")
    print(f"UUID: {result.get('uuid', 'NO ENCONTRADO')}")
    print(f"Total: {result.get('total', 'NO ENCONTRADO')}")
    print(f"IVA: {result.get('iva', 'NO ENCONTRADO')}")
    print(f"Conceptos: {len(result.get('conceptos', []))}")
    
    total_calculado = Decimal('0')
    for i, c in enumerate(result.get('conceptos', [])):
        desc = c.get('descripcion', '')
        cant = c.get('cantidad', 0)
        pu = c.get('precio_unitario', 0)
        imp = c.get('importe', 0)
        total_calculado += imp
        
        print(f"\nProducto {i+1}:")
        print(f"  Descripción: {desc}")
        print(f"  Cantidad: {cant}")
        print(f"  Precio Unitario: {pu}")
        print(f"  Importe: {imp}")
    
    print(f"\nTotal calculado: {total_calculado}")
    print(f"Total real: {result.get('total', 0)}")
    print(f"Diferencia: {total_calculado - Decimal(str(result.get('total', 0)))}")

if __name__ == "__main__":
    debug_extractor()
