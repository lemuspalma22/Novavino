"""
Debug para EPICO - Revisar extracción y stock
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from extractors.vieja_bodega import ExtractorViejaBodega
from inventario.models import Producto, ProductoNoReconocido
from compras.models import CompraProducto

# 1. Extraer datos del PDF
print("=== EXTRACCION DEL PDF ===")
result = ExtractorViejaBodega(None, 'VBM041202DD1FB24900.pdf').parse()

print(f"Folio: {result.get('folio')}")
print(f"UUID: {result.get('uuid', 'N/A')[:30]}...")
print(f"Total: ${result.get('total')}")

conceptos = result.get('conceptos', [])
print(f"\nConceptos extraídos: {len(conceptos)}")
for c in conceptos:
    print(f"  - {c['descripcion']}: {c['cantidad']} x ${c['precio_unitario']}")

# 2. Buscar el producto en la BD
print("\n=== PRODUCTO EN BD ===")
epico = Producto.objects.filter(nombre__icontains="EPICO").first()

if epico:
    print(f"Nombre: {epico.nombre}")
    print(f"ID: {epico.id}")
    print(f"Stock actual: {epico.stock}")
    
    # CompraProducto asociados
    compras = CompraProducto.objects.filter(producto=epico)
    print(f"\nCompraProducto asociados: {compras.count()}")
    for cp in compras:
        print(f"  - Compra {cp.compra.folio}: {cp.cantidad} unidades")
    
    stock_compras = sum(cp.cantidad for cp in compras)
    print(f"\nStock esperado según compras: {stock_compras}")
    print(f"Stock actual: {epico.stock}")
    print(f"Diferencia: {epico.stock - stock_compras}")
    
    # PNR asociados
    print("\n=== PNR ASOCIADOS ===")
    pnrs = ProductoNoReconocido.objects.filter(producto=epico).order_by('-fecha_detectado')
    print(f"Total PNR: {pnrs.count()}")
    for pnr in pnrs:
        print(f"  - {pnr.nombre_detectado}")
        print(f"    Procesado: {pnr.procesado}")
        print(f"    Movimiento generado: {pnr.movimiento_generado}")
        print(f"    UUID: {pnr.uuid_factura[:30] if pnr.uuid_factura else 'N/A'}...")
        print(f"    Cantidad: {pnr.cantidad}")
else:
    print("No se encontró el producto EPICO en la BD")
    
    # Buscar PNR con ese nombre
    print("\n=== PNR CON 'EPICO' ===")
    pnrs_epico = ProductoNoReconocido.objects.filter(nombre_detectado__icontains="EPICO")
    print(f"Total: {pnrs_epico.count()}")
    for pnr in pnrs_epico:
        print(f"  - {pnr.nombre_detectado}")
        print(f"    Procesado: {pnr.procesado}")
        print(f"    Producto asignado: {pnr.producto}")
