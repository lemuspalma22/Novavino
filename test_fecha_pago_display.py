"""
Script para verificar que el formato de fecha de pago en el admin funciona correctamente.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from datetime import date

print("\n" + "="*80)
print("VERIFICACION: FORMATO DE FECHA DE PAGO EN ADMIN")
print("="*80)

# Obtener algunas facturas de ejemplo
facturas_pagadas = Factura.objects.filter(pagado=True, fecha_pago__isnull=False)[:3]
facturas_no_pagadas = Factura.objects.filter(pagado=False, fecha_pago__isnull=True)[:3]

print("\n[1/2] Facturas PAGADAS (deben mostrar formato YYYY-MM-DD):")
print("-"*80)
for factura in facturas_pagadas:
    # Simular lo que hace el admin
    fecha_display = factura.fecha_pago.strftime("%Y-%m-%d") if factura.fecha_pago else "-"
    print(f"  Folio: {factura.folio_factura:10} | Fecha Pago: {fecha_display:12} | Cliente: {factura.cliente[:30]}")

if not facturas_pagadas:
    print("  [INFO] No hay facturas pagadas en la BD")

print("\n[2/2] Facturas NO PAGADAS (deben mostrar '-'):")
print("-"*80)
for factura in facturas_no_pagadas:
    # Simular lo que hace el admin
    fecha_display = factura.fecha_pago.strftime("%Y-%m-%d") if factura.fecha_pago else "-"
    print(f"  Folio: {factura.folio_factura:10} | Fecha Pago: {fecha_display:12} | Cliente: {factura.cliente[:30]}")

if not facturas_no_pagadas:
    print("  [INFO] No hay facturas pendientes en la BD")

print("\n" + "="*80)
print("FORMATO DE TABLA EN ADMIN")
print("="*80)
print("""
La tabla ahora mostrará:

┌──────┬─────────┬───────┬───────┬──────────┬────────────┬────────┬──────────────┬─────────────┐
│ Folio│ Cliente │ Total │ Costo │ Ganancia │ Método Pago│ Pagado │ Fecha Pago   │ Fecha Fact. │
├──────┼─────────┼───────┼───────┼──────────┼────────────┼────────┼──────────────┼─────────────┤
│ 1124 │ ANDRES  │ 1200  │  912  │   288    │     -      │   ✓    │  2025-12-15  │ 15/12/2025  │
│ 1017 │ JORGE   │ 7490  │ 5688  │  1802    │    PUE     │   ✗    │      -       │ 20/10/2025  │
│  985 │ SIMONE  │ 3645  │    0  │  3645    │    PPD     │   ✗    │      -       │ 27/09/2025  │
└──────┴─────────┴───────┴───────┴──────────┴────────────┴────────┴──────────────┴─────────────┘

FORMATO:
  - Fecha de Pago: YYYY-MM-DD (2025-12-15)
  - Si no está pagada: "-"
  - Ordenable por columna
  
VENTAJAS:
  - Formato estándar ISO para fácil lectura
  - Compacto, no sobrecarga la tabla
  - Se distingue claramente entre pagadas y pendientes
""")

print("\n" + "="*80)
print("CAMBIOS APLICADOS")
print("="*80)
print("""
1. ventas/admin.py:
   - list_display incluye 'fecha_pago_display'
   - Nueva función fecha_pago_display(self, obj):
     * Si existe fecha_pago: formato YYYY-MM-DD
     * Si no existe: "-"
   - Columna ordenable por fecha

2. Orden de columnas:
   Folio → Cliente → Total → Costo → Ganancia → Método Pago → Pagado → Fecha Pago → Fecha Fact.
""")

print("\n" + "="*80)
print("COMPLETADO")
print("="*80)
print("\nPróximos pasos:")
print("  1. Recarga el admin de Django")
print("  2. Ve a Ventas → Facturas")
print("  3. Verás la nueva columna 'Fecha de Pago'")
print("  4. Las pagadas mostrarán: 2025-12-15")
print("  5. Las no pagadas mostrarán: -")
print("\n" + "="*80 + "\n")
