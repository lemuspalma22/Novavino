"""
Script para analizar la factura 1127 y ver exactamente qué productos detecta
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ventas.extractors.novavino import extract_venta_data

pdf_path = "LEPR970522CD0_Factura_1127_E9DA14FE-E047-465F-A7B0-314647B8D87C.pdf"

print("="*80)
print("ANÁLISIS DE FACTURA 1127")
print("="*80)

# Extraer datos
datos = extract_venta_data(pdf_path)

print(f"\nFOLIO: {datos.get('folio')}")
print(f"UUID: {datos.get('uuid')}")
print(f"CLIENTE: {datos.get('cliente')}")
print(f"TOTAL: ${datos.get('total', 0):,.2f}")
print(f"MÉTODO PAGO: {datos.get('metodo_pago')}")

productos = datos.get('productos', [])
print(f"\n{'='*80}")
print(f"PRODUCTOS DETECTADOS: {len(productos)}")
print(f"{'='*80}\n")

if len(productos) == 0:
    print("⚠️ NO SE DETECTARON PRODUCTOS")
    print("\nEsto puede significar:")
    print("  1. El extractor no pudo parsear el PDF")
    print("  2. El formato del PDF es diferente al esperado")
    print("  3. Los productos están en una sección no reconocida")
else:
    for idx, p in enumerate(productos, 1):
        nombre = p.get('nombre', '')
        cantidad = p.get('cantidad', 0)
        precio = p.get('precio_unitario', 0)
        importe = cantidad * precio
        
        print(f"{idx}. {nombre}")
        print(f"   Cantidad: {cantidad}")
        print(f"   Precio unitario: ${precio:,.2f}")
        print(f"   Importe: ${importe:,.2f}")
        print()

print("="*80)
print("\nAhora verifica si estos productos EXISTEN en la base de datos:")
print("  python manage.py shell")
print("  >>> from inventario.models import Producto")
print("  >>> from inventario.utils import encontrar_producto_unico")
print("  >>> encontrar_producto_unico('NOMBRE_DEL_PRODUCTO')")
print("="*80)
