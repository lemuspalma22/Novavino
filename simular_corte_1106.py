"""
Simulación: Corte de caja con y sin fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from decimal import Decimal

print("="*70)
print(" SIMULACIÓN: CORTE DE CAJA DEL 09/12/2025")
print("="*70)

# Obtener factura 1106
try:
    factura = Factura.objects.get(folio_factura="1106")
    
    # Calcular valores
    total_guardado = factura.total
    suma_detalles = sum(d.cantidad * d.precio_unitario for d in factura.detalles.all())
    total_pdf_real = Decimal("14651.08")  # Del CFDI
    
    print("\n--- SITUACIÓN ACTUAL (Sin Fix) ---")
    print(f"Cliente pagó (según CFDI):          ${total_pdf_real:,.2f}")
    print(f"Sistema registró (total guardado):  ${total_guardado:,.2f}")
    print(f"Suma de productos en detalles:      ${suma_detalles:,.2f}")
    print(f"\nDiferencia en caja:")
    print(f"  Dinero real:                      ${total_pdf_real:,.2f}")
    print(f"  Dinero esperado por sistema:      ${total_guardado:,.2f}")
    print(f"  ¿Sobra o falta?                   ${(total_pdf_real - total_guardado):,.2f}")
    
    if abs(total_pdf_real - total_guardado) > Decimal("0.01"):
        print(f"\n  [!] PROBLEMA: Hay ${abs(total_pdf_real - total_guardado):,.2f} no explicados")
    else:
        print(f"\n  [OK] Caja cuadra")
    
    print("\n" + "-"*70)
    print("\n--- CON FIX PROPUESTO ---")
    print(f"Cliente pagó (según CFDI):          ${total_pdf_real:,.2f}")
    print(f"Sistema registraría:                ${total_pdf_real:,.2f}")
    print(f"Suma de productos en detalles:      ${suma_detalles:,.2f}")
    print(f"\nDiferencia en caja:")
    print(f"  Dinero real:                      ${total_pdf_real:,.2f}")
    print(f"  Dinero esperado por sistema:      ${total_pdf_real:,.2f}")
    print(f"  ¿Sobra o falta?                   $0.00")
    print(f"\n  [OK] CAJA CUADRA PERFECTO")
    
    print(f"\nDiferencia de redondeo (interna):")
    diferencia_redondeo = total_pdf_real - suma_detalles
    print(f"  Total facturado:                  ${total_pdf_real:,.2f}")
    print(f"  Suma de productos:                ${suma_detalles:,.2f}")
    print(f"  Diferencia por redondeo:          ${diferencia_redondeo:,.2f}")
    
    print(f"\n  [*] Esta diferencia se reporta al contador como:")
    if diferencia_redondeo > 0:
        print(f"     'Otros Ingresos - Ajuste Redondeo: +${diferencia_redondeo:,.2f}'")
    else:
        print(f"     'Gastos - Ajuste Redondeo: ${abs(diferencia_redondeo):,.2f}'")
    
    print("\n" + "="*70)
    print(" RECOMENDACIÓN")
    print("="*70)
    print("""
El fix propuesto:
[+] Hace que la caja cuadre con el dinero real
[+] El total coincide con el CFDI oficial
[+] Las diferencias de redondeo se reportan por separado

Sin el fix:
[-] La caja no cuadra con el dinero real
[-] Tienes "$0.15 fantasma" que no sabes de donde vienen
[-] Problema potencial en auditoria

Diferencia de redondeo de $0.15 es NORMAL y se maneja con:
- Reporte mensual de diferencias
- Poliza contable: "Ajustes por Redondeo"
- Tipicamente se compensan (unas +, otras -)
    """)
    
except Factura.DoesNotExist:
    print("Factura 1106 no encontrada")
