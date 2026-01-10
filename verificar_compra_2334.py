"""Verificar estado de la compra 2334 con licor"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto

compra = Compra.objects.filter(folio='2334').first()

if not compra:
    print("Compra 2334 no existe")
else:
    print(f"\n{'='*70}")
    print(f"COMPRA 2334 - ESTADO")
    print(f"{'='*70}")
    print(f"Proveedor:               {compra.proveedor.nombre}")
    print(f"Total:                   ${compra.total}")
    print(f"Requiere revision:       {compra.requiere_revision_manual}")
    print(f"Estado revision:         {compra.estado_revision}")
    
    if compra.requiere_revision_manual:
        print(f"\n[OK] Compra marcada para revision")
    else:
        print(f"\n[ERROR] Compra NO marcada (deberia estarlo por IEPS 53%)")
    
    print(f"\n{'='*70}")
    print(f"PRODUCTOS EN COMPRA")
    print(f"{'='*70}")
    
    productos = CompraProducto.objects.filter(compra=compra)
    for cp in productos:
        print(f"\nProducto: {cp.producto.nombre}")
        print(f"  Cantidad:            {cp.cantidad}")
        print(f"  P/U:                 ${cp.precio_unitario}")
        print(f"  Requiere revision:   {cp.requiere_revision_manual}")
        if cp.motivo_revision:
            print(f"  Motivo:              {cp.motivo_revision}")
    
    print(f"\n{'='*70}")
