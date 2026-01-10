"""
Test para verificar que el costo_total incluye correctamente el transporte.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from decimal import Decimal

print("="*80)
print(" VERIFICACION: COSTO CON TRANSPORTE")
print("="*80)
print()

# Buscar la factura mencionada por el usuario
folio = "VPG1125-03"
try:
    factura = Factura.objects.get(folio_factura=folio)
except Factura.DoesNotExist:
    print(f"[ERROR] No se encontro la factura {folio}")
    print("Buscando facturas recientes para probar...")
    factura = Factura.objects.filter(detalles__isnull=False).first()
    if not factura:
        print("[ERROR] No hay facturas con detalles para probar")
        exit(1)
    folio = factura.folio_factura

print(f"Factura: {folio}")
print(f"Cliente: {factura.cliente}")
print(f"Total: ${factura.total:,.2f}")
print()

print("="*80)
print(" ANALISIS DE DETALLES")
print("="*80)
print()

total_costo_sin_transporte = Decimal("0.00")
total_costo_con_transporte = Decimal("0.00")

for i, detalle in enumerate(factura.detalles.all(), 1):
    print(f"[{i}] {detalle.producto.nombre}")
    print(f"    Cantidad: {detalle.cantidad}")
    print(f"    Precio venta unitario: ${detalle.precio_unitario:,.2f}")
    print(f"    Precio compra (guardado): ${detalle.precio_compra:,.2f}")
    print()
    
    # Costos del producto
    precio_base = detalle.producto.precio_compra or Decimal("0.00")
    transporte = detalle.producto.costo_transporte or Decimal("0.00")
    
    print(f"    Producto en inventario:")
    print(f"      - Precio compra base: ${precio_base:,.2f}")
    print(f"      - Costo transporte: ${transporte:,.2f}")
    print(f"      - Total con transporte: ${precio_base + transporte:,.2f}")
    print()
    
    # Calcular costos
    costo_sin_trans = detalle.cantidad * detalle.precio_compra
    costo_con_trans = detalle.cantidad * detalle.costo_con_transporte
    
    print(f"    Subtotales:")
    print(f"      - Sin transporte: {detalle.cantidad} x ${detalle.precio_compra:,.2f} = ${costo_sin_trans:,.2f}")
    print(f"      - Con transporte: {detalle.cantidad} x ${detalle.costo_con_transporte:,.2f} = ${costo_con_trans:,.2f}")
    
    diferencia = costo_con_trans - costo_sin_trans
    if diferencia > 0:
        print(f"      - Diferencia: +${diferencia:,.2f} (transporte)")
    print()
    
    total_costo_sin_transporte += costo_sin_trans
    total_costo_con_transporte += costo_con_trans

print("="*80)
print(" RESUMEN DE COSTOS")
print("="*80)
print()

print(f"Total factura: ${factura.total:,.2f}")
print()
print(f"COSTO SIN TRANSPORTE:")
print(f"  Total: ${total_costo_sin_transporte:,.2f}")
print(f"  Ganancia: ${factura.total - total_costo_sin_transporte:,.2f}")
print(f"  Margen: {((factura.total - total_costo_sin_transporte) / factura.total * 100):.1f}%")
print()
print(f"COSTO CON TRANSPORTE (CORRECTO):")
print(f"  Total: ${total_costo_con_transporte:,.2f}")
print(f"  Ganancia: ${factura.total - total_costo_con_transporte:,.2f}")
print(f"  Margen: {((factura.total - total_costo_con_transporte) / factura.total * 100):.1f}%")
print()

# Verificar que la propiedad use el costo correcto
costo_propiedad = factura.costo_total
ganancia_propiedad = factura.ganancia_total

print(f"USANDO PROPIEDADES DE FACTURA:")
print(f"  factura.costo_total: ${costo_propiedad:,.2f}")
print(f"  factura.ganancia_total: ${ganancia_propiedad:,.2f}")
print(f"  factura.porcentaje_costo: {factura.porcentaje_costo * 100:.1f}%")
print(f"  factura.porcentaje_ganancia: {factura.porcentaje_ganancia * 100:.1f}%")
print()

# Verificacion
print("="*80)
print(" VERIFICACION")
print("="*80)
print()

diferencia_total = total_costo_con_transporte - total_costo_sin_transporte

if abs(costo_propiedad - total_costo_con_transporte) < Decimal("0.01"):
    print("[OK] La propiedad costo_total incluye el transporte correctamente")
else:
    print("[FALLO] La propiedad costo_total NO coincide con el calculo manual")
    print(f"  Esperado: ${total_costo_con_transporte:,.2f}")
    print(f"  Obtenido: ${costo_propiedad:,.2f}")

print()

if diferencia_total > 0:
    print(f"[INFO] El transporte agrega ${diferencia_total:,.2f} al costo total")
    print(f"       Esto reduce la ganancia de ${factura.total - total_costo_sin_transporte:,.2f}")
    print(f"       a ${ganancia_propiedad:,.2f}")
else:
    print("[INFO] Esta factura no tiene costo de transporte adicional")

print()
print("="*80)
print()
print("[SOLUCION IMPLEMENTADA]")
print("La propiedad costo_total ahora usa detalle.costo_con_transporte")
print("que SIEMPRE recalcula desde el producto actual, garantizando que")
print("incluye el costo de transporte sin importar que este guardado")
print("en detalle.precio_compra")
print()
