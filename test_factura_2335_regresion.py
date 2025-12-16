"""Test específico: Verificar si 2335 se rompió"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.extractors.pdf_reader import extract_text_from_pdf
from extractors.secretos_delavid import ExtractorSecretosDeLaVid

print("\n" + "="*70)
print("TEST CRITICO: FACTURA 2335 (IEPS 30%)")
print("="*70)

pdf_path = "SVI180726AHAFS2335.pdf"

if not os.path.exists(pdf_path):
    print(f"\n[ERROR] PDF no encontrado: {pdf_path}")
    exit(1)

try:
    # Extraer con el extractor mejorado
    text = extract_text_from_pdf(pdf_path)
    extractor = ExtractorSecretosDeLaVid(text, pdf_path)
    datos = extractor.parse()
    
    print(f"\nFactura: {datos.get('folio')}")
    print(f"Total: ${datos.get('total'):,.2f}")
    
    productos = datos.get('productos', [])
    print(f"\nProductos detectados: {len(productos)}")
    print("-"*70)
    
    suma = 0
    for i, prod in enumerate(productos, 1):
        nombre = prod.get('nombre_detectado', 'SIN NOMBRE')
        cantidad = prod.get('cantidad', 0)
        precio = prod.get('precio_unitario', 0)
        importe = cantidad * precio
        suma += importe
        
        print(f"\n{i}. {nombre}")
        print(f"   Cantidad: {cantidad}")
        print(f"   P/U: ${precio:,.2f}")
        print(f"   Importe: ${importe:,.2f}")
        
        # Verificar limpieza
        import re
        if re.search(r'[A-Z]{3,}\d{2}\.\d{2}$', nombre):
            print(f"   [ALERTA] Nombre tiene basura!")
    
    print(f"\n{'='*70}")
    print(f"Suma calculada: ${suma:,.2f}")
    print(f"Total factura:  ${datos.get('total'):,.2f}")
    diferencia = abs(datos.get('total') - suma)
    diferencia_pct = (diferencia / datos.get('total') * 100) if datos.get('total') else 0
    print(f"Diferencia:     ${diferencia:,.2f} ({diferencia_pct:.2f}%)")
    
    print(f"\n{'='*70}")
    print("DIAGNOSTICO:")
    print("-"*70)
    
    if len(productos) >= 4:
        print(f"[OK] Productos detectados: {len(productos)} >= 4")
    else:
        print(f"[ERROR] Solo {len(productos)} productos detectados (esperado: 4)")
        print("\nProductos esperados:")
        print("  1. Leone de Castris")
        print("  2. Rocca")
        print("  3. Prosecco (IEPS 26.5%)")
        print("  4. Vino con IEPS 30%")
    
    if diferencia_pct < 0.1:
        print(f"[OK] Diferencia < 0.1% - Extraccion correcta")
    else:
        print(f"[ALERTA] Diferencia {diferencia_pct:.2f}%")
    
    # Verificar nombres limpios
    nombres_sucios = []
    for prod in productos:
        nombre = prod.get('nombre_detectado', '')
        import re
        if re.search(r'[A-Z]{3,}\d{2}\.\d{2}$', nombre):
            nombres_sucios.append(nombre)
    
    if not nombres_sucios:
        print(f"[OK] Todos los nombres estan limpios")
    else:
        print(f"[ERROR] {len(nombres_sucios)} nombres con basura:")
        for nombre in nombres_sucios:
            print(f"  - {nombre}")
    
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    print("="*70 + "\n")
