"""
Analizar diferencias entre total de factura y suma de detalles en todas las facturas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura, DetalleFactura
from decimal import Decimal

print("=== ANALISIS DE DIFERENCIAS EN TOTALES ===\n")

facturas = Factura.objects.all().order_by('folio_factura')
total_facturas = facturas.count()
facturas_con_diferencia = 0
diferencias = []

for factura in facturas:
    num_detalles = factura.detalles.count()
    
    # Solo analizar facturas CON detalles
    if num_detalles == 0:
        continue
    
    suma_detalles = sum(
        det.cantidad * det.precio_unitario 
        for det in factura.detalles.all()
    )
    
    diferencia = abs(factura.total - suma_detalles)
    
    if diferencia > Decimal("0.01"):  # Más de 1 centavo
        facturas_con_diferencia += 1
        diferencias.append({
            'folio': factura.folio_factura,
            'total': factura.total,
            'suma': suma_detalles,
            'diferencia': diferencia,
            'num_detalles': num_detalles
        })

print(f"Total facturas analizadas: {total_facturas}")
print(f"Facturas con diferencia > $0.01: {facturas_con_diferencia}")

if facturas_con_diferencia > 0:
    print(f"\n=== DETALLE DE DIFERENCIAS ===\n")
    
    # Ordenar por diferencia (mayor primero)
    diferencias.sort(key=lambda x: x['diferencia'], reverse=True)
    
    for d in diferencias[:10]:  # Mostrar las 10 mayores
        print(f"Factura {d['folio']}:")
        print(f"  Total guardado: ${d['total']:,.2f}")
        print(f"  Suma detalles:  ${d['suma']:,.2f}")
        print(f"  Diferencia:     ${d['diferencia']:,.2f}")
        print(f"  Núm. productos: {d['num_detalles']}")
        print()
    
    # Estadísticas
    diferencias_valores = [d['diferencia'] for d in diferencias]
    max_dif = max(diferencias_valores)
    min_dif = min(diferencias_valores)
    avg_dif = sum(diferencias_valores) / len(diferencias_valores)
    
    print(f"=== ESTADISTICAS ===")
    print(f"Diferencia máxima: ${max_dif:,.2f}")
    print(f"Diferencia mínima: ${min_dif:,.2f}")
    print(f"Diferencia promedio: ${avg_dif:,.2f}")
    
    # Contar por rango
    menores_10_centavos = sum(1 for d in diferencias_valores if d < Decimal("0.10"))
    entre_10_50_centavos = sum(1 for d in diferencias_valores if Decimal("0.10") <= d < Decimal("0.50"))
    mayores_50_centavos = sum(1 for d in diferencias_valores if d >= Decimal("0.50"))
    
    print(f"\nDistribución:")
    print(f"  < $0.10:        {menores_10_centavos} facturas")
    print(f"  $0.10 - $0.50:  {entre_10_50_centavos} facturas")
    print(f"  >= $0.50:       {mayores_50_centavos} facturas")
    
else:
    print("\n[OK] No hay facturas con diferencias significativas")
