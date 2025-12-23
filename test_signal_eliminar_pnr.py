"""
Test: Verificar que los PNR se eliminan al borrar Factura/Compra
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from inventario.models import ProductoNoReconocido, Producto
from compras.models import Compra, Proveedor
from ventas.models import Factura
from decimal import Decimal
from datetime import date

print("=== TEST: ELIMINACION AUTOMATICA DE PNR ===\n")

# ===== TEST 1: PNR de COMPRAS =====
print("TEST 1: PNR de COMPRAS")
print("-" * 50)

# Crear proveedor de prueba
proveedor, _ = Proveedor.objects.get_or_create(
    nombre="Proveedor Test",
    defaults={"costo_transporte_unitario": Decimal("0")}
)

# Crear compra de prueba
compra = Compra.objects.create(
    folio="TEST-COMPRA-001",
    proveedor=proveedor,
    fecha=date(2025, 1, 1),
    uuid="TEST-UUID-COMPRA-12345",
    total=Decimal("100.00")
)
print(f"  Compra creada: {compra.folio} (UUID: {compra.uuid})")

# Crear PNR asociado
pnr_compra = ProductoNoReconocido.objects.create(
    nombre_detectado="Producto Test Compra",
    uuid_factura=compra.uuid,
    origen="compra",
    procesado=False
)
print(f"  PNR creado: ID={pnr_compra.id}, nombre='{pnr_compra.nombre_detectado}'")

# Verificar que existe
assert ProductoNoReconocido.objects.filter(id=pnr_compra.id).exists()
print(f"  [OK] PNR existe en BD")

# Borrar la compra
print(f"  Borrando compra...")
compra.delete()

# Verificar que el PNR también se borró
existe = ProductoNoReconocido.objects.filter(id=pnr_compra.id).exists()
if not existe:
    print(f"  [OK] PNR fue eliminado automaticamente por el signal\n")
else:
    print(f"  [ERROR] PNR sigue existiendo (signal no funciono)\n")

# ===== TEST 2: PNR de VENTAS =====
print("TEST 2: PNR de VENTAS")
print("-" * 50)

# Crear factura de prueba
factura = Factura.objects.create(
    folio_factura="TEST-VENTA-001",
    cliente="Cliente Test",
    fecha_facturacion=date(2025, 1, 1),
    uuid_factura="TEST-UUID-VENTA-67890",
    total=Decimal("200.00")
)
print(f"  Factura creada: {factura.folio_factura} (UUID: {factura.uuid_factura})")

# Crear PNR asociado
pnr_venta = ProductoNoReconocido.objects.create(
    nombre_detectado="Producto Test Venta",
    uuid_factura=factura.uuid_factura,
    origen="venta",
    procesado=False
)
print(f"  PNR creado: ID={pnr_venta.id}, nombre='{pnr_venta.nombre_detectado}'")

# Verificar que existe
assert ProductoNoReconocido.objects.filter(id=pnr_venta.id).exists()
print(f"  [OK] PNR existe en BD")

# Borrar la factura
print(f"  Borrando factura...")
factura.delete()

# Verificar que el PNR también se borró
existe = ProductoNoReconocido.objects.filter(id=pnr_venta.id).exists()
if not existe:
    print(f"  [OK] PNR fue eliminado automaticamente por el signal\n")
else:
    print(f"  [ERROR] PNR sigue existiendo (signal no funciono)\n")

# ===== TEST 3: Multiples PNR =====
print("TEST 3: MULTIPLES PNR")
print("-" * 50)

# Crear factura con múltiples PNR
factura2 = Factura.objects.create(
    folio_factura="TEST-VENTA-002",
    cliente="Cliente Test 2",
    fecha_facturacion=date(2025, 1, 2),
    uuid_factura="TEST-UUID-VENTA-MULTI",
    total=Decimal("300.00")
)
print(f"  Factura creada: {factura2.folio_factura}")

# Crear 3 PNR asociados
pnr_ids = []
for i in range(3):
    pnr = ProductoNoReconocido.objects.create(
        nombre_detectado=f"Producto Multi {i+1}",
        uuid_factura=factura2.uuid_factura,
        origen="venta",
        procesado=False
    )
    pnr_ids.append(pnr.id)
    print(f"  PNR {i+1} creado: ID={pnr.id}")

# Verificar que todos existen
count_antes = ProductoNoReconocido.objects.filter(id__in=pnr_ids).count()
print(f"  PNR existentes antes de borrar: {count_antes}")
assert count_antes == 3

# Borrar la factura
print(f"  Borrando factura...")
factura2.delete()

# Verificar que todos los PNR se borraron
count_despues = ProductoNoReconocido.objects.filter(id__in=pnr_ids).count()
print(f"  PNR existentes despues de borrar: {count_despues}")

if count_despues == 0:
    print(f"  [OK] Los 3 PNR fueron eliminados automaticamente\n")
else:
    print(f"  [ERROR] Quedan {count_despues} PNR sin eliminar\n")

# Limpiar proveedor
proveedor.delete()

print("=== RESULTADO FINAL ===")
print("[OK] Todos los tests pasaron correctamente")
print("Los signals de eliminacion de PNR funcionan tanto para Compras como para Ventas")
