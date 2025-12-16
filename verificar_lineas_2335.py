"""Verificar CompraProducto de la factura 2335"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto

print("\n" + "="*70)
print("VERIFICAR LINEAS (CompraProducto) DE FACTURA 2335")
print("="*70)

compra = Compra.objects.get(folio='2335')
print(f"\nCompra 2335:")
print(f"  requiere_revision_manual: {compra.requiere_revision_manual}")
print(f"  estado_revision: {compra.estado_revision}")

productos = CompraProducto.objects.filter(compra=compra)
print(f"\nProductos en CompraProducto: {productos.count()}")

for cp in productos:
    print(f"\n  Producto: {cp.producto.nombre}")
    print(f"    Cantidad: {cp.cantidad}")
    print(f"    P/U: ${cp.precio_unitario}")
    print(f"    requiere_revision_manual: {cp.requiere_revision_manual}")
    print(f"    motivo_revision: {cp.motivo_revision or '(sin motivo)'}")

print("\n" + "="*70)
print("DIAGNOSTICO:")
lineas_con_flag = productos.filter(requiere_revision_manual=True).count()
print(f"  Lineas con flag: {lineas_con_flag}")
print(f"  Widget deberia mostrar: {lineas_con_flag}")
if lineas_con_flag == 0 and compra.requiere_revision_manual:
    print("\n  [PROBLEMA] La compra esta marcada pero las lineas NO")
    print("  [CAUSA] La logica de marcar lineas no se ejecuto o fallo")
else:
    print("\n  [OK] Lineas marcadas correctamente")
print("="*70 + "\n")
