"""
Test simplificado para verificar restauración de stock en ventas.
Usa el primer producto disponible en la BD.
"""
from decimal import Decimal
from django.utils import timezone
from ventas.models import Factura, DetalleFactura
from inventario.models import Producto

print("\n" + "="*80)
print("TEST RÁPIDO: Restauración de Stock en Ventas")
print("="*80)

# Buscar primer producto
producto = Producto.objects.first()
if not producto:
    print("❌ No hay productos en la BD")
    exit()

print(f"\nProducto: {producto.nombre}")
stock_inicial = producto.stock or 0
print(f"Stock inicial: {stock_inicial}")

# Crear venta
cantidad = 2
factura = Factura.objects.create(
    folio_factura=f"TEST-{int(timezone.now().timestamp())}",
    cliente="Test",
    fecha_facturacion=timezone.now().date()
)

DetalleFactura.objects.create(
    factura=factura,
    producto=producto,
    cantidad=cantidad,
    precio_unitario=producto.precio_venta or Decimal("100.00"),
    precio_compra=producto.precio_compra or Decimal("50.00")
)

print(f"\n→ Venta creada: {cantidad} unidades")
producto.refresh_from_db()
stock_despues_venta = producto.stock or 0
print(f"   Stock después de venta: {stock_despues_venta}")
print(f"   Descontado: {stock_inicial - stock_despues_venta}")

# Eliminar venta
print(f"\n→ Eliminando factura...")
factura.delete()

producto.refresh_from_db()
stock_final = producto.stock or 0
print(f"   Stock después de eliminar: {stock_final}")
print(f"   Restaurado: {stock_final - stock_despues_venta}")

# Resultado
print("\n" + "="*80)
if stock_final == stock_inicial:
    print("✅ TEST PASADO")
    print(f"   Stock inicial = Stock final = {stock_inicial}")
else:
    print("❌ TEST FALLADO")
    print(f"   Stock inicial: {stock_inicial}")
    print(f"   Stock final: {stock_final}")
    print(f"   Diferencia: {stock_final - stock_inicial}")
print("="*80 + "\n")
