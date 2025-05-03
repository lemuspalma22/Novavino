from django.db import models
from compras.models import Proveedor  # Importamos el modelo de Proveedor
from django.utils import timezone

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    uva = models.CharField(max_length=100, null=True, blank=True)  # Tipo de uva (puede ser opcional)
    tipo = models.CharField(max_length=50, choices=[('tinto', 'Tinto'), ('blanco', 'Blanco'), ('rosado', 'Rosado')], null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='productos_inventario')
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    es_personalizado = models.BooleanField(default=False, verbose_name="Personalizado")
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} - {self.tipo if self.tipo else 'Sin tipo definido'}"

class AliasProducto(models.Model):
    alias = models.CharField(max_length=200, unique=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="aliases")

    def __str__(self):
        return f"{self.alias} → {self.producto.nombre}"

class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    stock_minimo = models.IntegerField(default=5)
    fecha_ingreso = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    @property
    def estado_stock(self):
        return "Bajo" if self.cantidad < self.stock_minimo else "Suficiente"

    def __str__(self):
        return f"{self.producto.nombre} - Cantidad: {self.cantidad} - Estado: {self.estado_stock}"

class ProductoNoReconocido(models.Model):
    ORIGENES = [
        ("compra", "Compra"),
        ("venta", "Venta"),
    ]

    nombre_detectado = models.CharField(max_length=200)
    fecha_detectado = models.DateTimeField(default=timezone.now)
    uuid_factura = models.CharField(max_length=100, null=True, blank=True)
    procesado = models.BooleanField(default=False)
    origen = models.CharField(max_length=10, choices=ORIGENES, default="compra")

    def __str__(self):
        return f"{self.nombre_detectado} ({'Procesado' if self.procesado else 'Pendiente'})"
