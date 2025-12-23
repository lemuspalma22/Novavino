"""
Corregir cantidad duplicada en factura 1116
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.models import Factura, DetalleFactura
from inventario.models import Producto

print("=== CORRECCION FACTURA 1116 ===\n")

try:
    factura = Factura.objects.get(folio_factura="1116")
    
    # Buscar el detalle con cantidad incorrecta
    det = factura.detalles.filter(producto__nombre__icontains="ENSAMBLE PERSONALIZADO").first()
    
    if det:
        print(f"Producto: {det.producto.nombre}")
        print(f"Cantidad actual: {det.cantidad}")
        print(f"Cantidad correcta: 6")
        
        # Ajustar stock
        diferencia = det.cantidad - 6
        producto = det.producto
        
        print(f"\nStock actual del producto: {producto.stock}")
        print(f"Ajuste necesario: +{diferencia} (devolver al inventario)")
        
        # Corregir cantidad en detalle
        det.cantidad = 6
        det.save()
        
        # Ajustar stock (devolver lo que se resto de mas)
        producto.stock += diferencia
        producto.save(update_fields=['stock'])
        
        print(f"Stock corregido: {producto.stock}")
        
        # Recalcular total de factura
        factura.refresh_from_db()
        print(f"\nTotal factura corregido: ${factura.total:,.2f}")
        print("\n[OK] Factura 1116 corregida")
    else:
        print("No se encontro el detalle")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
