"""
Test para verificar que al eliminar una factura de ventas,
el stock se restaura correctamente.

Ejecutar con: python manage.py shell < test_stock_ventas_delete.py
O copiar y pegar en: python manage.py shell
"""
from decimal import Decimal
from django.utils import timezone
from ventas.models import Factura, DetalleFactura
from inventario.models import Producto

print("="*80)
print("TEST: RESTAURACIÓN DE STOCK AL ELIMINAR FACTURA DE VENTAS")
print("="*80)

# 1. Crear o buscar un producto de prueba
try:
    producto = Producto.objects.get(nombre="Test Botella Vino 1")
    print(f"\n✓ Producto encontrado: {producto.nombre}")
except Producto.DoesNotExist:
    producto = Producto.objects.create(
        nombre="Test Botella Vino 1",
        precio_compra=Decimal("100.00"),
        precio_venta=Decimal("200.00"),
        stock=100
    )
    print(f"\n✓ Producto creado: {producto.nombre}")

# Guardar stock inicial
stock_inicial = producto.stock or 0
print(f"   Stock inicial: {stock_inicial}")

# 2. Crear factura de venta
factura = Factura.objects.create(
    folio_factura=f"TEST-VENTA-{timezone.now().timestamp()}",
    cliente="Cliente Test",
    fecha_facturacion=timezone.now().date(),
    total=Decimal("0.00")
)
print(f"\n✓ Factura creada: {factura.folio_factura}")

# 3. Crear detalle (esto debe descontar del stock)
cantidad_vendida = 5
detalle = DetalleFactura.objects.create(
    factura=factura,
    producto=producto,
    cantidad=cantidad_vendida,
    precio_unitario=Decimal("200.00"),
    precio_compra=Decimal("100.00")
)
print(f"✓ Detalle creado: {cantidad_vendida} unidades")

# Verificar que el stock se descontó
producto.refresh_from_db()
stock_despues_venta = producto.stock or 0
print(f"\n   Stock después de venta: {stock_despues_venta}")
print(f"   Diferencia: {stock_inicial - stock_despues_venta}")

if stock_despues_venta == stock_inicial - cantidad_vendida:
    print("   ✓ CORRECTO: Stock descontado correctamente")
else:
    print(f"   ✗ ERROR: Esperaba {stock_inicial - cantidad_vendida}, pero tengo {stock_despues_venta}")

# 4. Eliminar la factura (debe restaurar el stock)
print(f"\n📝 Eliminando factura {factura.folio_factura}...")
factura_id = factura.id
factura.delete()  # Esto elimina en cascada los DetalleFactura
print("✓ Factura eliminada")

# 5. Verificar que el stock se restauró
producto.refresh_from_db()
stock_final = producto.stock or 0
print(f"\n   Stock final: {stock_final}")
print(f"   Stock inicial: {stock_inicial}")

print("\n" + "="*80)
print("RESULTADO DEL TEST")
print("="*80)

if stock_final == stock_inicial:
    print("✅ TEST PASADO: El stock se restauró correctamente")
    print(f"   Stock inicial: {stock_inicial}")
    print(f"   Stock después de venta: {stock_despues_venta}")
    print(f"   Stock después de eliminar: {stock_final}")
    print(f"   Diferencia: {stock_final - stock_inicial} (esperado: 0)")
else:
    print("❌ TEST FALLADO: El stock NO se restauró correctamente")
    print(f"   Stock inicial: {stock_inicial}")
    print(f"   Stock después de venta: {stock_despues_venta}")
    print(f"   Stock final: {stock_final}")
    print(f"   Diferencia: {stock_final - stock_inicial} (esperado: 0)")
    print(f"   Falta restaurar: {stock_inicial - stock_final}")

print("="*80)

# Resumen
print("\nFLUJO VERIFICADO:")
print(f"1. Stock inicial:           {stock_inicial}")
print(f"2. Venta de {cantidad_vendida} unidades:     {stock_inicial} - {cantidad_vendida} = {stock_despues_venta}")
print(f"3. Eliminar factura:        {stock_despues_venta} + {cantidad_vendida} = {stock_final}")
print(f"4. Resultado:               {'✓ OK' if stock_final == stock_inicial else '✗ ERROR'}")
