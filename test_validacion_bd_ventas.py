"""
Test: Validación de precios contra BD en widget de ventas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura

print("="*80)
print(" TEST: Validacion de precios contra BD (Guardian)")
print("="*80)
print()

# Buscar una factura con productos
factura = Factura.objects.filter(detalles__isnull=False).first()

if not factura:
    print("No hay facturas con productos para probar")
    exit(0)

print(f"Factura: {factura.folio_factura}")
print(f"Cliente: {factura.cliente}")
print(f"Total factura: ${factura.total:,.2f}")
print()

print("DETALLES:")
print("-" * 80)

from decimal import Decimal

suma_real = Decimal("0")
suma_esperada_bd = Decimal("0")

for detalle in factura.detalles.all():
    cantidad = detalle.cantidad or 0
    precio_factura = detalle.precio_unitario or Decimal("0")
    precio_bd = detalle.producto.precio_venta or Decimal("0")
    
    importe_real = cantidad * precio_factura
    importe_esperado = cantidad * precio_bd if precio_bd > 0 else Decimal("0")
    
    suma_real += importe_real
    if precio_bd > 0:
        suma_esperada_bd += importe_esperado
    
    print(f"\n{detalle.producto.nombre[:50]}")
    print(f"  Cantidad: {cantidad}")
    print(f"  Precio factura: ${precio_factura:,.2f}")
    print(f"  Precio BD:      ${precio_bd:,.2f}")
    print(f"  Importe real:   ${importe_real:,.2f}")
    if precio_bd > 0:
        print(f"  Importe esper.: ${importe_esperado:,.2f}")
        if precio_factura < precio_bd * Decimal("0.90"):
            diff_pct = ((precio_bd - precio_factura) / precio_bd) * 100
            print(f"  [ALERTA] Precio {diff_pct:.0f}% menor al esperado!")

print()
print("="*80)
print(" RESUMEN")
print("="*80)
print()

print(f"Suma real (factura):   ${suma_real:,.2f}")

if suma_esperada_bd > 0:
    print(f"Suma esperada (BD):    ${suma_esperada_bd:,.2f}")
    diferencia = suma_real - suma_esperada_bd
    diferencia_pct = abs((diferencia / suma_esperada_bd) * 100)
    
    print(f"Diferencia:            ${diferencia:,.2f} ({diferencia_pct:.1f}%)")
    print()
    
    if abs(diferencia_pct) > 10:
        print("[CRITICO] Diferencia > 10% - El guardian debe mostrar alerta ROJA")
    elif abs(diferencia_pct) > 5:
        print("[ADVERTENCIA] Diferencia > 5% - El guardian debe mostrar alerta AMARILLA")
    else:
        print("[OK] Diferencia < 5% - El guardian debe mostrar check VERDE")
else:
    print("[INFO] No hay precios en BD para comparar")

print()
print("="*80)
print()
print("INSTRUCCIONES:")
print("1. Inicia el servidor: python manage.py runserver")
print("2. Ve al admin de facturas")
print(f"3. Abre la factura {factura.folio_factura}")
print("4. Busca la seccion 'Validacion contra BD (Guardian)'")
print("5. Verifica que muestre:")
print("   - Suma esperada (BD)")
print("   - Suma real (Factura)")
print("   - Diferencia con color segun porcentaje")
print()
print("="*80)
