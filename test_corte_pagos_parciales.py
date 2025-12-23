"""
Test: Verificar que el corte de flujo incluye pagos parciales
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura, PagoFactura
from datetime import date, timedelta

print("="*80)
print(" TEST: Corte de Flujo con Pagos Parciales")
print("="*80)
print()

# Buscar factura VPG1125-03 o facturas con pagos parciales
facturas_con_pagos_parciales = []

print("Buscando facturas con pagos parciales...")
print("-" * 80)

for factura in Factura.objects.all()[:50]:  # Revisar primeras 50
    pagos = PagoFactura.objects.filter(factura=factura)
    num_pagos = pagos.count()
    
    if num_pagos > 0:
        total_pagado = sum(p.monto for p in pagos)
        
        if num_pagos > 1 or (total_pagado < factura.total and total_pagado > 0):
            facturas_con_pagos_parciales.append({
                'factura': factura,
                'pagos': list(pagos),
                'total_pagado': total_pagado
            })
            
            print(f"\n[ENCONTRADA] {factura.folio_factura}")
            print(f"  Cliente: {factura.cliente}")
            print(f"  Total factura: ${factura.total:,.2f}")
            print(f"  Total pagado: ${total_pagado:,.2f}")
            print(f"  Saldo: ${factura.total - total_pagado:,.2f}")
            print(f"  Numero de pagos: {num_pagos}")
            print(f"  Pagos:")
            for pago in pagos:
                print(f"    - {pago.fecha_pago}: ${pago.monto:,.2f} ({pago.metodo_pago})")

print()
print("="*80)
print(f" RESUMEN: {len(facturas_con_pagos_parciales)} facturas con pagos parciales encontradas")
print("="*80)
print()

# Test específico: Verificar que el nuevo sistema las incluye
if facturas_con_pagos_parciales:
    print("TEST: Verificar inclusión en corte de flujo")
    print("-" * 80)
    
    caso = facturas_con_pagos_parciales[0]
    factura = caso['factura']
    pagos = caso['pagos']
    
    print(f"\nFactura de prueba: {factura.folio_factura}")
    print(f"Pagos registrados:")
    
    for pago in pagos:
        print(f"  {pago.fecha_pago}: ${pago.monto:,.2f}")
    
    # Simular periodo que incluya algún pago
    if pagos:
        fecha_pago_ejemplo = pagos[0].fecha_pago
        fecha_inicio = fecha_pago_ejemplo - timedelta(days=7)
        fecha_fin = fecha_pago_ejemplo + timedelta(days=7)
        
        print(f"\nPeriodo de prueba: {fecha_inicio} a {fecha_fin}")
        
        # Verificar filtrado nuevo
        from utils.reportes import calcular_agregados_periodo_ventas
        
        agregados = calcular_agregados_periodo_ventas(
            Factura.objects.all(),
            fecha_inicio,
            fecha_fin,
            campo_fecha='fecha_pago',
            solo_pagadas=False
        )
        
        facturas_en_periodo = list(agregados['queryset'])
        folios = [f.folio_factura for f in facturas_en_periodo]
        
        print(f"\nFacturas en el periodo: {len(facturas_en_periodo)}")
        
        if factura.folio_factura in folios:
            print(f"[OK] Factura {factura.folio_factura} incluida en el corte")
            
            # Calcular pagos en el periodo
            pagos_periodo = [p for p in pagos if fecha_inicio <= p.fecha_pago <= fecha_fin]
            total_pagos_periodo = sum(p.monto for p in pagos_periodo)
            
            print(f"[OK] Pagos en el periodo: {len(pagos_periodo)}")
            print(f"[OK] Monto en el periodo: ${total_pagos_periodo:,.2f}")
        else:
            print(f"[ERROR] Factura {factura.folio_factura} NO incluida en el corte")
            print(f"        Folios en periodo: {folios}")
else:
    print("[INFO] No hay facturas con pagos parciales para probar")

print()
print("="*80)
print()
print("INSTRUCCIONES:")
print("1. Inicia el servidor: python manage.py runserver")
print("2. Ve a: Admin > Corte Semanal")
print("3. Selecciona modo 'Flujo (por fecha de pago)'")
print("4. Elige un periodo que incluya pagos parciales")
print("5. Genera el reporte")
print("6. Verifica que aparezcan facturas con pagos parciales")
print("7. Prueba los checkboxes:")
print("   - Desactiva algunas facturas")
print("   - Los totales deben recalcularse automáticamente")
print("   - El checkbox del encabezado selecciona/deselecciona todo")
print()
print("="*80)
