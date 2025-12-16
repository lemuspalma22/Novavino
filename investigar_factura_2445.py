"""Investigar por qué TRES RIBERAS no se detectó en factura 2445"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto
from inventario.models import ProductoNoReconocido
from decimal import Decimal

print("\n" + "="*70)
print("INVESTIGACION: FACTURA 2445 - TRES RIBERAS FALTANTE")
print("="*70)

try:
    compra = Compra.objects.get(folio="2445")
    
    print(f"\nFactura: {compra.folio}")
    print(f"Total: ${compra.total:,.2f}")
    print(f"Proveedor: {compra.proveedor.nombre if compra.proveedor else 'N/A'}")
    print(f"Estado: {compra.estado_revision}")
    print(f"Requiere revision: {compra.requiere_revision_manual}")
    
    # Productos detectados
    productos = CompraProducto.objects.filter(compra=compra)
    print(f"\n{'='*70}")
    print(f"PRODUCTOS DETECTADOS: {productos.count()}")
    print("-"*70)
    
    suma_bd = Decimal("0")
    suma_pdf = Decimal("0")
    
    for cp in productos:
        cantidad = cp.cantidad or 0
        precio_pdf = cp.precio_unitario or Decimal("0")
        precio_bd = cp.producto.precio_compra if cp.producto else Decimal("0")
        
        importe_pdf = cantidad * precio_pdf
        importe_bd = cantidad * precio_bd
        
        suma_pdf += importe_pdf
        suma_bd += importe_bd
        
        print(f"\n{cp.producto.nombre if cp.producto else 'N/A'}")
        print(f"  Cantidad: {cantidad}")
        print(f"  P/U PDF: ${precio_pdf:,.2f}")
        print(f"  P/U BD:  ${precio_bd:,.2f}")
        print(f"  Importe: ${importe_pdf:,.2f}")
    
    print(f"\n{'='*70}")
    print(f"SUMA PDF:  ${suma_pdf:,.2f}")
    print(f"SUMA BD:   ${suma_bd:,.2f}")
    print(f"TOTAL:     ${compra.total:,.2f}")
    print(f"FALTANTE:  ${compra.total - suma_pdf:,.2f}")
    
    # Buscar PNR
    pnr_list = ProductoNoReconocido.objects.filter(uuid_factura=compra.uuid, procesado=False)
    print(f"\n{'='*70}")
    print(f"PRODUCTOS NO RECONOCIDOS (PNR): {pnr_list.count()}")
    print("-"*70)
    
    if pnr_list.exists():
        for pnr in pnr_list:
            cantidad = pnr.cantidad or Decimal("0")
            precio = pnr.precio_unitario or Decimal("0")
            importe = cantidad * precio
            
            print(f"\n[PNR] {pnr.nombre_detectado}")
            print(f"  Cantidad: {cantidad}")
            print(f"  P/U extraido: ${precio:,.2f}")
            print(f"  Importe: ${importe:,.2f}")
    else:
        print("\n[INFO] No hay PNR pendientes")
        print("\nEsto significa que:")
        print("  1. El extractor NO detecto el producto TRES RIBERAS en el PDF")
        print("  2. Necesitamos revisar el extractor o agregar manualmente")
    
    # Verificar si existe en BD
    print(f"\n{'='*70}")
    print("BUSCAR 'TRES RIBERAS' EN BASE DE DATOS:")
    print("-"*70)
    
    from inventario.models import Producto, AliasProducto
    
    # Buscar por nombre
    productos_encontrados = Producto.objects.filter(
        nombre__icontains="tres riberas"
    )
    
    if productos_encontrados.exists():
        print(f"\n[OK] Encontrado en BD ({productos_encontrados.count()} resultados):")
        for prod in productos_encontrados:
            print(f"  - {prod.nombre}")
            print(f"    Precio compra: ${prod.precio_compra:,.2f}")
            print(f"    Proveedor: {prod.proveedor.nombre if prod.proveedor else 'N/A'}")
    else:
        print("\n[INFO] NO encontrado en BD")
        print("       Necesita ser creado como producto nuevo")
    
    # Buscar por alias
    alias_encontrados = AliasProducto.objects.filter(
        alias__icontains="tres riberas"
    )
    
    if alias_encontrados.exists():
        print(f"\n[OK] Encontrado por alias ({alias_encontrados.count()} resultados):")
        for alias in alias_encontrados:
            print(f"  - Alias: {alias.alias}")
            print(f"    Producto: {alias.producto.nombre}")
    
    print("\n" + "="*70)
    print("DIAGNOSTICO:")
    print("-"*70)
    
    if not pnr_list.exists():
        print("\n[PROBLEMA] El extractor NO detecto 'TRES RIBERAS' en el PDF")
        print("\nPosibles causas:")
        print("  1. Nombre muy largo o con caracteres especiales")
        print("  2. Formato de tabla diferente en esta factura")
        print("  3. Producto en posicion inusual del PDF")
        print("\nSoluciones:")
        print("  1. Reprocesar factura")
        print("  2. Agregar producto manualmente desde admin")
        print("  3. Revisar extractor para mejorar deteccion")
    else:
        print("\n[INFO] Producto esta en PNR - Necesita ser asignado/creado")
    
    print("="*70 + "\n")

except Compra.DoesNotExist:
    print("\n[ERROR] Factura 2445 no encontrada")
    print("="*70 + "\n")
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    print("="*70 + "\n")
