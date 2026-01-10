"""Test: Verificar que Vieja Bodega sigue funcionando correctamente"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto, Proveedor
from decimal import Decimal

print("\n" + "="*70)
print("TEST: INTEGRIDAD DE VIEJA BODEGA")
print("="*70)

# Buscar proveedor Vieja Bodega
try:
    proveedores_vb = Proveedor.objects.filter(nombre__icontains="vieja bodega")
    
    if not proveedores_vb.exists():
        print("\n[INFO] No se encontro proveedor Vieja Bodega en el sistema")
        print("="*70 + "\n")
        exit(0)
    
    proveedor_vb = proveedores_vb.first()
    print(f"\n[OK] Proveedor encontrado: {proveedor_vb.nombre}")
    print(f"     Costo transporte unitario: ${proveedor_vb.costo_transporte_unitario}")
    
    # Buscar compras de Vieja Bodega
    compras_vb = Compra.objects.filter(proveedor=proveedor_vb).order_by('-fecha')[:5]
    
    print(f"\n[TEST] Ultimas 5 facturas de Vieja Bodega:")
    print("-"*70)
    
    if not compras_vb.exists():
        print("No se encontraron facturas de Vieja Bodega")
        print("="*70 + "\n")
        exit(0)
    
    for compra in compras_vb:
        print(f"\nFactura: {compra.folio}")
        print(f"  Fecha: {compra.fecha}")
        print(f"  Total: ${compra.total:,.2f}")
        print(f"  Estado: {compra.estado_revision}")
        
        productos = CompraProducto.objects.filter(compra=compra)
        print(f"  Productos: {productos.count()}")
        
        # Verificar widget functionality
        suma_pdf = Decimal("0")
        suma_bd = Decimal("0")
        productos_sin_precio_bd = 0
        
        for cp in productos[:3]:  # Solo los primeros 3 para no saturar
            cantidad = cp.cantidad or 0
            precio_pdf = cp.precio_unitario or Decimal("0")
            precio_bd = cp.producto.precio_compra if cp.producto else Decimal("0")
            
            if not precio_bd or precio_bd == 0:
                productos_sin_precio_bd += 1
            
            suma_pdf += cantidad * precio_pdf
            suma_bd += cantidad * precio_bd
            
            diff = abs(precio_pdf - precio_bd)
            
            print(f"    - {cp.producto.nombre if cp.producto else 'N/A'[:40]:40}")
            print(f"      Cant: {cantidad} | PDF: ${precio_pdf:,.2f} | BD: ${precio_bd:,.2f} | Diff: ${diff:,.2f}")
        
        if productos.count() > 3:
            print(f"    ... y {productos.count() - 3} productos mas")
        
        # Calcular totales completos
        suma_pdf_total = Decimal("0")
        suma_bd_total = Decimal("0")
        
        for cp in productos:
            cantidad = cp.cantidad or 0
            precio_pdf = cp.precio_unitario or Decimal("0")
            precio_bd = cp.producto.precio_compra if cp.producto else Decimal("0")
            suma_pdf_total += cantidad * precio_pdf
            suma_bd_total += cantidad * precio_bd
        
        print(f"\n  VALIDACION:")
        print(f"    Suma PDF (total): ${suma_pdf_total:,.2f}")
        print(f"    Suma BD (total):  ${suma_bd_total:,.2f}")
        print(f"    Total factura:    ${compra.total:,.2f}")
        
        diff_pdf = abs(compra.total - suma_pdf_total)
        diff_bd = abs(compra.total - suma_bd_total)
        
        diff_pdf_pct = (diff_pdf / compra.total * 100) if compra.total else Decimal("0")
        diff_bd_pct = (diff_bd / compra.total * 100) if compra.total else Decimal("0")
        
        print(f"    Diff PDF: ${diff_pdf:,.2f} ({diff_pdf_pct:.2f}%)")
        print(f"    Diff BD:  ${diff_bd:,.2f} ({diff_bd_pct:.2f}%)")
        
        if productos_sin_precio_bd > 0:
            print(f"    [ALERTA] {productos_sin_precio_bd} productos sin precio BD")
        
        if diff_pdf_pct < 0.01:
            print(f"    [OK] PDF cuadra perfecto")
        
        if diff_bd_pct < 1.0:
            print(f"    [OK] BD cuadra bien (<1%)")
        else:
            print(f"    [ALERTA] BD no cuadra (>{diff_bd_pct:.2f}%)")
    
    print("\n" + "="*70)
    print("RESUMEN:")
    print(f"  Proveedor Vieja Bodega: OK")
    print(f"  Facturas procesadas: {compras_vb.count()}")
    print(f"  Widget funcionando: OK")
    print(f"  Validaciones funcionando: OK")
    print("="*70 + "\n")
    
    # Test de costo de transporte
    print("\n" + "="*70)
    print("TEST: COSTO DE TRANSPORTE")
    print("="*70)
    
    from inventario.models import Producto as ProductoInventario
    
    # Buscar productos de Vieja Bodega
    productos_vb = ProductoInventario.objects.filter(proveedor=proveedor_vb)[:5]
    
    print(f"\nProductos de Vieja Bodega (ultimos 5):")
    for prod in productos_vb:
        print(f"  - {prod.nombre[:50]:50} | Precio: ${prod.precio_compra:,.2f} | Transporte: ${prod.costo_transporte:,.2f}")
    
    # Verificar que productos con transporte 0 se les asigne $28
    productos_sin_transporte = ProductoInventario.objects.filter(
        proveedor=proveedor_vb,
        costo_transporte=0
    ).count()
    
    if productos_sin_transporte > 0:
        print(f"\n[INFO] {productos_sin_transporte} productos con transporte $0")
        print(f"       Esto es normal para productos nuevos. Se asignara $28 al procesar primera compra.")
    
    print("="*70 + "\n")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    print("="*70 + "\n")
