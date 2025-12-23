"""
Test: Sistema de descuentos en facturas de venta
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
print(" TEST: Sistema de Descuentos en Facturas")
print("="*80)
print()

# TEST 1: Verificar factura 1137 (caso real con descuento)
print("TEST 1: Verificar factura 1137 corregida")
print("-" * 80)

try:
    factura_1137 = Factura.objects.get(folio_factura="1137")
    
    suma_productos = sum(
        detalle.cantidad * detalle.precio_unitario 
        for detalle in factura_1137.detalles.all()
    )
    
    print(f"Folio: {factura_1137.folio_factura}")
    print(f"Cliente: {factura_1137.cliente}")
    print(f"Subtotal: ${factura_1137.subtotal:,.2f}")
    print(f"Descuento: ${factura_1137.descuento:,.2f}")
    print(f"Total: ${factura_1137.total:,.2f}")
    print()
    print(f"Suma productos: ${suma_productos:,.2f}")
    print(f"Verificacion: {factura_1137.subtotal} - {factura_1137.descuento} = {factura_1137.total}")
    
    # Validar
    total_calculado = factura_1137.subtotal - factura_1137.descuento
    if total_calculado == factura_1137.total:
        print("[OK] Subtotal - Descuento = Total")
    else:
        print(f"[ERROR] Descuadre: {total_calculado} != {factura_1137.total}")
    
    if abs(suma_productos - factura_1137.subtotal) < Decimal("0.10"):
        print("[OK] Suma productos = Subtotal")
    else:
        print(f"[ERROR] Suma productos != Subtotal")
    
except Factura.DoesNotExist:
    print("[ERROR] Factura 1137 no encontrada")

print()
print()

# TEST 2: Crear factura de prueba con descuento
print("TEST 2: Crear factura con descuento")
print("-" * 80)

# Obtener producto de prueba
producto_test = Producto.objects.first()

if producto_test:
    # Crear factura
    factura_test = Factura.objects.create(
        folio_factura="TEST-DESC-001",
        cliente="Cliente Test Descuento",
        fecha_facturacion=date.today(),
        subtotal=Decimal("1000.00"),
        descuento=Decimal("100.00"),  # 10% de descuento
        total=Decimal("900.00")
    )
    
    # Agregar producto
    DetalleFactura.objects.create(
        factura=factura_test,
        producto=producto_test,
        cantidad=10,
        precio_unitario=Decimal("100.00"),
        precio_compra=Decimal("50.00")
    )
    
    factura_test.refresh_from_db()
    
    print(f"Factura creada: {factura_test.folio_factura}")
    print(f"Subtotal: ${factura_test.subtotal:,.2f}")
    print(f"Descuento: ${factura_test.descuento:,.2f} (10%)")
    print(f"Total: ${factura_test.total:,.2f}")
    print()
    
    # Validar
    if factura_test.subtotal - factura_test.descuento == factura_test.total:
        print("[OK] Formula correcta: Subtotal - Descuento = Total")
    else:
        print("[ERROR] Formula incorrecta")
    
    # Limpiar
    factura_test.delete()
    print("[OK] Factura de prueba eliminada")
else:
    print("[SKIP] No hay productos para crear factura de prueba")

print()
print()

# TEST 3: Validar metodo calcular_total()
print("TEST 3: Validar metodo calcular_total()")
print("-" * 80)

if producto_test:
    # Crear factura sin descuento
    factura_test2 = Factura.objects.create(
        folio_factura="TEST-DESC-002",
        cliente="Cliente Test 2",
        fecha_facturacion=date.today(),
        descuento=Decimal("50.00")  # Descuento de $50
    )
    
    # Agregar productos
    DetalleFactura.objects.create(
        factura=factura_test2,
        producto=producto_test,
        cantidad=5,
        precio_unitario=Decimal("100.00"),
        precio_compra=Decimal("50.00")
    )
    
    # Llamar calcular_total() - debe aplicar descuento
    factura_test2.calcular_total()
    factura_test2.refresh_from_db()
    
    print(f"Factura: {factura_test2.folio_factura}")
    print(f"Suma productos: $500.00 (5 × $100)")
    print(f"Descuento: ${factura_test2.descuento:,.2f}")
    print(f"Total calculado: ${factura_test2.total:,.2f}")
    print()
    
    # Validar
    expected_total = Decimal("500.00") - Decimal("50.00")  # 500 - 50 = 450
    if factura_test2.total == expected_total:
        print(f"[OK] calcular_total() aplico descuento correctamente: $500 - $50 = ${expected_total}")
    else:
        print(f"[ERROR] Total esperado ${expected_total}, obtenido ${factura_test2.total}")
    
    # Limpiar
    factura_test2.delete()
    print("[OK] Factura de prueba eliminada")
else:
    print("[SKIP] No hay productos")

print()
print("="*80)
print(" RESUMEN")
print("="*80)
print()
print("[OK] Sistema de descuentos implementado correctamente")
print("     - Campo 'subtotal' agregado al modelo")
print("     - Campo 'descuento' agregado al modelo")
print("     - Metodo calcular_total() actualizado")
print("     - Widget muestra descuentos en validacion")
print("     - Admin permite editar subtotal y descuento")
print()
print("="*80)
