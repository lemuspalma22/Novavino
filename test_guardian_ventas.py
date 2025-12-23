"""
Script de prueba para verificar el guardian de precios en ventas.
Simula una factura con productos a diferentes precios y verifica que el guardian detecte los sospechosos.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura, DetalleFactura
from inventario.models import Producto
from decimal import Decimal
from datetime import date

print("="*80)
print(" TEST: GUARDIAN DE PRECIOS EN VENTAS")
print("="*80)
print()

# Buscar productos existentes con precio_venta definido
productos_test = Producto.objects.filter(precio_venta__gt=0).order_by('-precio_venta')[:3]

if productos_test.count() < 3:
    print("[ERROR] No hay suficientes productos con precio_venta definido para probar")
    print("       Necesitas al menos 3 productos con precio_venta > 0")
    exit(1)

print("[*] Productos seleccionados para la prueba:")
print()
for p in productos_test:
    print(f"  - {p.nombre}")
    print(f"    Precio venta BD: ${p.precio_venta:,.2f}")
    print()

# Crear factura de prueba
print("[*] Creando factura de prueba...")
factura = Factura.objects.create(
    folio_factura="TEST-GUARDIAN-VENTAS",
    cliente="Cliente Test Guardian",
    fecha_facturacion=date.today(),
    total=Decimal("0"),
    metodo_pago="PUE"
)
print(f"   Factura creada: {factura.folio_factura}")
print()

# Escenarios de prueba
print("[TEST] Escenarios de prueba:")
print()

# Escenario 1: Precio OK (95% del precio BD - dentro de tolerancia)
prod1 = productos_test[0]
precio_ok = prod1.precio_venta * Decimal("0.95")
DetalleFactura.objects.create(
    factura=factura,
    producto=prod1,
    cantidad=10,
    precio_unitario=precio_ok,
    precio_compra=prod1.precio_compra or Decimal("0")
)
print(f"[OK] Escenario 1: Precio OK (95% del precio BD)")
print(f"   Producto: {prod1.nombre}")
print(f"   Precio BD: ${prod1.precio_venta:,.2f}")
print(f"   Precio facturado: ${precio_ok:,.2f} (95%)")
print(f"   >> NO debe alertar (dentro de tolerancia del 10%)")
print()

# Escenario 2: Precio en el límite (90% del precio BD - justo en el límite)
prod2 = productos_test[1]
precio_limite = prod2.precio_venta * Decimal("0.90")
DetalleFactura.objects.create(
    factura=factura,
    producto=prod2,
    cantidad=5,
    precio_unitario=precio_limite,
    precio_compra=prod2.precio_compra or Decimal("0")
)
print(f"[LIMIT] Escenario 2: Precio en el limite (90% del precio BD)")
print(f"   Producto: {prod2.nombre}")
print(f"   Precio BD: ${prod2.precio_venta:,.2f}")
print(f"   Precio facturado: ${precio_limite:,.2f} (90%)")
print(f"   >> NO debe alertar (justo en el limite)")
print()

# Escenario 3: Precio sospechoso (50% del precio BD - fuera de tolerancia)
prod3 = productos_test[2]
precio_sospechoso = prod3.precio_venta * Decimal("0.50")
DetalleFactura.objects.create(
    factura=factura,
    producto=prod3,
    cantidad=3,
    precio_unitario=precio_sospechoso,
    precio_compra=prod3.precio_compra or Decimal("0")
)
print(f"[ALERT] Escenario 3: Precio SOSPECHOSO (50% del precio BD)")
print(f"   Producto: {prod3.nombre}")
print(f"   Precio BD: ${prod3.precio_venta:,.2f}")
print(f"   Precio facturado: ${precio_sospechoso:,.2f} (50%)")
print(f"   >> SI debe alertar (menor al 90%)")
print()

# Actualizar total de factura
total = (precio_ok * 10) + (precio_limite * 5) + (precio_sospechoso * 3)
factura.total = total
factura.save(update_fields=["total"])

print("="*80)
print(" RESULTADO")
print("="*80)
print()
print(f"Factura creada: {factura.folio_factura}")
print(f"URL del admin: /admin/ventas/factura/{factura.id}/change/")
print()
print("[INSTRUCCIONES]")
print()
print("1. Abre el admin de Django en tu navegador:")
print(f"   http://localhost:8000/admin/ventas/factura/{factura.id}/change/")
print()
print("2. Busca la seccion 'Resumen del estado de revision'")
print()
print("3. Verifica que el GUARDIAN muestre:")
print(f"   [OK] {prod1.nombre} - SIN alerta (precio 95%)")
print(f"   [OK] {prod2.nombre} - SIN alerta (precio 90%)")
print(f"   [ALERTA] {prod3.nombre} - CON alerta (precio 50%)")
print()
print("4. Debe aparecer un mensaje:")
print("   'GUARDIAN: 1 producto(s) con precio menor al esperado'")
print()
print("5. El mensaje final debe decir:")
print("   'Revision recomendada: El guardian detecto productos...'")
print()
print("="*80)
print()
print("[LIMPIEZA]")
print(f"   Para eliminar esta factura de prueba:")
print(f"   Factura.objects.get(folio_factura='TEST-GUARDIAN-VENTAS').delete()")
print()
