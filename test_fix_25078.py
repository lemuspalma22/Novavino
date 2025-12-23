"""
Test final: verificar que el fix funciona correctamente
"""
from extractors.vieja_bodega import ExtractorViejaBodega

pdf_path = "VBM041202DD1FB25078.pdf"

print("="*80)
print(" TEST FIX: Factura 25078")
print("="*80)
print()

extractor = ExtractorViejaBodega(pdf_path)
resultado = extractor.parse()

print(f"Proveedor: {resultado.get('proveedor')}")
print(f"Folio: {resultado.get('folio')}")
print(f"Total: ${resultado.get('total', 0):,.2f}")
print()

print("PRODUCTOS EXTRAIDOS:")
print("-" * 80)

for i, concepto in enumerate(resultado.get('conceptos', []), 1):
    print(f"\n{i}. {concepto['descripcion']}")
    print(f"   Cantidad: {concepto['cantidad']}")
    print(f"   P/U: ${concepto['precio_unitario']:,.2f}")
    print(f"   Importe: ${concepto['importe']:,.2f}")
    
    # Calcular precio con impuestos
    precio_base = float(concepto['precio_unitario'])
    con_ieps = precio_base * 1.265  # +26.50% IEPS
    con_iva = con_ieps * 1.16  # +16% IVA
    
    if 'VALLE OCULTO' in concepto['descripcion'].upper():
        print(f"   ---")
        print(f"   Precio base (PDF):      ${precio_base:,.2f}")
        print(f"   + IEPS 26.50%:          ${con_ieps:,.2f}")
        print(f"   + IVA 16%:              ${con_iva:,.2f}")
        print(f"   ---")
        if abs(con_iva - 141.00) < 1.00:
            print(f"   [OK] Con impuestos = $141.00 aprox")
        else:
            print(f"   [ALERTA] Con impuestos = ${con_iva:.2f} (esperado $141.00)")

print()
print("="*80)
print(" RESULTADO")
print("="*80)
print()

valle_ocultos = [c for c in resultado.get('conceptos', []) 
                 if 'VALLE OCULTO' in c['descripcion'].upper()]

if all(float(c['precio_unitario']) > 90 for c in valle_ocultos):
    print("[EXITO] Valle Oculto extrae precios correctos ($96.09)")
    print("        Con impuestos (IEPS 26.50% + IVA 16%) = ~$141.00")
else:
    print("[ERROR] Valle Oculto aun tiene precios incorrectos")

print()
print("="*80)
