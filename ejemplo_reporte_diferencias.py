"""
Ejemplo: Reporte mensual de diferencias por redondeo
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura
from decimal import Decimal
from datetime import datetime

def reporte_diferencias_redondeo(mes, año):
    """
    Muestra diferencias acumuladas entre total facturado y suma de productos.
    Útil para contabilidad mensual.
    """
    facturas = Factura.objects.filter(
        fecha_facturacion__month=mes,
        fecha_facturacion__year=año
    )
    
    print(f"=== REPORTE DE DIFERENCIAS POR REDONDEO ===")
    print(f"Período: {mes}/{año}\n")
    
    total_diferencias = Decimal("0")
    facturas_con_diferencia = 0
    
    for factura in facturas:
        if factura.detalles.count() == 0:
            continue
            
        suma_detalles = sum(
            det.cantidad * det.precio_unitario 
            for det in factura.detalles.all()
        )
        
        diferencia = factura.total - suma_detalles
        
        # Solo reportar si diferencia > 1 centavo
        if abs(diferencia) > Decimal("0.01"):
            facturas_con_diferencia += 1
            total_diferencias += diferencia
            
            signo = "+" if diferencia > 0 else ""
            print(f"Factura {factura.folio_factura}:")
            print(f"  Total facturado: ${factura.total:,.2f}")
            print(f"  Suma productos:  ${suma_detalles:,.2f}")
            print(f"  Diferencia:      {signo}${diferencia:,.2f}")
            print()
    
    print(f"=== RESUMEN ===")
    print(f"Facturas con diferencia: {facturas_con_diferencia}")
    print(f"Diferencia neta total:   ${total_diferencias:,.2f}")
    
    if abs(total_diferencias) < Decimal("1.00"):
        print(f"\n[OK] Diferencia neta insignificante (< $1.00)")
    
    print(f"\n=== REGISTRO CONTABLE SUGERIDO ===")
    if total_diferencias > 0:
        print(f"Cargo:  Caja/Bancos          ${total_diferencias:,.2f}")
        print(f"Abono:  Otros Ingresos       ${total_diferencias:,.2f}")
        print(f"        (Ajustes por redondeo)")
    elif total_diferencias < 0:
        print(f"Cargo:  Gastos - Ajustes     ${abs(total_diferencias):,.2f}")
        print(f"Abono:  Caja/Bancos          ${abs(total_diferencias):,.2f}")
        print(f"        (Ajustes por redondeo)")
    else:
        print(f"[OK] No se requiere póliza (diferencia = $0.00)")

# Ejemplo de uso
if __name__ == "__main__":
    # Reportar diciembre 2025
    reporte_diferencias_redondeo(12, 2025)
