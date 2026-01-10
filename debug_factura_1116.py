"""
Debug factura de venta 1116
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.extractors.novavino import extraer_factura_novavino
from compras.extractors.pdf_reader import extract_text_from_pdf

pdf_path = "LEPR970522CD0_Factura_1116_9F5DA3A8-E3E2-489E-B5D3-5B1C49437E7F.pdf"

print("=== EXTRACCION FACTURA 1116 ===\n")

try:
    texto = extract_text_from_pdf(pdf_path)
    datos = extraer_factura_novavino(texto)
    
    print(f"Folio: {datos.get('folio')}")
    print(f"Cliente: {datos.get('cliente')}")
    print(f"Fecha: {datos.get('fecha')}")
    print(f"Total: {datos.get('total')}")
    print(f"\nProductos extraidos: {len(datos.get('productos', []))}")
    
    suma_productos = 0
    for i, prod in enumerate(datos.get('productos', []), 1):
        nombre = prod.get('nombre') or prod.get('producto')
        cantidad = prod.get('cantidad', 0)
        precio_u = prod.get('precio_unitario', 0)
        importe = cantidad * precio_u
        suma_productos += importe
        
        print(f"\n{i}. {nombre}")
        print(f"   Cantidad: {cantidad}")
        print(f"   Precio unitario: ${precio_u:,.2f}")
        print(f"   Importe: ${importe:,.2f}")
    
    print(f"\n=== RESUMEN ===")
    print(f"Suma productos: ${suma_productos:,.2f}")
    print(f"Total factura: ${datos.get('total'):,.2f}")
    print(f"Diferencia: ${abs(datos.get('total') - suma_productos):,.2f}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
