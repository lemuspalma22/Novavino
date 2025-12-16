"""Verificar que el extractor de SV devuelve datos para validacion de totales"""
import os
import sys
from decimal import Decimal

# Setup Django PRIMERO
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

# Agregar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from factura_parser import extract_invoice_data

print("\n" + "="*70)
print("TEST: VALIDACION DE TOTALES - SECRETOS DE LA VID")
print("="*70)

# Test con factura 2335
print("\n[TEST] Extrayendo factura 2335...")
try:
    datos = extract_invoice_data("SVI180726AHAFS2335.pdf")
    
    print(f"\n1. DATOS EXTRAIDOS:")
    print(f"   Folio: {datos.get('folio')}")
    print(f"   Subtotal: ${datos.get('subtotal', 'NO EXTRAIDO')}")
    print(f"   IVA: ${datos.get('iva', 'NO EXTRAIDO')}")
    print(f"   Total: ${datos.get('total', 'NO EXTRAIDO')}")
    print(f"   Productos: {len(datos.get('productos', []))}")
    
    # Calcular suma de productos
    print(f"\n2. PRODUCTOS:")
    suma_productos = Decimal("0")
    for p in datos.get('productos', []):
        cant = Decimal(str(p.get('cantidad', 0)))
        pu = Decimal(str(p.get('precio_unitario', 0)))
        importe = cant * pu
        suma_productos += importe
        print(f"   - {p.get('nombre', 'SIN NOMBRE')[:40]:40} | Cant: {cant:6} | P/U: ${pu:8.2f} | Imp: ${importe:10.2f}")
    
    print(f"\n3. VALIDACION:")
    print(f"   Suma productos: ${suma_productos:,.2f}")
    
    subtotal = Decimal(str(datos.get('subtotal', 0)))
    iva = Decimal(str(datos.get('iva', 0)))
    total = Decimal(str(datos.get('total', 0)))
    
    if subtotal:
        print(f"   Subtotal extraido: ${subtotal:,.2f}")
        diff_subtotal = abs(suma_productos - subtotal)
        diff_pct = (diff_subtotal / subtotal * 100) if subtotal else Decimal("0")
        print(f"   Diferencia: ${diff_subtotal:,.2f} ({diff_pct:.2f}%)")
        
        if diff_pct > 2:
            print(f"   [ERROR] Diferencia > 2% - MARCARIA PARA REVISION")
        else:
            print(f"   [OK] Diferencia < 2%")
    else:
        print(f"   [ERROR] No se extrajo subtotal")
    
    if subtotal and total:
        total_calc = subtotal + iva
        diff_total = abs(total - total_calc)
        diff_pct_total = (diff_total / total * 100) if total else Decimal("0")
        print(f"\n   Total calculado (subtotal+IVA): ${total_calc:,.2f}")
        print(f"   Total extraido: ${total:,.2f}")
        print(f"   Diferencia: ${diff_total:,.2f} ({diff_pct_total:.2f}%)")
        
        if diff_pct_total > 2:
            print(f"   [ERROR] Diferencia > 2% - MARCARIA PARA REVISION")
        else:
            print(f"   [OK] Diferencia < 2%")
    
    # Ahora probar la validacion automatica
    print(f"\n4. VALIDACION AUTOMATICA:")
    from compras.utils.validation import evaluar_totales_factura
    
    motivos = evaluar_totales_factura(datos)
    if motivos:
        print(f"   [ALERTA] Motivos detectados:")
        for m in motivos:
            print(f"      - {m}")
    else:
        print(f"   [OK] Sin problemas detectados")
    
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70 + "\n")
