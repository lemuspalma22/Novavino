"""
Corregir factura 1137 aplicando descuento correcto
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from decimal import Decimal

print("="*80)
print(" CORRECCION: Factura 1137")
print("="*80)
print()

try:
    factura = Factura.objects.get(folio_factura="1137")
except Factura.DoesNotExist:
    print("ERROR: No se encontro la factura 1137")
    exit(1)

print(f"Factura: {factura.folio_factura}")
print(f"Cliente: {factura.cliente}")
print()

# Calcular suma de productos
suma_productos = sum(
    detalle.cantidad * detalle.precio_unitario 
    for detalle in factura.detalles.all()
)

print("ANTES DE LA CORRECCION:")
print("-" * 80)
print(f"Subtotal actual: ${factura.subtotal:,.2f}")
print(f"Descuento actual: ${factura.descuento:,.2f}")
print(f"Total actual: ${factura.total:,.2f}")
print(f"Suma productos: ${suma_productos:,.2f}")
print()

# Total correcto segun usuario
total_correcto = Decimal("6763.00")
descuento_calculado = suma_productos - total_correcto

print("CALCULO DEL DESCUENTO:")
print("-" * 80)
print(f"Suma productos:      ${suma_productos:,.2f}")
print(f"Total correcto:      ${total_correcto:,.2f}")
print(f"Descuento necesario: ${descuento_calculado:,.2f}")
print(f"Porcentaje:          {(descuento_calculado / suma_productos * 100):.2f}%")
print()

# Aplicar correccion
print("Aplicando correccion...")
factura.subtotal = suma_productos
factura.descuento = descuento_calculado
factura.total = total_correcto
factura.save(update_fields=["subtotal", "descuento", "total"])

print("[OK] Factura actualizada")
print()

# Verificar
factura.refresh_from_db()

print("DESPUES DE LA CORRECCION:")
print("-" * 80)
print(f"Subtotal: ${factura.subtotal:,.2f}")
print(f"Descuento: ${factura.descuento:,.2f}")
print(f"Total: ${factura.total:,.2f}")
print()

# Validacion
if factura.subtotal - factura.descuento == factura.total:
    print("[OK] Subtotal - Descuento = Total")
else:
    print("[ERROR] Los montos no cuadran!")

print()
print("="*80)
print()
print("INSTRUCCIONES:")
print("1. Recarga el servidor si esta corriendo")
print("2. Abre la factura 1137 en el admin")
print("3. Verifica que en 'Validacion de totales' aparezca:")
print(f"   - Suma productos: ${suma_productos:,.2f}")
print(f"   - Descuento: -${descuento_calculado:,.2f}")
print(f"   - Total factura: ${total_correcto:,.2f}")
print()
print("="*80)
