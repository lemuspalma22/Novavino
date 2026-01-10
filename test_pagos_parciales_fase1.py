"""
Test de FASE 1: Pagos Parciales en Ventas
Verifica que las propiedades calculadas y la distribución proporcional funcionan correctamente.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura, DetalleFactura, PagoFactura
from inventario.models import Producto
from compras.models import Proveedor
from decimal import Decimal
from datetime import date, timedelta

print("="*80)
print(" TEST: FASE 1 - PAGOS PARCIALES Y DISTRIBUCIÓN PROPORCIONAL")
print("="*80)
print()

# Limpiar datos de prueba
print("[*] Limpiando datos de prueba anteriores...")
Factura.objects.filter(folio_factura__startswith="TEST-PP-").delete()
print("    OK")
print()

# Crear factura de prueba
print("[*] Creando factura de prueba...")
factura = Factura.objects.create(
    folio_factura="TEST-PP-001",
    cliente="Cliente Test Pagos Parciales",
    fecha_facturacion=date.today() - timedelta(days=10),
    vencimiento=date.today() + timedelta(days=5),
    total=Decimal("2000.00"),
    metodo_pago="PPD"
)
print(f"    Factura creada: {factura.folio_factura}")
print()

# Crear productos de prueba
print("[*] Creando productos para la factura...")
# Necesitamos un proveedor
proveedor = Proveedor.objects.first()
if not proveedor:
    proveedor = Proveedor.objects.create(nombre="Proveedor Test")

# Producto 1: $100 costo, $150 venta (50% margen)
producto1, _ = Producto.objects.get_or_create(
    nombre="Producto Test 1",
    defaults={
        "proveedor": proveedor,
        "precio_compra": Decimal("100.00"),
        "precio_venta": Decimal("150.00")
    }
)

# Producto 2: $130 costo, $185 venta (42% margen)
producto2, _ = Producto.objects.get_or_create(
    nombre="Producto Test 2",
    defaults={
        "proveedor": proveedor,
        "precio_compra": Decimal("130.00"),
        "precio_venta": Decimal("185.00")
    }
)

# Agregar detalles a la factura
DetalleFactura.objects.create(
    factura=factura,
    producto=producto1,
    cantidad=5,
    precio_unitario=Decimal("150.00"),  # 5 × $150 = $750
    precio_compra=Decimal("100.00")     # Costo: 5 × $100 = $500
)

DetalleFactura.objects.create(
    factura=factura,
    producto=producto2,
    cantidad=10,
    precio_unitario=Decimal("125.00"),  # 10 × $125 = $1,250
    precio_compra=Decimal("65.00")      # Costo: 10 × $65 = $650
)

print(f"    2 productos agregados")
print()

# Recalcular total
factura.calcular_total()
factura.refresh_from_db()

print("="*80)
print(" ANÁLISIS DE LA FACTURA")
print("="*80)
print()
print(f"Folio: {factura.folio_factura}")
print(f"Total factura: ${factura.total:,.2f}")
print(f"Costo total: ${factura.costo_total:,.2f} ({factura.porcentaje_costo * 100:.1f}%)")
print(f"Ganancia total: ${factura.ganancia_total:,.2f} ({factura.porcentaje_ganancia * 100:.1f}%)")
print()

# Crear pagos parciales
print("="*80)
print(" REGISTRANDO PAGOS PARCIALES")
print("="*80)
print()

# Pago 1: $800
print("[1] Primer pago: $800.00")
pago1 = PagoFactura.objects.create(
    factura=factura,
    fecha_pago=date.today() - timedelta(days=5),
    monto=Decimal("800.00"),
    metodo_pago="transferencia",
    referencia="TRANS-001",
    notas="Primer pago parcial"
)
factura.refresh_from_db()

print(f"    Total pagado: ${factura.total_pagado:,.2f}")
print(f"    Saldo pendiente: ${factura.saldo_pendiente:,.2f}")
print(f"    Estado: {factura.estado_pago}")
print()
print(f"    Distribucion del pago:")
print(f"      Para proveedores: ${pago1.monto_costo:,.2f}")
print(f"      Ganancia: ${pago1.monto_ganancia:,.2f}")
print()

# Pago 2: $500
print("[2] Segundo pago: $500.00")
pago2 = PagoFactura.objects.create(
    factura=factura,
    fecha_pago=date.today() - timedelta(days=2),
    monto=Decimal("500.00"),
    metodo_pago="efectivo",
    notas="Segundo pago parcial"
)
factura.refresh_from_db()

print(f"    Total pagado: ${factura.total_pagado:,.2f}")
print(f"    Saldo pendiente: ${factura.saldo_pendiente:,.2f}")
print(f"    Estado: {factura.estado_pago}")
print()
print(f"    Distribucion del pago:")
print(f"      Para proveedores: ${pago2.monto_costo:,.2f}")
print(f"      Ganancia: ${pago2.monto_ganancia:,.2f}")
print()

# Resumen acumulado
print("="*80)
print(" RESUMEN ACUMULADO")
print("="*80)
print()
print(f"Total factura: ${factura.total:,.2f}")
print()
print(f"PAGOS RECIBIDOS:")
print(f"  Total pagado: ${factura.total_pagado:,.2f}")
print(f"  Para proveedores (comprometido): ${factura.costo_pagado:,.2f}")
print(f"  Ganancia realizada (disponible): ${factura.ganancia_pagada:,.2f}")
print()
print(f"PENDIENTE POR COBRAR:")
print(f"  Saldo pendiente: ${factura.saldo_pendiente:,.2f}")
print(f"  Para proveedores: ${factura.costo_pendiente:,.2f}")
print(f"  Ganancia por recibir: ${factura.ganancia_pendiente:,.2f}")
print()

# Pago 3: Completar pago
print("[3] Tercer pago (completa la factura): $700.00")
pago3 = PagoFactura.objects.create(
    factura=factura,
    fecha_pago=date.today(),
    monto=Decimal("700.00"),
    metodo_pago="cheque",
    referencia="CHQ-123",
    notas="Pago final"
)
factura.refresh_from_db()

print(f"    Total pagado: ${factura.total_pagado:,.2f}")
print(f"    Saldo pendiente: ${factura.saldo_pendiente:,.2f}")
print(f"    Estado: {factura.estado_pago}")
print(f"    Pagado (campo booleano): {factura.pagado}")
print()

# Verificaciones
print("="*80)
print(" VERIFICACIONES")
print("="*80)
print()

checks = [
    ("Suma de pagos = Total factura", factura.total_pagado == factura.total),
    ("Saldo pendiente = 0", factura.saldo_pendiente == 0),
    ("Estado = pagada", factura.estado_pago == "pagada"),
    ("Campo pagado = True", factura.pagado == True),
    ("Número de pagos = 3", factura.pagos.count() == 3),
]

all_pass = True
for check_name, result in checks:
    status = "[OK]" if result else "[FALLO]"
    print(f"  {status} {check_name}")
    if not result:
        all_pass = False

print()

if all_pass:
    print("[EXITO] Todas las verificaciones pasaron")
else:
    print("[FALLO] Algunas verificaciones fallaron")

print()
print("="*80)
print(" INSTRUCCIONES PARA VERIFICAR EN EL ADMIN")
print("="*80)
print()
print("1. Ir a: http://localhost:8000/admin/ventas/factura/")
print()
print("2. Buscar la factura: TEST-PP-001")
print()
print("3. Verificar en el listado:")
print("   - Total: $2,000.00")
print("   - Pagado: $2,000.00 (verde)")
print("   - Saldo: $0.00 (verde)")
print("   - Estado: PAGADA (badge verde)")
print()
print("4. Click en la factura para ver detalle:")
print("   - Ver 'Información de Pagos' con distribución completa")
print("   - Ver tabla de 'Pagos de Facturas' con 3 pagos")
print("   - Cada pago muestra 'Costo' y 'Ganancia'")
print()
print("5. Para probar pago parcial, crear nueva factura y registrar solo")
print("   parte del total para ver estado 'PARCIAL'")
print()
print("="*80)
print()
print("[LIMPIEZA]")
print("Para eliminar esta factura de prueba:")
print("Factura.objects.filter(folio_factura='TEST-PP-001').delete()")
print()
