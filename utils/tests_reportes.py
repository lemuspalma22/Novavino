# utils/tests_reportes.py
"""
Tests para el módulo utils/reportes.py
Cubre las funciones abstraídas de reportes y cortes.
"""
from decimal import Decimal
from datetime import date, datetime
from django.test import TestCase
from django.utils import timezone

from compras.models import Compra, CompraProducto, Proveedor
from ventas.models import Factura, DetalleFactura
from inventario.models import Producto
from utils.reportes import (
    calcular_agregados_periodo_compras,
    calcular_agregados_periodo_ventas,
    generar_dict_reporte_factura,
    generar_dict_reporte_compra
)


class TestCalcularAgregadosPeriodoCompras(TestCase):
    """Tests para calcular_agregados_periodo_compras"""
    
    def setUp(self):
        """Setup común para tests de compras"""
        self.proveedor = Proveedor.objects.create(nombre="Test Proveedor")
        self.producto_personalizado = Producto.objects.create(
            nombre="Vino Personalizado",
            proveedor=self.proveedor,
            precio_compra=Decimal('100.00'),
            precio_venta=Decimal('150.00'),
            es_personalizado=True,
            stock=10
        )
        self.producto_normal = Producto.objects.create(
            nombre="Vino Normal",
            proveedor=self.proveedor,
            precio_compra=Decimal('50.00'),
            precio_venta=Decimal('75.00'),
            es_personalizado=False,
            stock=20
        )
        
        # Crear compra de prueba
        self.compra = Compra.objects.create(
            folio="TEST-001",
            proveedor=self.proveedor,
            fecha=date.today(),
            total=Decimal('300.00'),
            pagado=True
        )
        
        # Crear productos de compra
        self.compra_producto_1 = CompraProducto.objects.create(
            compra=self.compra,
            producto=self.producto_personalizado,
            cantidad=2,
            precio_unitario=Decimal('100.00')
        )
        
        self.compra_producto_2 = CompraProducto.objects.create(
            compra=self.compra,
            producto=self.producto_normal,
            cantidad=2,
            precio_unitario=Decimal('50.00')
        )

    def test_calcular_agregados_periodo_compras_vacio(self):
        """Test con período sin compras"""
        fecha_inicio = date(2020, 1, 1)
        fecha_fin = date(2020, 1, 31)
        
        resultado = calcular_agregados_periodo_compras(
            CompraProducto.objects.none(),
            fecha_inicio,
            fecha_fin
        )
        
        self.assertEqual(resultado['total_gastado'], 0)
        self.assertEqual(resultado['productos_personalizados'], 0)
        self.assertEqual(resultado['productos_no_personalizados'], 0)
        self.assertEqual(len(resultado['queryset']), 0)

    def test_calcular_agregados_periodo_compras_con_datos(self):
        """Test con compras en el período"""
        fecha_inicio = date.today()
        fecha_fin = date.today()
        
        resultado = calcular_agregados_periodo_compras(
            CompraProducto.objects.all(),
            fecha_inicio,
            fecha_fin
        )
        
        # Verificar totales
        self.assertEqual(resultado['total_gastado'], 300.0)  # 2*100 + 2*50
        self.assertEqual(resultado['productos_personalizados'], 2)  # cantidad del producto personalizado
        self.assertEqual(resultado['productos_no_personalizados'], 2)  # cantidad del producto normal
        self.assertEqual(len(resultado['queryset']), 2)


