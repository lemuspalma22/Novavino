"""Test: Mostrar cómo se verá el widget mejorado"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto
from decimal import Decimal

print("\n" + "="*70)
print("PREVIEW: WIDGET MEJORADO - FACTURA 2364")
print("="*70)

folio = "2364"
compra = Compra.objects.get(folio=folio)
productos = CompraProducto.objects.filter(compra=compra)

print(f"\n{'='*70}")
print("OK Productos detectados: 4")
print("\nNota: Para Secretos de la Vid, el P/U mostrado ya incluye")
print("      IEPS 26.5%, IVA 16% y descuento 24% aplicados.")
print(f"{'='*70}\n")

suma_pdf = Decimal("0")
suma_bd = Decimal("0")
hay_discrepancias = False

for cp in productos:
    cantidad = cp.cantidad or 0
    precio_pdf = cp.precio_unitario or Decimal("0")
    precio_bd = cp.producto.precio_compra or Decimal("0")
    
    importe_pdf = cantidad * precio_pdf
    importe_bd = cantidad * precio_bd
    
    suma_pdf += importe_pdf
    suma_bd += importe_bd
    
    diff_precio = abs(precio_pdf - precio_bd)
    diff_precio_pct = (diff_precio / precio_bd * 100) if precio_bd else Decimal("0")
    
    nombre = cp.producto.nombre
    
    # Clasificar y mostrar
    if diff_precio_pct > Decimal("1.0"):
        hay_discrepancias = True
        print(f"- {nombre} | {cantidad} x ${precio_pdf:,.2f} (BD: ${precio_bd:,.2f}) = ${importe_pdf:,.2f} [!] [ROJO]")
    elif diff_precio_pct > Decimal("0.1"):
        hay_discrepancias = True
        print(f"- {nombre} | {cantidad} x ${precio_pdf:,.2f} (BD: ${precio_bd:,.2f}) = ${importe_pdf:,.2f} [!] [NARANJA]")
    elif diff_precio > Decimal("0.01"):
        print(f"- {nombre} | {cantidad} x ${precio_pdf:,.2f} (BD: ${precio_bd:,.2f}) = ${importe_pdf:,.2f} [GRIS]")
    else:
        print(f"- {nombre} | {cantidad} x ${precio_pdf:,.2f} = ${importe_pdf:,.2f}")

total_factura = compra.total
diferencia = abs(total_factura - suma_bd)
diferencia_pct = (diferencia / total_factura * 100) if total_factura else Decimal("0")

print(f"\n{'='*70}")
if diferencia_pct < Decimal("0.5"):
    print(f"[OK] Suma esperada (BD): ${suma_bd:,.2f}  [VERDE]")
elif diferencia_pct < Decimal("1.0"):
    print(f"[!] Suma esperada (BD): ${suma_bd:,.2f}  [AMARILLO]")
else:
    print(f"[X] Suma esperada (BD): ${suma_bd:,.2f}  [ROJO]")

print(f"    Total factura: ${total_factura:,.2f}")
print(f"    Diferencia: ${diferencia:,.2f} ({diferencia_pct:.2f}%)")

if hay_discrepancias:
    print(f"\n[i] Productos con diferencia de precio BD vs PDF mostrados arriba.")
    print(f"    Esto puede ser normal por redondeos o indicar error de facturacion.")

print("="*70 + "\n")

# Explicación de colores
print("LEYENDA DE COLORES:")
print("  [ROJO]    - Diferencia >1%  -> Error de facturacion probable")
print("  [NARANJA] - Diferencia >0.1% -> Diferencia notable, revisar")
print("  [GRIS]    - Diferencia >$0.01 -> Redondeo normal")
print("  (sin marca) - Precio exacto\n")
