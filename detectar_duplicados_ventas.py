"""
Detectar y consolidar detalles duplicados en facturas antes de aplicar el constraint
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura, DetalleFactura
from django.db.models import Count
from django.db import transaction

print("=== DETECCION DE DUPLICADOS EN DETALLES DE FACTURAS ===\n")

# Buscar detalles duplicados (misma factura + mismo producto)
duplicados = (
    DetalleFactura.objects
    .values('factura', 'producto')
    .annotate(count=Count('id'))
    .filter(count__gt=1)
)

num_duplicados = duplicados.count()

if num_duplicados == 0:
    print("[OK] No se encontraron detalles duplicados")
else:
    print(f"[!] Encontrados {num_duplicados} casos de duplicacion\n")
    
    for dup in duplicados:
        factura_id = dup['factura']
        producto_id = dup['producto']
        count = dup['count']
        
        # Obtener todos los detalles duplicados
        detalles = DetalleFactura.objects.filter(
            factura_id=factura_id,
            producto_id=producto_id
        ).order_by('id')
        
        factura = Factura.objects.get(id=factura_id)
        producto_nombre = detalles.first().producto.nombre
        
        print(f"Factura {factura.folio_factura} - Producto: {producto_nombre}")
        print(f"  Tiene {count} detalles duplicados:")
        
        cantidad_total = 0
        precio_promedio = 0
        ids_a_eliminar = []
        
        for idx, det in enumerate(detalles, 1):
            print(f"    {idx}. ID={det.id}, Cantidad={det.cantidad}, Precio=${det.precio_unitario}")
            cantidad_total += det.cantidad
            precio_promedio += det.precio_unitario
            
            if idx > 1:  # Mantener el primero, eliminar los demás
                ids_a_eliminar.append(det.id)
        
        precio_promedio = precio_promedio / count
        
        print(f"  Consolidando a:")
        print(f"    Cantidad total: {cantidad_total}")
        print(f"    Precio promedio: ${precio_promedio:.2f}")
        
        with transaction.atomic():
            # Actualizar el primer detalle
            primer_detalle = detalles.first()
            primer_detalle.cantidad = cantidad_total
            primer_detalle.precio_unitario = precio_promedio
            primer_detalle.save()
            
            # Eliminar los duplicados
            DetalleFactura.objects.filter(id__in=ids_a_eliminar).delete()
            
            print(f"  [OK] Consolidado (mantener ID={primer_detalle.id}, eliminar IDs={ids_a_eliminar})\n")

print(f"\n[OK] Limpieza completada. Ahora puedes aplicar la migracion:")
print("  python manage.py migrate ventas")