class TestCalcularAgregadosPeriodoVentas(TestCase):
    """Tests para calcular_agregados_periodo_ventas"""
    
    def setUp(self):
        """Setup común para tests de ventas"""
        self.proveedor = Proveedor.objects.create(nombre="Test Proveedor")
        self.producto_personalizado = Producto.objects.create(
            nombre="Vino Personalizado",
            proveedor=self.proveedor,
            precio_compra=Decimal('100.00'),
            precio_venta=Decimal('150.00'),
            es_personalizado=True,
            stock=10
        )
        self.producto_normal = Producto.objects.create(
            nombre="Vino Normal",
            proveedor=self.proveedor,
            precio_compra=Decimal('50.00'),
            precio_venta=Decimal('75.00'),
            es_personalizado=False,
            stock=20
        )
        
        # Crear factura de prueba (el total se calculará automáticamente por signals)
        self.factura = Factura.objects.create(
            folio_factura="FACT-001",
            cliente="Test Cliente",
            fecha_facturacion=date.today(),
            total=Decimal('0.00'),  # Se calculará automáticamente
            pagado=True,
            fecha_pago=date.today()
        )
        
        # Crear detalles de factura
        self.detalle_1 = DetalleFactura.objects.create(
            factura=self.factura,
            producto=self.producto_personalizado,
            cantidad=2,
            precio_unitario=Decimal('150.00'),
            precio_compra=Decimal('100.00')
        )
        
        self.detalle_2 = DetalleFactura.objects.create(
            factura=self.factura,
            producto=self.producto_normal,
            cantidad=2,
            precio_unitario=Decimal('75.00'),
            precio_compra=Decimal('50.00')
        )

    def test_calcular_agregados_periodo_ventas_con_productos_mixtos(self):
        """Test con ventas que incluyen productos personalizados y normales"""
        fecha_inicio = date.today()
        fecha_fin = date.today()
        
        resultado = calcular_agregados_periodo_ventas(
            Factura.objects.all(),
            fecha_inicio,
            fecha_fin,
            campo_fecha='fecha_facturacion',
            solo_pagadas=False
        )
        
        # Verificar totales (el total se calcula automáticamente por signals)
        total_esperado = 450.0  # 2*150 + 2*75 = 300 + 150 = 450
        self.assertEqual(resultado['total_venta'], total_esperado)
        self.assertEqual(resultado['costo_total'], 300.0)  # 2*100 + 2*50
        self.assertEqual(resultado['ganancia_total'], 150.0)  # 450 - 300
        self.assertEqual(resultado['productos_personalizados'], 2)  # cantidad del producto personalizado
        self.assertEqual(resultado['productos_no_personalizados'], 2)  # cantidad del producto normal
        self.assertEqual(len(resultado['queryset']), 1)

    def test_calcular_agregados_periodo_ventas_solo_pagadas(self):
        """Test filtrando solo facturas pagadas"""
        # Crear factura no pagada
        factura_no_pagada = Factura.objects.create(
            folio_factura="FACT-002",
            cliente="Test Cliente 2",
            fecha_facturacion=date.today(),
            total=Decimal('100.00'),
            pagado=False
        )
        
        fecha_inicio = date.today()
        fecha_fin = date.today()
        
        resultado = calcular_agregados_periodo_ventas(
            Factura.objects.all(),
            fecha_inicio,
            fecha_fin,
            campo_fecha='fecha_facturacion',
            solo_pagadas=True
        )
        
        # Solo debe incluir la factura pagada
        self.assertEqual(len(resultado['queryset']), 1)
        self.assertEqual(resultado['total_venta'], 450.0)  # Total calculado por signals


class TestGenerarDictReporteFactura(TestCase):
    """Tests para generar_dict_reporte_factura"""
    
    def setUp(self):
        """Setup para tests de reporte de factura"""
        self.proveedor = Proveedor.objects.create(nombre="Test Proveedor")
        self.producto = Producto.objects.create(
            nombre="Vino Test",
            proveedor=self.proveedor,
            precio_compra=Decimal('100.00'),
            precio_venta=Decimal('150.00'),
            es_personalizado=True,
            stock=10
        )
        
        self.factura = Factura.objects.create(
            folio_factura="FACT-001",
            cliente="Test Cliente",
            fecha_facturacion=date.today(),
            total=Decimal('300.00'),
            pagado=True
        )
        
        self.detalle = DetalleFactura.objects.create(
            factura=self.factura,
            producto=self.producto,
            cantidad=2,
            precio_unitario=Decimal('150.00'),
            precio_compra=Decimal('100.00')
        )

    def test_generar_dict_reporte_factura_estructura_correcta(self):
        """Test que el diccionario generado tiene la estructura correcta"""
        reporte = generar_dict_reporte_factura(self.factura)
        
        # Verificar que tiene todas las claves esperadas
        claves_esperadas = [
            'folio', 'cliente', 'fecha', 'total_venta',
            'costo_proveedores', 'ganancia', 'productos_personalizados',
            'productos_no_personalizados'
        ]
        
        for clave in claves_esperadas:
            self.assertIn(clave, reporte)
        
        # Verificar valores específicos
        self.assertEqual(reporte['folio'], 'FACT-001')
        self.assertEqual(reporte['cliente'], 'Test Cliente')
        self.assertEqual(reporte['total_venta'], 300.0)
        self.assertEqual(reporte['costo_proveedores'], 200.0)  # 2*100
        self.assertEqual(reporte['ganancia'], 100.0)  # 300-200
