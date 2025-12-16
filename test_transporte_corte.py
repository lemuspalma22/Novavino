"""
Script para verificar que el cálculo de transporte en cortes esté funcionando.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from utils.reportes import calcular_agregados_periodo_ventas, generar_dict_reporte_factura
from datetime import datetime, timedelta

print("\n" + "="*80)
print("VERIFICACION: CALCULO DE TRANSPORTE EN CORTES")
print("="*80)

# 1. Obtener última factura como ejemplo
print("\n[1/3] Obteniendo factura de ejemplo...")
print("-"*80)

factura = Factura.objects.filter(detalles__isnull=False).first()

if not factura:
    print("  [ADVERTENCIA] No hay facturas en la BD")
    exit(0)

print(f"  [OK] Factura: {factura.folio_factura}")
print(f"  Cliente: {factura.cliente}")
print(f"  Total: ${factura.total:.2f}")

# 2. Verificar cálculo de transporte en dict reporte
print("\n[2/3] Verificando función generar_dict_reporte_factura...")
print("-"*80)

reporte_dict = generar_dict_reporte_factura(factura)

print(f"  Costo Proveedores: ${reporte_dict['costo_proveedores']:.2f}")
print(f"  Transporte: ${reporte_dict.get('transporte', 0):.2f}")
print(f"  Ganancia: ${reporte_dict['ganancia']:.2f}")

# Verificar detalles
print("\n  Detalles de productos:")
for detalle in factura.detalles.all():
    costo_transporte = getattr(detalle.producto, 'costo_transporte', 0) or 0
    transporte_total = costo_transporte * detalle.cantidad
    print(f"    - {detalle.producto.nombre}")
    print(f"      Cantidad: {detalle.cantidad}")
    print(f"      Precio compra unitario: ${detalle.precio_compra:.2f}")
    print(f"      Transporte unitario: ${costo_transporte:.2f}")
    print(f"      Transporte total: ${transporte_total:.2f}")

# 3. Verificar agregados de período
print("\n[3/3] Verificando función calcular_agregados_periodo_ventas...")
print("-"*80)

# Usar fecha de la factura ±7 días
if factura.fecha_facturacion:
    fecha_inicio = factura.fecha_facturacion - timedelta(days=7)
    fecha_fin = factura.fecha_facturacion + timedelta(days=7)
else:
    # Usar fechas recientes
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)

agregados = calcular_agregados_periodo_ventas(
    Factura.objects.all(),
    fecha_inicio,
    fecha_fin,
    campo_fecha='fecha_facturacion',
    solo_pagadas=False
)

print(f"  Período: {fecha_inicio} a {fecha_fin}")
print(f"  Total Venta: ${agregados['total_venta']:.2f}")
print(f"  Costo Total: ${agregados['costo_total']:.2f}")
print(f"  Transporte Total: ${agregados.get('transporte_total', 0):.2f}")
print(f"  Ganancia Total: ${agregados['ganancia_total']:.2f}")

# Verificación de coherencia
print("\n" + "="*80)
print("VERIFICACION DE COHERENCIA")
print("="*80)

transporte_esperado = sum(
    (d.cantidad or 0) * (getattr(d.producto, 'costo_transporte', 0) or 0)
    for f in agregados['queryset']
    for d in f.detalles.all()
)

print(f"  Transporte calculado por agregados: ${agregados.get('transporte_total', 0):.2f}")
print(f"  Transporte calculado manualmente:   ${transporte_esperado:.2f}")

if abs(agregados.get('transporte_total', 0) - transporte_esperado) < 0.01:
    print("\n  [OK] Los cálculos coinciden ✅")
else:
    print("\n  [ERROR] Los cálculos NO coinciden ❌")

print("\n" + "="*80)
print("COMPLETADO")
print("="*80)
print("\nVerifica que:")
print("  1. El campo 'transporte' aparece en generar_dict_reporte_factura")
print("  2. El campo 'transporte_total' aparece en calcular_agregados_periodo_ventas")
print("  3. Los valores son correctos (costo_transporte * cantidad)")
print("  4. Los templates muestran la columna de transporte")
print("\n" + "="*80 + "\n")
