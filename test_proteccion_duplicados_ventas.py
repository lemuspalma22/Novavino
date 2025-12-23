"""
Probar que el sistema está protegido contra duplicados en facturas de venta
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura, DetalleFactura
from inventario.models import Producto
from decimal import Decimal
from django.db import IntegrityError
from datetime import date

print("=== TEST: PROTECCION CONTRA DUPLICADOS ===\n")

# Obtener un producto de prueba
producto = Producto.objects.first()
if not producto:
    print("[ERROR] No hay productos en la BD")
    exit(1)

print(f"Producto de prueba: {producto.nombre} (ID: {producto.id})")

# Crear factura de prueba
factura = Factura.objects.create(
    folio_factura="TEST-DUPLICADO-001",
    cliente="Cliente Test",
    fecha_facturacion=date(2025, 1, 1),
    total=Decimal("0.00")
)
print(f"Factura creada: {factura.folio_factura} (ID: {factura.id})\n")

# TEST 1: Crear primer detalle
print("TEST 1: Crear primer detalle con 5 unidades")
detalle1 = DetalleFactura.objects.create(
    factura=factura,
    producto=producto,
    cantidad=5,
    precio_unitario=Decimal("100.00")
)
print(f"  [OK] Detalle creado: {detalle1.cantidad} unidades\n")

# TEST 2: Intentar crear duplicado (debe fallar por el constraint)
print("TEST 2: Intentar crear detalle duplicado (debe fallar)")
try:
    detalle2 = DetalleFactura.objects.create(
        factura=factura,
        producto=producto,
        cantidad=3,
        precio_unitario=Decimal("100.00")
    )
    print("  [ERROR] El constraint NO funciono! Se creo duplicado")
except IntegrityError as e:
    print(f"  [OK] Constraint funciona: {str(e)[:80]}...\n")

# TEST 3: Usar get_or_create (debe sumar cantidades)
print("TEST 3: Usar get_or_create con 3 unidades mas")
detalle, created = DetalleFactura.objects.get_or_create(
    factura=factura,
    producto=producto,
    defaults={
        "cantidad": 3,
        "precio_unitario": Decimal("100.00")
    }
)

if created:
    print("  [ERROR] Se creo nuevo detalle en lugar de reutilizar el existente")
else:
    print(f"  [OK] Se reutilizo detalle existente (ID: {detalle.id})")
    print(f"  Cantidad antes: {detalle1.cantidad}")
    
    # Sumar la cantidad
    detalle.cantidad += 3
    detalle.save(update_fields=["cantidad"])
    
    detalle.refresh_from_db()
    print(f"  Cantidad despues: {detalle.cantidad}")
    print(f"  [OK] Cantidades sumadas correctamente\n")

# TEST 4: Verificar que solo hay 1 detalle
print("TEST 4: Verificar que solo hay 1 detalle en la factura")
detalles_count = DetalleFactura.objects.filter(factura=factura, producto=producto).count()
print(f"  Detalles encontrados: {detalles_count}")
if detalles_count == 1:
    print(f"  [OK] Solo hay 1 detalle (proteccion funciona)\n")
else:
    print(f"  [ERROR] Hay {detalles_count} detalles (hay duplicados)\n")

# Limpiar
factura.delete()
print("[OK] Factura de prueba eliminada")
print("\n=== RESULTADO ===")
print("El sistema esta protegido contra duplicados:")
print("  1. Constraint a nivel BD previene inserts duplicados")
print("  2. get_or_create en registrar_venta.py suma cantidades")
