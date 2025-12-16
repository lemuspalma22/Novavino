"""Test: Verificar si el extractor mejorado detecta TRES RIBERAS"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.extractors.pdf_reader import extract_text_from_pdf
from extractors.secretos_delavid import ExtractorSecretosDeLaVid

print("\n" + "="*70)
print("TEST: EXTRACTOR MEJORADO - FACTURA 2445")
print("="*70)

pdf_path = "SVI180726AHAFS2445.pdf"

try:
    # Extraer texto
    text = extract_text_from_pdf(pdf_path)
    
    # Usar extractor
    extractor = ExtractorSecretosDeLaVid(text, pdf_path)
    datos = extractor.parse()
    
    print(f"\nFactura: {datos.get('folio')}")
    print(f"Total: ${datos.get('total'):,.2f}")
    print(f"UUID: {datos.get('uuid')}")
    
    productos = datos.get('productos', [])
    print(f"\nProductos detectados: {len(productos)}")
    print("-"*70)
    
    suma_total = 0
    tres_riberas_encontrado = False
    
    for i, prod in enumerate(productos, 1):
        nombre = prod.get('nombre_detectado', 'SIN NOMBRE')
        cantidad = prod.get('cantidad', 0)
        precio = prod.get('precio_unitario', 0)
        importe = cantidad * precio
        suma_total += importe
        
        print(f"\n{i}. {nombre}")
        print(f"   Cantidad: {cantidad}")
        print(f"   P/U: ${precio:,.2f}")
        print(f"   Importe: ${importe:,.2f}")
        
        # Verificar si es TRES RIBERAS
        if "TRES RIBERAS" in nombre.upper() or "RIBERA" in nombre.upper():
            tres_riberas_encontrado = True
            print(f"   [OK] TRES RIBERAS DETECTADO!")
    
    print("\n" + "="*70)
    print(f"SUMA CALCULADA: ${suma_total:,.2f}")
    print(f"TOTAL FACTURA:  ${datos.get('total'):,.2f}")
    diferencia = abs(datos.get('total') - suma_total)
    diferencia_pct = (diferencia / datos.get('total') * 100) if datos.get('total') else 0
    print(f"DIFERENCIA:     ${diferencia:,.2f} ({diferencia_pct:.2f}%)")
    
    print("\n" + "="*70)
    print("RESULTADO:")
    print("-"*70)
    
    if tres_riberas_encontrado:
        print("[OK] TRES RIBERAS fue detectado correctamente")
    else:
        print("[ERROR] TRES RIBERAS NO fue detectado")
    
    if len(productos) >= 4:
        print(f"[OK] Se detectaron {len(productos)} productos (esperados: 4)")
    else:
        print(f"[ERROR] Solo se detectaron {len(productos)} productos (esperados: 4)")
    
    if diferencia_pct < 1:
        print(f"[OK] Diferencia < 1% - Extraccion correcta")
    else:
        print(f"[ALERTA] Diferencia {diferencia_pct:.2f}% - Revisar")
    
    print("="*70 + "\n")
    
except FileNotFoundError:
    print(f"\n[ERROR] PDF no encontrado: {pdf_path}")
    print("="*70 + "\n")
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    print("="*70 + "\n")
