"""Test: Validación de precios BD vs Factura"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto
from decimal import Decimal

print("\n" + "="*70)
print("TEST: VALIDACION PRECIOS BD vs FACTURA")
print("="*70)

# Test con factura 2364
folio_test = "2364"

try:
    compra = Compra.objects.get(folio=folio_test)
    print(f"\n[TEST] Factura: {folio_test}")
    print(f"Total factura: ${compra.total:,.2f}")
    print(f"Proveedor: {compra.proveedor.nombre if compra.proveedor else 'N/A'}")
    
    productos = CompraProducto.objects.filter(compra=compra)
    print(f"\nProductos: {productos.count()}")
    print("-" * 70)
    
    suma_pdf = Decimal("0")
    suma_bd = Decimal("0")
    
    for cp in productos:
        cantidad = cp.cantidad or 0
        precio_pdf = cp.precio_unitario or Decimal("0")
        precio_bd = cp.producto.precio_compra or Decimal("0")
        
        importe_pdf = cantidad * precio_pdf
        importe_bd = cantidad * precio_bd
        
        suma_pdf += importe_pdf
        suma_bd += importe_bd
        
        diff_precio = abs(precio_pdf - precio_bd)
        diff_pct = (diff_precio / precio_bd * 100) if precio_bd else Decimal("0")
        
        print(f"\n{cp.producto.nombre[:50]:50}")
        print(f"  Cantidad: {cantidad}")
        print(f"  Precio PDF: ${precio_pdf:,.2f}")
        print(f"  Precio BD:  ${precio_bd:,.2f}")
        
        if diff_pct > Decimal("0.5"):
            print(f"  [ALERTA] Diferencia: ${diff_precio:,.2f} ({diff_pct:.2f}%)")
        else:
            print(f"  [OK] Diferencia: ${diff_precio:,.2f} ({diff_pct:.2f}%)")
        
        print(f"  Importe PDF: ${importe_pdf:,.2f}")
        print(f"  Importe BD:  ${importe_bd:,.2f}")
    
    print("\n" + "="*70)
    print("RESUMEN:")
    print(f"  Suma usando precios PDF: ${suma_pdf:,.2f}")
    print(f"  Suma usando precios BD:  ${suma_bd:,.2f}")
    print(f"  Total factura:           ${compra.total:,.2f}")
    
    diff_pdf = abs(compra.total - suma_pdf)
    diff_bd = abs(compra.total - suma_bd)
    
    diff_pdf_pct = (diff_pdf / compra.total * 100) if compra.total else Decimal("0")
    diff_bd_pct = (diff_bd / compra.total * 100) if compra.total else Decimal("0")
    
    print(f"\n  Diferencia PDF vs Factura: ${diff_pdf:,.2f} ({diff_pdf_pct:.2f}%)")
    print(f"  Diferencia BD vs Factura:  ${diff_bd:,.2f} ({diff_bd_pct:.2f}%)")
    
    print("\n" + "="*70)
    print("VALIDACION:")
    
    if diff_pdf_pct < Decimal("0.01"):
        print("  [PROBLEMA] PDF cuadra perfecto - NO detectaria errores de facturacion")
    
    if diff_bd_pct > Decimal("1.0"):
        print(f"  [GUARDIAN ACTIVO] BD no cuadra (>{diff_bd_pct:.2f}%) - MARCARIA PARA REVISION")
    elif diff_bd_pct > Decimal("0.5"):
        print(f"  [GUARDIAN ALERTA] BD no cuadra ({diff_bd_pct:.2f}%) - En umbral amarillo")
    else:
        print(f"  [GUARDIAN OK] BD cuadra ({diff_bd_pct:.2f}%) - Todo correcto")
    
    print("="*70 + "\n")

except Compra.DoesNotExist:
    print(f"[ERROR] Factura {folio_test} no encontrada")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
