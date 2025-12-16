import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.utils.validation import evaluar_concepto_para_revision
from inventario.models import Producto
from decimal import Decimal

# Obtener el producto real
producto = Producto.objects.filter(nombre__icontains='Ilivia Leone').first()

print(f"Producto: {producto.nombre}")
print(f"precio_compra en BD: ${producto.precio_compra}")

# Simular concepto extraído
concepto = {
    "nombre_detectado": "LEONE DE CASTRIS ILLIVIA Primitivo 100%",
    "cantidad": Decimal("30.0"),
    "precio_unitario": Decimal("218.07")
}

print(f"\nConcepto extraido:")
print(f"  nombre: {concepto['nombre_detectado']}")
print(f"  cantidad: {concepto['cantidad']}")
print(f"  precio_unitario: ${concepto['precio_unitario']}")

# Ejecutar validación
print(f"\nEjecutando evaluar_concepto_para_revision...")
motivos = evaluar_concepto_para_revision(
    concepto=concepto,
    producto_mapeado=producto,
    datos_factura={}
)

print(f"\nResultados:")
print(f"  Motivos: {motivos}")
print(f"  Requiere revision: {bool(motivos)}")

if motivos:
    print(f"\n  CORRECTO - Se detecto el problema de precio")
else:
    print(f"\n  ERROR - NO se detecto el problema de precio")
