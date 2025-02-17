from django.db import models

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='productos_compras')
    precio = models.DecimalField(max_digits=10, decimal_places=2)  # Precio unitario del producto

    def __str__(self):
        return f"{self.nombre} - {self.proveedor.nombre}"

class Compra(models.Model):
    folio = models.CharField(max_length=20)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha = models.DateField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    revision = models.BooleanField(default=False)
    archivo = models.FileField(upload_to='compras_archivos/', null=True, blank=True)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    complemento_pago = models.CharField(max_length=100, null=True, blank=True)
    notas = models.TextField(null=True, blank=True)

    @property
    def estado(self):
        return "Viva" if not self.pagado else "Muerta"

    def __str__(self):
        return f"Compra {self.folio} - Proveedor: {self.proveedor} - Estado: {self.estado}"

class CompraProducto(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='productos')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en Compra {self.compra.folio}"
