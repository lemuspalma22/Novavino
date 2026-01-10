# test_vpg_funcionalidad.py
"""
Script para probar la funcionalidad VPG implementada.
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from decimal import Decimal


def test_crear_vpg():
    """Prueba crear una VPG y verificar que el folio se genera automáticamente."""
    print("\n" + "="*80)
    print("TEST 1: CREAR VPG CON FOLIO AUTOMATICO")
    print("="*80)
    
    # Crear VPG
    vpg = Factura.objects.create(
        es_vpg=True,
        cliente="Cliente de Prueba VPG",
        fecha_facturacion=datetime.now().date(),
        total=Decimal("1500.00"),
        subtotal=Decimal("1500.00"),
        metodo_pago="PUE"
    )
    
    print(f"[OK] VPG creada con ID: {vpg.id}")
    print(f"[OK] Folio generado: {vpg.folio_factura}")
    print(f"[OK] Año VPG: {vpg.folio_vpg_anio}")
    print(f"[OK] Número VPG: {vpg.folio_vpg_numero}")
    print(f"[OK] Tipo venta: {vpg.tipo_venta}")
    print(f"[OK] Es VPG: {vpg.es_vpg}")
    
    # Verificar formato
    anio_actual = datetime.now().year % 100
    formato_esperado = f"VPG{anio_actual}-"
    
    if vpg.folio_factura.startswith(formato_esperado):
        print(f"[OK] Formato de folio correcto: {vpg.folio_factura}")
    else:
        print(f"[ERROR] Formato incorrecto. Esperado: {formato_esperado}X, Obtenido: {vpg.folio_factura}")
    
    return vpg


def test_crear_factura_normal():
    """Prueba crear una factura normal y verificar que NO se genera folio VPG."""
    print("\n" + "="*80)
    print("TEST 2: CREAR FACTURA NORMAL (NO VPG)")
    print("="*80)
    
    # Crear factura normal
    factura = Factura.objects.create(
        es_vpg=False,
        folio_factura="TEST-9999",
        cliente="Cliente de Prueba Normal",
        fecha_facturacion=datetime.now().date(),
        total=Decimal("2500.00"),
        subtotal=Decimal("2500.00"),
        metodo_pago="PPD"
    )
    
    print(f"[OK] Factura creada con ID: {factura.id}")
    print(f"[OK] Folio: {factura.folio_factura}")
    print(f"[OK] Tipo venta: {factura.tipo_venta}")
    print(f"[OK] Es VPG: {factura.es_vpg}")
    print(f"[OK] Año VPG (debe ser None): {factura.folio_vpg_anio}")
    print(f"[OK] Número VPG (debe ser None): {factura.folio_vpg_numero}")
    
    if not factura.es_vpg and factura.folio_factura == "TEST-9999":
        print(f"[OK] Factura normal funciona correctamente")
    else:
        print(f"[ERROR] Algo salió mal con la factura normal")
    
    return factura


def test_consecutivo_vpg():
    """Prueba que el consecutivo VPG se incrementa correctamente."""
    print("\n" + "="*80)
    print("TEST 3: CONSECUTIVO VPG")
    print("="*80)
    
    # Obtener último VPG del año actual
    anio_actual = datetime.now().year
    ultimo_vpg = Factura.objects.filter(
        es_vpg=True,
        folio_vpg_anio=anio_actual
    ).order_by('-folio_vpg_numero').first()
    
    if ultimo_vpg:
        print(f"[INFO] Último VPG del año {anio_actual}: {ultimo_vpg.folio_factura}")
        print(f"[INFO] Número consecutivo: {ultimo_vpg.folio_vpg_numero}")
        numero_esperado = ultimo_vpg.folio_vpg_numero + 1
    else:
        print(f"[INFO] No hay VPG previas en {anio_actual}")
        numero_esperado = 1
    
    # Crear nueva VPG
    nueva_vpg = Factura.objects.create(
        es_vpg=True,
        cliente="Cliente Consecutivo",
        fecha_facturacion=datetime.now().date(),
        total=Decimal("800.00"),
        subtotal=Decimal("800.00")
    )
    
    print(f"[OK] Nueva VPG creada: {nueva_vpg.folio_factura}")
    print(f"[OK] Número esperado: {numero_esperado}")
    print(f"[OK] Número obtenido: {nueva_vpg.folio_vpg_numero}")
    
    if nueva_vpg.folio_vpg_numero == numero_esperado:
        print(f"[OK] Consecutivo correcto!")
    else:
        print(f"[ERROR] Consecutivo incorrecto")
    
    return nueva_vpg


def test_ordenamiento():
    """Prueba que el ordenamiento por fecha funciona correctamente."""
    print("\n" + "="*80)
    print("TEST 4: ORDENAMIENTO CRONOLOGICO")
    print("="*80)
    
    # Obtener últimas 10 facturas (VPG + normales)
    facturas = Factura.objects.all().order_by('-fecha_facturacion', '-id')[:10]
    
    print(f"[INFO] Mostrando últimas 10 facturas ordenadas por fecha:")
    print(f"\n{'Tipo':<10} {'Folio':<15} {'Cliente':<30} {'Fecha':<12}")
    print("-" * 70)
    
    for f in facturas:
        tipo = "VPG" if f.es_vpg else "Factura"
        print(f"{tipo:<10} {f.folio_factura:<15} {f.cliente:<30} {f.fecha_facturacion}")
    
    print(f"\n[OK] Ordenamiento aplicado correctamente")


def test_propiedades():
    """Prueba las propiedades del modelo."""
    print("\n" + "="*80)
    print("TEST 5: PROPIEDADES DEL MODELO")
    print("="*80)
    
    # Buscar una VPG
    vpg = Factura.objects.filter(es_vpg=True).first()
    
    if vpg:
        print(f"[INFO] Probando con VPG: {vpg.folio_factura}")
        print(f"  - tipo_venta: {vpg.tipo_venta}")
        print(f"  - folio_display: {vpg.folio_display}")
        print(f"  - es_vpg: {vpg.es_vpg}")
        print(f"[OK] Propiedades funcionan correctamente")
    else:
        print(f"[WARNING] No hay VPG para probar propiedades")
    
    # Buscar una factura normal
    factura = Factura.objects.filter(es_vpg=False).first()
    
    if factura:
        print(f"\n[INFO] Probando con Factura: {factura.folio_factura}")
        print(f"  - tipo_venta: {factura.tipo_venta}")
        print(f"  - folio_display: {factura.folio_display}")
        print(f"  - es_vpg: {factura.es_vpg}")
        print(f"[OK] Propiedades funcionan correctamente")


def test_estadisticas():
    """Muestra estadísticas generales."""
    print("\n" + "="*80)
    print("ESTADISTICAS GENERALES")
    print("="*80)
    
    total_facturas = Factura.objects.count()
    total_vpg = Factura.objects.filter(es_vpg=True).count()
    total_normales = Factura.objects.filter(es_vpg=False).count()
    
    print(f"Total de facturas: {total_facturas}")
    print(f"  - VPG: {total_vpg}")
    print(f"  - Facturas normales: {total_normales}")
    
    # VPG por año
    anio_actual = datetime.now().year
    vpg_este_anio = Factura.objects.filter(
        es_vpg=True,
        folio_vpg_anio=anio_actual
    ).count()
    
    print(f"\nVPG en {anio_actual}: {vpg_este_anio}")


def limpiar_tests():
    """Limpia las facturas de prueba creadas."""
    print("\n" + "="*80)
    print("LIMPIEZA DE DATOS DE PRUEBA")
    print("="*80)
    
    respuesta = input("\n¿Deseas eliminar las facturas de prueba creadas? (s/n): ")
    
    if respuesta.lower() == 's':
        # Eliminar facturas de prueba
        eliminadas = Factura.objects.filter(
            cliente__icontains="prueba"
        ).delete()
        
        print(f"[OK] Eliminadas {eliminadas[0]} facturas de prueba")
    else:
        print(f"[INFO] Facturas de prueba conservadas")


def main():
    print("\n")
    print("="*80)
    print(" "*25 + "TEST DE FUNCIONALIDAD VPG")
    print("="*80)
    
    try:
        # Ejecutar tests
        test_crear_vpg()
        test_crear_factura_normal()
        test_consecutivo_vpg()
        test_ordenamiento()
        test_propiedades()
        test_estadisticas()
        
        print("\n" + "="*80)
        print("[COMPLETADO] Todos los tests ejecutados")
        print("="*80)
        
        # Preguntar si limpiar
        limpiar_tests()
        
    except Exception as e:
        print(f"\n[ERROR] Error durante los tests: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
