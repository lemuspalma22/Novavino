"""
Comando para probar la restauración de stock al eliminar facturas de ventas.
Ejecutar con: python manage.py test_stock_ventas
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from django.utils import timezone
from ventas.models import Factura, DetalleFactura
from inventario.models import Producto


class Command(BaseCommand):
    help = 'Prueba la restauración de stock al eliminar facturas de ventas'

    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write(self.style.SUCCESS("TEST: Restauración de Stock en Ventas"))
        self.stdout.write("="*80)
        
        # Buscar primer producto
        producto = Producto.objects.first()
        if not producto:
            self.stdout.write(self.style.ERROR("[X] No hay productos en la BD"))
            return
        
        self.stdout.write(f"\nProducto: {producto.nombre}")
        stock_inicial = producto.stock or 0
        self.stdout.write(f"Stock inicial: {stock_inicial}")
        
        # Crear venta
        cantidad = 2
        self.stdout.write(f"\n> Creando venta de {cantidad} unidades...")
        
        factura = Factura.objects.create(
            folio_factura=f"TEST-{int(timezone.now().timestamp())}",
            cliente="Test Cliente",
            fecha_facturacion=timezone.now().date()
        )
        
        DetalleFactura.objects.create(
            factura=factura,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio_venta or Decimal("100.00"),
            precio_compra=producto.precio_compra or Decimal("50.00")
        )
        
        producto.refresh_from_db()
        stock_despues_venta = producto.stock or 0
        self.stdout.write(self.style.WARNING(f"   Stock después de venta: {stock_despues_venta}"))
        self.stdout.write(f"   Descontado: {stock_inicial - stock_despues_venta}")
        
        # Verificar descuento
        if stock_despues_venta == stock_inicial - cantidad:
            self.stdout.write(self.style.SUCCESS("   [OK] Descuento correcto"))
        else:
            self.stdout.write(self.style.ERROR(f"   [X] Error en descuento. Esperaba {stock_inicial - cantidad}"))
        
        # Eliminar venta
        self.stdout.write(f"\n> Eliminando factura {factura.folio_factura}...")
        factura.delete()
        
        producto.refresh_from_db()
        stock_final = producto.stock or 0
        self.stdout.write(self.style.WARNING(f"   Stock después de eliminar: {stock_final}"))
        self.stdout.write(f"   Restaurado: {stock_final - stock_despues_venta}")
        
        # Resultado final
        self.stdout.write("\n" + "="*80)
        if stock_final == stock_inicial:
            self.stdout.write(self.style.SUCCESS("[OK] TEST PASADO"))
            self.stdout.write(f"   Stock inicial = Stock final = {stock_inicial}")
        else:
            self.stdout.write(self.style.ERROR("[X] TEST FALLADO"))
            self.stdout.write(f"   Stock inicial: {stock_inicial}")
            self.stdout.write(f"   Stock final: {stock_final}")
            self.stdout.write(f"   Diferencia: {stock_final - stock_inicial}")
        self.stdout.write("="*80 + "\n")
        
        # Resumen
        self.stdout.write(self.style.SUCCESS("\nFLUJO VERIFICADO:"))
        self.stdout.write(f"1. Stock inicial:           {stock_inicial}")
        self.stdout.write(f"2. Venta de {cantidad} unidades:     {stock_inicial} - {cantidad} = {stock_despues_venta}")
        self.stdout.write(f"3. Eliminar factura:        {stock_despues_venta} + {cantidad} = {stock_final}")
        self.stdout.write(f"4. Resultado:               {'[OK]' if stock_final == stock_inicial else '[ERROR]'}\n")
