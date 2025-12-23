"""
Script de prueba para verificar la acción de marcar facturas como pagadas.
Crea facturas de prueba pendientes y pagadas.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from decimal import Decimal
from datetime import date, timedelta

print("="*80)
print(" TEST: MARCAR FACTURAS COMO PAGADAS")
print("="*80)
print()

# Limpiar facturas de prueba anteriores
print("[*] Limpiando facturas de prueba anteriores...")
Factura.objects.filter(folio_factura__startswith="TEST-PAGO-").delete()
print("   OK")
print()

# Crear facturas de prueba
print("[*] Creando facturas de prueba...")
print()

facturas_creadas = []

# 3 facturas pendientes (sin pagar)
for i in range(1, 4):
    factura = Factura.objects.create(
        folio_factura=f"TEST-PAGO-PEND-{i}",
        cliente=f"Cliente Test {i}",
        fecha_facturacion=date.today() - timedelta(days=10+i),
        vencimiento=date.today() - timedelta(days=i),
        total=Decimal(f"{1000 * i}.00"),
        metodo_pago="PUE",
        pagado=False,
        fecha_pago=None
    )
    facturas_creadas.append(factura)
    print(f"   [PENDIENTE] {factura.folio_factura} - {factura.cliente} - ${factura.total:,.2f}")

# 2 facturas ya pagadas
for i in range(1, 3):
    factura = Factura.objects.create(
        folio_factura=f"TEST-PAGO-PAGADA-{i}",
        cliente=f"Cliente Ya Pagado {i}",
        fecha_facturacion=date.today() - timedelta(days=20+i),
        vencimiento=date.today() - timedelta(days=10+i),
        total=Decimal(f"{500 * i}.00"),
        metodo_pago="PUE",
        pagado=True,
        fecha_pago=date.today() - timedelta(days=5)
    )
    facturas_creadas.append(factura)
    print(f"   [YA PAGADA] {factura.folio_factura} - {factura.cliente} - ${factura.total:,.2f}")

print()
print(f"[OK] {len(facturas_creadas)} facturas de prueba creadas")
print()

print("="*80)
print(" INSTRUCCIONES PARA PROBAR")
print("="*80)
print()
print("1. Abre el admin de Django:")
print("   http://localhost:8000/admin/ventas/factura/")
print()
print("2. Busca las facturas que empiecen con 'TEST-PAGO-'")
print()
print("3. Selecciona TODAS las facturas de prueba (5 facturas):")
print("   - 3 pendientes")
print("   - 2 ya pagadas")
print()
print("4. En el menu desplegable 'Accion:', selecciona:")
print("   'Marcar como pagadas (con fecha)'")
print()
print("5. Click en 'Ir'")
print()
print("6. Veras una pagina con:")
print("   - Resumen: 5 total, 3 pendientes, 2 ya pagadas")
print("   - Lista de facturas pendientes")
print("   - Calendario para seleccionar fecha")
print()
print("7. Selecciona una fecha (ej: hoy) y click en:")
print("   'Marcar 3 factura(s) como pagadas'")
print()
print("8. Verificar:")
print("   - Mensaje de exito: '3 factura(s) marcadas como pagadas...'")
print("   - Las 3 pendientes ahora tienen check verde en columna 'Pagado'")
print("   - Las 2 que ya estaban pagadas siguen igual")
print()
print("="*80)
print()
print("[VERIFICACION MANUAL]")
print()
print("Puedes verificar en la BD:")
print()
print("from ventas.models import Factura")
print("pendientes = Factura.objects.filter(folio_factura__startswith='TEST-PAGO-PEND')")
print("for f in pendientes:")
print("    print(f'{f.folio_factura}: Pagado={f.pagado}, Fecha={f.fecha_pago}')")
print()
print("="*80)
print()
print("[LIMPIEZA]")
print("Para eliminar las facturas de prueba:")
print("Factura.objects.filter(folio_factura__startswith='TEST-PAGO-').delete()")
print()
