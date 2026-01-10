"""Verificar que las compras 2334 y 2335 ya no tienen flags"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto

print("\n" + "="*70)
print("VERIFICAR LIMPIEZA DE FLAGS - COMPRAS 2334 y 2335")
print("="*70)

for folio in ['2334', '2335']:
    compra = Compra.objects.get(folio=folio)
    print(f"\n{'='*70}")
    print(f"Compra {folio}:")
    print(f"  Estado: {compra.estado_revision}")
    print(f"  Requiere revision (Compra): {compra.requiere_revision_manual}")
    
    productos = CompraProducto.objects.filter(compra=compra)
    lineas_con_flags = productos.filter(requiere_revision_manual=True).count()
    
    print(f"\n  Productos ({productos.count()}):")
    for cp in productos:
        flag_icon = "[WARNING]" if cp.requiere_revision_manual else "[OK]"
        print(f"    {flag_icon} {cp.producto.nombre}")
        print(f"         requiere_revision: {cp.requiere_revision_manual}")
        print(f"         motivo: {cp.motivo_revision or '(sin motivo)'}")
    
    print(f"\n  Lineas con flags: {lineas_con_flags}")
    if lineas_con_flags == 0:
        print(f"  [OK] Todos los flags limpiados correctamente")
    else:
        print(f"  [ERROR] Todavia hay {lineas_con_flags} lineas con flags")

print("\n" + "="*70 + "\n")
