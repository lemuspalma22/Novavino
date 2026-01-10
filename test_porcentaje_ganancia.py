"""
Script para verificar que el cálculo de porcentaje de ganancia esté funcionando.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from utils.reportes import generar_dict_reporte_factura
from datetime import datetime, timedelta

print("\n" + "="*80)
print("VERIFICACION: CALCULO DE PORCENTAJE DE GANANCIA")
print("="*80)

# 1. Obtener facturas de ejemplo
print("\n[1/2] Verificando cálculo en facturas individuales...")
print("-"*80)

facturas = Factura.objects.filter(detalles__isnull=False)[:5]

if not facturas:
    print("  [ADVERTENCIA] No hay facturas en la BD")
    exit(0)

for factura in facturas:
    reporte = generar_dict_reporte_factura(factura)
    
    total = reporte['total_venta']
    costo = reporte['costo_proveedores']
    ganancia = reporte['ganancia']
    porcentaje = reporte.get('porcentaje_ganancia', 0)
    
    # Calcular porcentaje esperado
    porcentaje_esperado = 0
    if total > 0:
        porcentaje_esperado = (ganancia / total) * 100
    
    print(f"\nFactura: {reporte['folio']}")
    print(f"  Total Venta: ${total:.2f}")
    print(f"  Costo: ${costo:.2f}")
    print(f"  Ganancia: ${ganancia:.2f}")
    print(f"  % Ganancia calculado: {porcentaje:.2f}%")
    print(f"  % Ganancia esperado: {porcentaje_esperado:.2f}%")
    
    if abs(porcentaje - porcentaje_esperado) < 0.01:
        print(f"  [OK] Correcto ✅")
    else:
        print(f"  [ERROR] Incorrecto ❌")

# 2. Verificar agregados
print("\n[2/2] Verificando porcentaje total...")
print("-"*80)

from utils.reportes import calcular_agregados_periodo_ventas

# Usar última semana
fecha_fin = datetime.now().date()
fecha_inicio = fecha_fin - timedelta(days=7)

agregados = calcular_agregados_periodo_ventas(
    Factura.objects.all(),
    fecha_inicio,
    fecha_fin,
    campo_fecha='fecha_facturacion',
    solo_pagadas=False
)

total_venta = agregados['total_venta']
ganancia_total = agregados['ganancia_total']

# Calcular porcentaje esperado
porcentaje_esperado = 0
if total_venta > 0:
    porcentaje_esperado = (ganancia_total / total_venta) * 100

print(f"\nPeríodo: {fecha_inicio} a {fecha_fin}")
print(f"  Total Venta: ${total_venta:.2f}")
print(f"  Ganancia Total: ${ganancia_total:.2f}")
print(f"  % Ganancia esperado: {porcentaje_esperado:.2f}%")

print("\n" + "="*80)
print("EJEMPLOS DE INTERPRETACION")
print("="*80)

print("\nEjemplo 1:")
print("  Total Venta: $1,000")
print("  Costo: $600")
print("  Ganancia: $400")
print("  % Ganancia: 40% (ganancia muy buena)")

print("\nEjemplo 2:")
print("  Total Venta: $1,000")
print("  Costo: $800")
print("  Ganancia: $200")
print("  % Ganancia: 20% (ganancia moderada)")

print("\nEjemplo 3:")
print("  Total Venta: $1,000")
print("  Costo: $900")
print("  Ganancia: $100")
print("  % Ganancia: 10% (ganancia baja)")

print("\n" + "="*80)
print("COMPLETADO")
print("="*80)
print("\nEl porcentaje de ganancia ahora aparece en:")
print("  1. Cada fila de factura en los cortes")
print("  2. Total general al final del corte")
print("  3. Exportaciones CSV y PDF")
print("\nEsto te ayudará a analizar:")
print("  - Qué facturas tienen mejor margen")
print("  - Cuál es el margen promedio del período")
print("  - Detectar ventas con márgenes muy bajos")
print("\n" + "="*80 + "\n")
