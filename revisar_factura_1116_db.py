"""
Revisar factura 1116 en la base de datos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura, DetalleFactura
from decimal import Decimal

print("=== FACTURA 1116 EN BASE DE DATOS ===\n")

try:
    factura = Factura.objects.get(folio_factura="1116")
    
    print(f"Folio: {factura.folio_factura}")
    print(f"Cliente: {factura.cliente}")
    print(f"Total: ${factura.total:,.2f}")
    print(f"\nDetalles:")
    
    suma_precio_venta = Decimal("0")
    suma_precio_compra = Decimal("0")
    
    for det in factura.detalles.all():
        importe_venta = det.cantidad * det.precio_unitario
        importe_compra = det.cantidad * det.precio_compra
        
        suma_precio_venta += importe_venta
        suma_precio_compra += importe_compra
        
        print(f"\n  Producto: {det.producto.nombre}")
        print(f"  Cantidad: {det.cantidad}")
        print(f"  Precio unitario (VENTA): ${det.precio_unitario:,.2f}")
        print(f"  Precio compra (COSTO): ${det.precio_compra:,.2f}")
        print(f"  Importe con precio venta: ${importe_venta:,.2f}")
        print(f"  Importe con precio compra: ${importe_compra:,.2f}")
        
        # Verificar con los precios del producto
        print(f"\n  Producto en inventario:")
        print(f"    precio_venta: ${det.producto.precio_venta:,.2f}")
        print(f"    precio_compra: ${det.producto.precio_compra:,.2f}")
    
    print(f"\n=== TOTALES ===")
    print(f"Suma con precios de VENTA: ${suma_precio_venta:,.2f}")
    print(f"Suma con precios de COMPRA: ${suma_precio_compra:,.2f}")
    print(f"Total factura: ${factura.total:,.2f}")
    
    diferencia_venta = abs(factura.total - suma_precio_venta)
    diferencia_compra = abs(factura.total - suma_precio_compra)
    
    print(f"\nDiferencia con precio venta: ${diferencia_venta:,.2f}")
    print(f"Diferencia con precio compra: ${diferencia_compra:,.2f}")
    
    if diferencia_venta < Decimal("1.00"):
        print("\n[OK] La factura usa precios de VENTA correctamente")
    elif diferencia_compra < Decimal("1.00"):
        print("\n[ERROR] La factura esta usando precios de COMPRA!")
    else:
        print("\n[WARNING] Hay una discrepancia en los precios")
    
except Factura.DoesNotExist:
    print("Factura 1116 NO encontrada en la base de datos")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
