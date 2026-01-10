"""
Comando para generar reporte mensual de diferencias por redondeo entre
total facturado (CFDI) y suma de productos.

Uso:
    python manage.py reporte_diferencias_redondeo --mes 12 --año 2025
    python manage.py reporte_diferencias_redondeo  (mes actual)
"""
from django.core.management.base import BaseCommand
from ventas.models import Factura
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = 'Genera reporte mensual de diferencias por redondeo en facturas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mes',
            type=int,
            help='Mes (1-12). Por defecto: mes actual'
        )
        parser.add_argument(
            '--año',
            type=int,
            help='Año (ej: 2025). Por defecto: año actual'
        )
        parser.add_argument(
            '--mostrar-todas',
            action='store_true',
            help='Mostrar todas las facturas, incluso sin diferencias'
        )

    def handle(self, *args, **options):
        # Obtener mes y año
        mes = options['mes'] or datetime.now().month
        año = options['año'] or datetime.now().year
        mostrar_todas = options['mostrar_todas']
        
        self.stdout.write("=" * 70)
        self.stdout.write(f" REPORTE DE DIFERENCIAS POR REDONDEO")
        self.stdout.write(f" Período: {mes:02d}/{año}")
        self.stdout.write("=" * 70)
        self.stdout.write("")
        
        # Obtener facturas del mes
        facturas = Factura.objects.filter(
            fecha_facturacion__month=mes,
            fecha_facturacion__year=año
        ).order_by('folio_factura')
        
        total_facturas = facturas.count()
        if total_facturas == 0:
            self.stdout.write(self.style.WARNING(f"No hay facturas en {mes:02d}/{año}"))
            return
        
        total_diferencias = Decimal("0")
        facturas_con_diferencia = 0
        detalles_list = []
        
        for factura in facturas:
            num_detalles = factura.detalles.count()
            
            # Ignorar facturas sin detalles
            if num_detalles == 0:
                continue
            
            # Calcular suma de detalles
            suma_detalles = sum(
                det.cantidad * det.precio_unitario 
                for det in factura.detalles.all()
            )
            
            diferencia = factura.total - suma_detalles
            
            # Decidir si mostrar
            tiene_diferencia = abs(diferencia) > Decimal("0.01")
            if tiene_diferencia or mostrar_todas:
                if tiene_diferencia:
                    facturas_con_diferencia += 1
                    total_diferencias += diferencia
                
                signo = "+" if diferencia > 0 else ""
                status = "[!]" if tiene_diferencia else "[OK]"
                
                detalles_list.append({
                    'folio': factura.folio_factura,
                    'total': factura.total,
                    'suma': suma_detalles,
                    'diferencia': diferencia,
                    'tiene_diferencia': tiene_diferencia,
                    'signo': signo,
                    'status': status
                })
        
        # Mostrar detalles
        if detalles_list:
            self.stdout.write("Facturas:")
            self.stdout.write("-" * 70)
            for d in detalles_list:
                self.stdout.write(f"{d['status']} Factura {d['folio']:>8}")
                self.stdout.write(f"    Total facturado: ${d['total']:>12,.2f}")
                self.stdout.write(f"    Suma productos:  ${d['suma']:>12,.2f}")
                if d['tiene_diferencia']:
                    style = self.style.WARNING if abs(d['diferencia']) > Decimal("0.50") else self.style.SUCCESS
                    self.stdout.write(style(f"    Diferencia:      {d['signo']}${abs(d['diferencia']):>12,.2f}"))
                self.stdout.write("")
        
        # Resumen
        self.stdout.write("=" * 70)
        self.stdout.write(" RESUMEN")
        self.stdout.write("=" * 70)
        self.stdout.write(f"Total facturas analizadas:     {total_facturas}")
        self.stdout.write(f"Facturas con diferencia:       {facturas_con_diferencia}")
        self.stdout.write(f"Diferencia neta acumulada:     ${total_diferencias:,.2f}")
        
        # Evaluación
        self.stdout.write("")
        if facturas_con_diferencia == 0:
            self.stdout.write(self.style.SUCCESS("[OK] No hay diferencias significativas"))
        elif abs(total_diferencias) < Decimal("1.00"):
            self.stdout.write(self.style.SUCCESS(
                f"[OK] Diferencia neta insignificante (< $1.00)"
            ))
        elif abs(total_diferencias) < Decimal("10.00"):
            self.stdout.write(self.style.WARNING(
                f"[*] Diferencia moderada. Revisar con contador."
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"[!] Diferencia significativa. Requiere revisión urgente."
            ))
        
        # Registro contable sugerido
        if abs(total_diferencias) > Decimal("0.01"):
            self.stdout.write("")
            self.stdout.write("=" * 70)
            self.stdout.write(" REGISTRO CONTABLE SUGERIDO")
            self.stdout.write("=" * 70)
            if total_diferencias > 0:
                self.stdout.write(f"Cargo:  Caja/Bancos                ${total_diferencias:,.2f}")
                self.stdout.write(f"Abono:  Otros Ingresos - Redondeo  ${total_diferencias:,.2f}")
                self.stdout.write("        (Diferencias por redondeo fiscal)")
            else:
                self.stdout.write(f"Cargo:  Gastos - Ajuste Redondeo   ${abs(total_diferencias):,.2f}")
                self.stdout.write(f"Abono:  Caja/Bancos                ${abs(total_diferencias):,.2f}")
                self.stdout.write("        (Diferencias por redondeo fiscal)")
