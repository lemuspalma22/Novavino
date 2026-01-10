"""
Verificar qué se guardó en la BD para la factura 1106
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura, DetalleFactura
from decimal import Decimal

print("=== FACTURA 1106 EN BASE DE DATOS ===\n")

try:
    factura = Factura.objects.get(folio_factura="1106")
    
    print(f"Folio: {factura.folio_factura}")
    print(f"Cliente: {factura.cliente}")
    print(f"Total en BD: ${factura.total:,.2f}")
    print(f"\nDetalles:")
    
    suma_detalles = Decimal("0")
    for det in factura.detalles.all():
        subtotal = det.cantidad * det.precio_unitario
        suma_detalles += subtotal
        print(f"  - {det.cantidad} × {det.producto.nombre} @ ${det.precio_unitario:,.2f} = ${subtotal:,.2f}")
    
    print(f"\n=== COMPARACION ===")
    print(f"Total guardado en factura:  ${factura.total:,.2f}")
    print(f"Suma de detalles:           ${suma_detalles:,.2f}")
    print(f"Diferencia:                 ${abs(factura.total - suma_detalles):,.2f}")
    
    print(f"\n=== ORIGEN DEL PROBLEMA ===")
    if abs(factura.total - suma_detalles) > Decimal("0.01"):
        print(f"[!] HAY DISCREPANCIA")
        print(f"    El total guardado en la factura NO coincide con la suma de detalles")
        if abs(Decimal("14651.08") - factura.total) < Decimal("0.01"):
            print(f"    El total de la BD SI coincide con el PDF (${14651.08})")
            print(f"    Pero los detalles suman ${suma_detalles}")
        else:
            print(f"    El total de la BD NO coincide con el PDF (${14651.08})")
    else:
        print(f"[OK] Total y suma de detalles coinciden")
    
except Factura.DoesNotExist:
    print("La factura 1106 no existe en la base de datos")
