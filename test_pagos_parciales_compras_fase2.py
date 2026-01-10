"""
Test de FASE 2: Pagos Parciales en Compras
Verifica que las propiedades calculadas funcionan correctamente.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, PagoCompra, Proveedor
from decimal import Decimal
from datetime import date, timedelta

print("="*80)
print(" TEST: FASE 2 - PAGOS PARCIALES EN COMPRAS")
print("="*80)
print()

# Buscar una compra sin pagos para probar
compra = Compra.objects.filter(pagado=False).first()

if not compra:
    print("[INFO] No hay compras pendientes. Verificando compras pagadas con sistema antiguo...")
    compra = Compra.objects.filter(pagado=True).first()

if not compra:
    print("[ERROR] No hay compras en la base de datos para probar")
    exit(1)

print(f"Compra seleccionada: {compra.folio}")
print(f"Proveedor: {compra.proveedor}")
print(f"Total: ${compra.total:,.2f}")
print(f"Pagado (campo): {compra.pagado}")
print()

print("="*80)
print(" ESTADO INICIAL")
print("="*80)
print()

print(f"Total pagado: ${compra.total_pagado:,.2f}")
print(f"Saldo pendiente: ${compra.saldo_pendiente:,.2f}")
print(f"Estado pago: {compra.estado_pago}")
print(f"Pagos registrados: {compra.pagos.count()}")
print()

# Si ya está pagada con el sistema antiguo, verificar compatibilidad
if compra.pagado and compra.pagos.count() == 0:
    print("="*80)
    print(" VERIFICACION DE COMPATIBILIDAD")
    print("="*80)
    print()
    print("[INFO] Esta compra usa el sistema ANTIGUO (pagado=True sin pagos)")
    print()
    
    checks = [
        ("Estado = pagada", compra.estado_pago == "pagada"),
        ("Total pagado = Total", compra.total_pagado == compra.total),
        ("Saldo = 0", compra.saldo_pendiente == 0),
    ]
    
    print("VERIFICACIONES:")
    for check_name, result in checks:
        status = "[OK]" if result else "[FALLO]"
        print(f"  {status} {check_name}")
    
    print()
    if all(c[1] for c in checks):
        print("[EXITO] Compatibilidad con sistema antiguo funciona correctamente")
    else:
        print("[FALLO] Hay problemas con la compatibilidad")
    
else:
    # Crear un pago parcial de prueba
    print("="*80)
    print(" CREANDO PAGO PARCIAL DE PRUEBA")
    print("="*80)
    print()
    
    # Calcular monto del pago (50% del total)
    monto_pago = (compra.total * Decimal("0.5")).quantize(Decimal("0.01"))
    
    print(f"Creando pago de ${monto_pago:,.2f} (50% del total)")
    
    pago = PagoCompra.objects.create(
        compra=compra,
        fecha_pago=date.today(),
        monto=monto_pago,
        metodo_pago='transferencia',
        referencia='TEST-001',
        notas='Pago parcial de prueba'
    )
    
    # Refrescar la compra
    compra.refresh_from_db()
    
    print()
    print("DESPUES DEL PAGO:")
    print(f"  Total pagado: ${compra.total_pagado:,.2f}")
    print(f"  Saldo pendiente: ${compra.saldo_pendiente:,.2f}")
    print(f"  Estado: {compra.estado_pago}")
    print()
    
    # Verificar
    checks = [
        ("Total pagado = Monto pago", compra.total_pagado == monto_pago),
        ("Saldo = Total - Pagado", compra.saldo_pendiente == compra.total - monto_pago),
        ("Estado = parcial", compra.estado_pago == "parcial"),
    ]
    
    print("VERIFICACIONES:")
    for check_name, result in checks:
        status = "[OK]" if result else "[FALLO]"
        print(f"  {status} {check_name}")
    
    print()
    
    # Crear segundo pago para completar
    print("="*80)
    print(" COMPLETANDO EL PAGO")
    print("="*80)
    print()
    
    saldo_restante = compra.saldo_pendiente
    print(f"Creando pago de ${saldo_restante:,.2f} (saldo restante)")
    
    pago2 = PagoCompra.objects.create(
        compra=compra,
        fecha_pago=date.today() + timedelta(days=1),
        monto=saldo_restante,
        metodo_pago='efectivo',
        notas='Pago final de prueba'
    )
    
    # Refrescar
    compra.refresh_from_db()
    
    print()
    print("DESPUES DEL PAGO FINAL:")
    print(f"  Total pagado: ${compra.total_pagado:,.2f}")
    print(f"  Saldo pendiente: ${compra.saldo_pendiente:,.2f}")
    print(f"  Estado: {compra.estado_pago}")
    print(f"  Pagado (campo): {compra.pagado}")
    print()
    
    # Verificar
    checks2 = [
        ("Total pagado = Total compra", compra.total_pagado == compra.total),
        ("Saldo = 0", compra.saldo_pendiente == 0),
        ("Estado = pagada", compra.estado_pago == "pagada"),
        ("Campo pagado = True", compra.pagado == True),
    ]
    
    print("VERIFICACIONES FINALES:")
    for check_name, result in checks2:
        status = "[OK]" if result else "[FALLO]"
        print(f"  {status} {check_name}")
    
    print()
    
    if all(c[1] for c in checks) and all(c[1] for c in checks2):
        print("[EXITO] Todas las verificaciones pasaron")
    else:
        print("[FALLO] Algunas verificaciones fallaron")
    
    print()
    print("[LIMPIEZA]")
    print("Los pagos de prueba fueron creados. Para eliminarlos:")
    print(f"PagoCompra.objects.filter(compra__folio='{compra.folio}', notas__contains='prueba').delete()")

print()
print("="*80)
print(" INSTRUCCIONES PARA VERIFICAR EN EL ADMIN")
print("="*80)
print()
print("1. Ir a: http://localhost:8000/admin/compras/compra/")
print()
print(f"2. Buscar la compra: {compra.folio}")
print()
print("3. Verificar en el listado:")
print("   - Total: muestra el total de la compra")
print("   - Pagado: muestra el total pagado (rojo)")
print("   - Por Pagar: muestra el saldo (verde)")
print("   - Estado Pago: badge con color")
print()
print("4. Click en la compra para ver detalle:")
print("   - Ver 'Informacion de Pagos a Proveedor'")
print("   - Ver tabla de 'Pagos de Compras'")
print()
print("="*80)
print()
