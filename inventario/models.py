from django.db import models
from compras.models import Proveedor  # Importamos el modelo de Proveedor
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower
from django.apps import apps
from decimal import Decimal

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    uva = models.CharField(max_length=100, null=True, blank=True)  # Tipo de uva (puede ser opcional)
    tipo = models.CharField(max_length=50, choices=[('tinto', 'Tinto'), ('blanco', 'Blanco'), ('rosado', 'Rosado')], null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='productos_inventario')
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    # Costo adicional por unidad (e.g., transporte). Permite trazabilidad separada del precio de factura.
    costo_transporte = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    es_personalizado = models.BooleanField(default=False, verbose_name="Personalizado")
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre

class AliasProducto(models.Model):
    alias = models.CharField(max_length=255, unique=False)  # dejamos unique=False y ponemos UniqueConstraint CI abajo
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="aliases")

    def clean(self):
        """Evita cruces: alias igual a nombre de otro producto distinto."""
        texto = (self.alias or "").strip()
        if not texto:
            return
        # ¿existe un producto con ese nombre?
        p = Producto.objects.filter(nombre__iexact=texto).first()
        if p and p.pk != getattr(self.producto, "pk", None):
            raise ValidationError(
                {"alias": f"El alias '{texto}' coincide con el nombre del producto '{p.nombre}'. "
                          f"No puede apuntar a un producto distinto."}
            )

    class Meta:
        constraints = [
            # Unicidad case-insensitive de alias (no puede existir el mismo alias para dos filas)
            models.UniqueConstraint(
                Lower("alias"),
                name="uniq_alias_ci"
            ),
        ]

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
    raw_conceptos = models.JSONField(null=True, blank=True, help_text="Snapshot de líneas detectadas por el extractor")

    origen = models.CharField(max_length=10, choices=ORIGENES, default="compra")

    # 
    producto = models.ForeignKey(
        "inventario.Producto",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="Producto real al que corresponde este hallazgo."
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    movimiento_generado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre_detectado} ({'Procesado' if self.procesado else 'Pendiente'})"

    def procesar_a_stock(self):
        """
        - Si hay producto y está marcado como procesado, ingresa a stock.
        - Si existe Compra con uuid/uuid_sat == uuid_factura, crea detalle (CompraProducto).
        - Evita duplicar con 'movimiento_generado'.
        """
        if self.movimiento_generado or not self.procesado or not self.producto_id:
            return

        # Valores defensivos
        cant = self.cantidad or Decimal("1")
        if cant <= 0:
            cant = Decimal("1")
        costo = self.precio_unitario or Decimal("0")

        # 1) Aumentar stock del producto (tu modelo Producto tiene campo 'stock')
        prod = self.producto
        prod.stock = (prod.stock or 0) + int(cant)
        # (opcional) si tienes costo promedio o último costo, podrías actualizarlo aquí
        # Si el proveedor es Vieja Bodega y no se ha configurado costo_transporte, sugerimos 28 por unidad
        try:
            prov_name = (getattr(prod.proveedor, "nombre", "") or "").strip().lower()
            if prov_name.startswith("vieja bodega") and (prod.costo_transporte is None or prod.costo_transporte == Decimal("0")):
                prod.costo_transporte = Decimal("28")
                prod.save(update_fields=["stock", "costo_transporte"])
            else:
                prod.save(update_fields=["stock"])
        except Exception:
            prod.save(update_fields=["stock"])

        # 2) Crear detalle de compra si existe una Compra ligada por UUID
        Compra = apps.get_model("compras", "Compra")
        CompraProducto = apps.get_model("compras", "CompraProducto")
        compra = None
        if self.uuid_factura:
            compra = (Compra.objects.filter(uuid=self.uuid_factura).first() or
                      Compra.objects.filter(uuid_sat=self.uuid_factura).first())

        if compra and CompraProducto:
            det_kwargs = dict(compra=compra, producto=prod, cantidad=cant, precio_unitario=costo)
            # si tu modelo tiene 'importe', lo llenamos
            if hasattr(CompraProducto, "importe"):
                det_kwargs["importe"] = cant * costo
            CompraProducto.objects.create(**det_kwargs)

        self.movimiento_generado = True
        self.save(update_fields=["movimiento_generado"])