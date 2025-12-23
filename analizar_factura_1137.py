"""
Analizar factura 1137 - Problema con descuento
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from decimal import Decimal

print("="*80)
print(" ANALISIS: Factura 1137 - Descuento")
print("="*80)
print()

try:
    factura = Factura.objects.get(folio_factura="1137")
except Factura.DoesNotExist:
    print("ERROR: No se encontro la factura 1137")
    exit(1)

print(f"Folio: {factura.folio_factura}")
print(f"Cliente: {factura.cliente}")
print(f"Fecha: {factura.fecha_facturacion}")
print(f"Total factura: ${factura.total:,.2f}")
print()

# Revisar campos disponibles
print("CAMPOS DE LA FACTURA:")
print("-" * 80)
print(f"Total: ${factura.total:,.2f}")

# Verificar campos relacionados con montos
campos_monto = ['subtotal', 'iva', 'descuento', 'descuento_monto', 'total_sin_descuento']
for campo in campos_monto:
    if hasattr(factura, campo):
        valor = getattr(factura, campo)
        if valor:
            print(f"{campo.capitalize()}: ${valor:,.2f}")
        else:
            print(f"{campo.capitalize()}: $0.00 (campo existe pero vacio)")
    else:
        print(f"{campo.capitalize()}: (campo no existe)")

print()
print("PRODUCTOS:")
print("-" * 80)

suma_productos = Decimal("0")
detalles = factura.detalles.all()

for i, detalle in enumerate(detalles, 1):
    cantidad = detalle.cantidad or 0
    precio_u = detalle.precio_unitario or Decimal("0")
    importe = cantidad * precio_u
    suma_productos += importe
    
    print(f"\n{i}. {detalle.producto.nombre}")
    print(f"   Cantidad: {cantidad}")
    print(f"   Precio unitario: ${precio_u:,.2f}")
    print(f"   Importe: ${importe:,.2f}")

print()
print("="*80)
print(" ANALISIS DE TOTALES")
print("="*80)
print()

print(f"Suma productos:     ${suma_productos:,.2f}")
print(f"Total factura:      ${factura.total:,.2f}")

diferencia = suma_productos - factura.total
print(f"Diferencia:         ${diferencia:,.2f}")

if diferencia > 0:
    print()
    print(f"[IDENTIFICADO] Hay un descuento de ${diferencia:,.2f}")
    descuento_pct = (diferencia / suma_productos) * 100
    print(f"               Descuento del {descuento_pct:.2f}%")
    print()
    print("VERIFICACION:")
    print(f"  Suma productos:  ${suma_productos:,.2f}")
    print(f"  - Descuento:     ${diferencia:,.2f}")
    print(f"  = Total:         ${suma_productos - diferencia:,.2f}")
    print(f"  Total factura:   ${factura.total:,.2f}")
    print(f"  Cuadra: {'SI' if abs((suma_productos - diferencia) - factura.total) < Decimal('0.10') else 'NO'}")

print()
print("="*80)
print(" ESTRUCTURA DEL MODELO")
print("="*80)
print()

from django.db import connection
from django.apps import apps

Factura_model = apps.get_model('ventas', 'Factura')
print("Campos del modelo Factura:")
for field in Factura_model._meta.fields:
    print(f"  - {field.name}: {field.get_internal_type()}")

print()
print("="*80)
