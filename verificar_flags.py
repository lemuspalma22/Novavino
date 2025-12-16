import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import CompraProducto, Compra

compra = Compra.objects.filter(folio='2326').first()
print(f"\nCompra: {compra.folio}")
print(f"Requiere revision manual: {compra.requiere_revision_manual}")
print(f"Estado revision: {compra.estado_revision}")

print(f"\nProductos en Compra 2326:")
cps = CompraProducto.objects.filter(compra__folio='2326')
for cp in cps:
    print(f"\n  Producto: {cp.producto.nombre}")
    print(f"  Precio BD: ${cp.producto.precio_compra}")
    print(f"  Precio extraido: ${cp.precio_unitario}")
    print(f"  Requiere revision: {cp.requiere_revision_manual}")
    print(f"  Motivo: {cp.motivo_revision}")
    print(f"  Estado visual: {'[!] REQUIERE REVISION' if cp.requiere_revision_manual else '[OK]'}")
