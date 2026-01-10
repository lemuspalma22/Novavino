# test_flujo_completo_complementos.py
"""
Script para probar el flujo completo de Complementos de Pago.
Simula el proceso desde la creación de factura hasta la vinculación.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from datetime import date
from decimal import Decimal
from ventas.models import Factura, PagoFactura, ComplementoPago, DocumentoRelacionado


def test_1_verificar_facturas_ppd():
    """Test 1: Verificar si hay facturas PPD en el sistema."""
    print("\n" + "="*80)
    print("TEST 1: Verificar Facturas PPD en el Sistema")
    print("="*80)
    
    facturas_ppd = Factura.objects.filter(metodo_pago='PPD')
    count = facturas_ppd.count()
    
    if count == 0:
        print("[INFO] No hay facturas PPD en el sistema.")
        print("[TIP] Procesa facturas desde Drive primero:")
        print("      python process_drive_sales.py")
        return False
    
    print(f"[OK] Encontradas {count} facturas PPD:\n")
    
    for f in facturas_ppd[:5]:  # Mostrar máximo 5
        print(f"   - Factura {f.folio_factura}")
        print(f"     Cliente: {f.cliente}")
        print(f"     Total: ${f.total:,.2f}")
        print(f"     Estado: {f.estado_pago}")
        print(f"     Pagos registrados: {f.pagos.count()}")
        print()
    
    if count > 5:
        print(f"   ... y {count - 5} más")
    
    return True


def test_2_crear_pago_prueba():
    """Test 2: Crear un pago de prueba para factura PPD."""
    print("\n" + "="*80)
    print("TEST 2: Crear Pago de Prueba (Simula registro en Admin)")
    print("="*80)
    
    # Buscar una factura PPD sin pagos
    factura = Factura.objects.filter(
        metodo_pago='PPD',
        pagos__isnull=True
    ).first()
    
    if not factura:
        factura = Factura.objects.filter(metodo_pago='PPD').first()
    
    if not factura:
        print("[ERROR] No hay facturas PPD para probar")
        return False
    
    print(f"[INFO] Usando Factura {factura.folio_factura}")
    print(f"      Total: ${factura.total:,.2f}")
    print(f"      Cliente: {factura.cliente}")
    
    # Verificar si ya tiene pagos
    if factura.pagos.exists():
        print(f"\n[WARNING] Esta factura ya tiene {factura.pagos.count()} pago(s):")
        for p in factura.pagos.all():
            print(f"   - Pago #{p.id}: ${p.monto} el {p.fecha_pago}")
        
        respuesta = input("\n¿Crear otro pago de prueba? (s/n): ")
        if respuesta.lower() != 's':
            return True
    
    # Calcular monto sugerido
    saldo = factura.saldo_pendiente
    monto_sugerido = saldo / 2 if saldo > 100 else saldo
    
    print(f"\n[INFO] Saldo pendiente: ${saldo:,.2f}")
    print(f"[TIP] Monto sugerido: ${monto_sugerido:,.2f}")
    
    monto_input = input(f"\nMonto del pago (Enter para ${monto_sugerido:,.2f}): ")
    monto = Decimal(monto_input) if monto_input else monto_sugerido
    
    print(f"\n[ACTION] Creando PagoFactura de ${monto:,.2f}...")
    print("[NOTE] Esto debería enviar un email a contabilidad")
    print("       (Revisa la consola del servidor Django)")
    
    respuesta = input("\n¿Continuar? (s/n): ")
    if respuesta.lower() != 's':
        print("[SKIP] Pago no creado")
        return True
    
    try:
        pago = PagoFactura.objects.create(
            factura=factura,
            fecha_pago=date.today(),
            monto=monto,
            metodo_pago='transferencia',
            referencia='PRUEBA-TEST-COMPLEMENTOS',
            notas='Pago de prueba para testing de complementos'
        )
        
        print(f"\n[OK] PagoFactura #{pago.id} creado exitosamente")
        print(f"     Factura: {factura.folio_factura}")
        print(f"     Monto: ${pago.monto:,.2f}")
        print(f"     Fecha: {pago.fecha_pago}")
        print(f"\n[EMAIL] Si el servidor Django está corriendo, deberías ver:")
        print(f"        '[OK] Email enviado a contabilidad para factura PPD {factura.folio_factura}'")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] No se pudo crear el pago: {e}")
        return False


def test_3_verificar_complementos():
    """Test 3: Verificar complementos existentes."""
    print("\n" + "="*80)
    print("TEST 3: Verificar Complementos de Pago Existentes")
    print("="*80)
    
    complementos = ComplementoPago.objects.all()
    count = complementos.count()
    
    if count == 0:
        print("[INFO] No hay complementos en el sistema todavía.")
        print("[TIP] Para crear uno:")
        print("      1. Opción manual: /admin/ventas/complementopago/add/")
        print("      2. Opción programática: procesar_complemento_pdf('archivo.pdf')")
        return False
    
    print(f"[OK] Encontrados {count} complemento(s):\n")
    
    for comp in complementos:
        print(f"   Complemento {comp.folio_complemento}")
        print(f"   UUID: {comp.uuid_complemento}")
        print(f"   Cliente: {comp.cliente}")
        print(f"   Monto: ${comp.monto_total:,.2f}")
        print(f"   Fecha pago: {comp.fecha_pago}")
        
        # Documentos relacionados
        docs = comp.documentos_relacionados.all()
        print(f"   Facturas pagadas: {docs.count()}")
        
        for doc in docs:
            print(f"      - Factura {doc.factura.folio_factura}")
            print(f"        Importe: ${doc.importe_pagado:,.2f}")
            if doc.pago_factura:
                print(f"        [OK] Vinculado con PagoFactura #{doc.pago_factura.id}")
            else:
                print(f"        [WARNING] Sin vincular")
        
        if comp.requiere_revision:
            print(f"   [WARNING] Requiere revisión: {comp.motivo_revision}")
        
        print()
    
    return True


def test_4_estado_vinculacion():
    """Test 4: Verificar estado de vinculación."""
    print("\n" + "="*80)
    print("TEST 4: Estado de Vinculación Pagos vs Complementos")
    print("="*80)
    
    total_pagos = PagoFactura.objects.count()
    pagos_vinculados = PagoFactura.objects.filter(
        documento_relacionado__isnull=False
    ).count()
    pagos_sin_vincular = total_pagos - pagos_vinculados
    
    total_complementos = ComplementoPago.objects.count()
    
    print(f"[STATS] Pagos Registrados:")
    print(f"   Total: {total_pagos}")
    print(f"   Vinculados a complemento: {pagos_vinculados}")
    print(f"   Sin vincular: {pagos_sin_vincular}")
    
    print(f"\n[STATS] Complementos de Pago:")
    print(f"   Total: {total_complementos}")
    
    if pagos_sin_vincular > 0:
        print(f"\n[INFO] Hay {pagos_sin_vincular} pago(s) PPD sin complemento fiscal")
        print("[ACTION] El contador debe generar los complementos en el SAT")
    
    # Mostrar pagos sin vincular
    if pagos_sin_vincular > 0 and pagos_sin_vincular <= 10:
        print("\n[DETAIL] Pagos sin complemento:")
        pagos = PagoFactura.objects.filter(
            documento_relacionado__isnull=True,
            factura__metodo_pago='PPD'
        )
        
        for pago in pagos:
            print(f"   - Pago #{pago.id}")
            print(f"     Factura: {pago.factura.folio_factura}")
            print(f"     Monto: ${pago.monto:,.2f}")
            print(f"     Fecha: {pago.fecha_pago}")
    
    return True


def main():
    print("\n")
    print("="*80)
    print(" "*20 + "TEST FLUJO COMPLETO - COMPLEMENTOS DE PAGO")
    print("="*80)
    print("\n[INFO] Este script verifica el estado del sistema de complementos")
    print("[INFO] y te guía para probarlo paso a paso.\n")
    
    tests = [
        ("Verificar facturas PPD", test_1_verificar_facturas_ppd),
        ("Crear pago de prueba", test_2_crear_pago_prueba),
        ("Verificar complementos", test_3_verificar_complementos),
        ("Estado de vinculación", test_4_estado_vinculacion),
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"\n[ERROR] en {nombre}: {e}")
            import traceback
            traceback.print_exc()
            resultados.append((nombre, False))
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    
    for nombre, resultado in resultados:
        status = "[OK]" if resultado else "[SKIP/FAIL]"
        print(f"   {status} {nombre}")
    
    print("\n" + "="*80)
    print("\n[TIP] Para ver el sistema en acción:")
    print("   1. Corre el servidor: python manage.py runserver")
    print("   2. Ve al admin: http://localhost:8000/admin/")
    print("   3. Navega entre Facturas <-> Complementos usando los enlaces")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
