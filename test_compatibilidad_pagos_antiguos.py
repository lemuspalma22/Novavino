"""
Test de compatibilidad con sistema de pagos antiguo.
Verifica que facturas marcadas como pagado=True se muestren correctamente.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from decimal import Decimal

print("="*80)
print(" TEST: COMPATIBILIDAD CON PAGOS ANTIGUOS")
print("="*80)
print()

# Buscar facturas pagadas con el sistema antiguo (pagado=True, sin pagos en PagoFactura)
facturas_antiguas = Factura.objects.filter(
    pagado=True
).prefetch_related('pagos')[:10]

print(f"Encontradas {facturas_antiguas.count()} facturas marcadas como pagadas")
print()

for i, factura in enumerate(facturas_antiguas, 1):
    num_pagos = factura.pagos.count()
    
    print(f"[{i}] Factura {factura.folio_factura}")
    print(f"    Cliente: {factura.cliente}")
    print(f"    Total: ${factura.total:,.2f}")
    print(f"    Pagado (campo): {factura.pagado}")
    print(f"    Fecha pago: {factura.fecha_pago or 'N/A'}")
    print(f"    Pagos registrados: {num_pagos}")
    print()
    
    # Verificar propiedades calculadas
    print(f"    PROPIEDADES:")
    print(f"      total_pagado: ${factura.total_pagado:,.2f}")
    print(f"      saldo_pendiente: ${factura.saldo_pendiente:,.2f}")
    print(f"      estado_pago: {factura.estado_pago}")
    print()
    
    # Verificación
    if num_pagos == 0:
        # Sistema antiguo
        checks = [
            ("Estado = pagada", factura.estado_pago == "pagada"),
            ("Total pagado = Total", factura.total_pagado == factura.total),
            ("Saldo = 0", factura.saldo_pendiente == 0),
        ]
        
        print("    VERIFICACIONES (sistema antiguo):")
        for check_name, result in checks:
            status = "[OK]" if result else "[FALLO]"
            print(f"      {status} {check_name}")
        print()
        
        if not all(c[1] for c in checks):
            print("    [!] PROBLEMA DETECTADO")
        else:
            print("    [V] TODO CORRECTO")
    else:
        # Sistema nuevo
        print("    [i] Esta factura usa el sistema NUEVO (tiene pagos registrados)")
    
    print("-" * 80)
    print()

print("="*80)
print(" RESUMEN")
print("="*80)
print()
print("Si ves '[OK]' en todas las verificaciones, el sistema de compatibilidad")
print("funciona correctamente y las facturas antiguas se mostrarán como 'PAGADA'")
print("en el admin de Django.")
print()
