"""
Script para corregir la factura 1127 que se procesó sin detectar PNRs.
Ejecutar con: python manage.py shell < corregir_factura_1127.py
O copiar y pegar en: python manage.py shell
"""
from ventas.models import Factura
from inventario.models import ProductoNoReconocido

print("="*80)
print("CORRIGIENDO FACTURA 1127")
print("="*80)

# 1. Buscar la factura
try:
    factura = Factura.objects.get(folio_factura='1127')
    print(f"\n✓ Factura encontrada (ID: {factura.id})")
    print(f"  UUID: {factura.uuid_factura}")
    print(f"  Estado actual: {factura.estado_revision}")
    print(f"  Requiere revisión: {factura.requiere_revision_manual}")
except Factura.DoesNotExist:
    print("\n✗ Factura NO encontrada")
    exit()

# 2. Buscar PNRs asociados
uuid = factura.uuid_factura
if not uuid:
    print("\n⚠️ Factura no tiene UUID guardado, buscando por nombre...")
    # Si no tiene UUID, buscar PNRs recientes
    pnrs = ProductoNoReconocido.objects.filter(
        origen='venta',
        procesado=False,
        fecha_detectado__gte=factura.fecha_facturacion
    ).order_by('-fecha_detectado')[:10]
else:
    pnrs = ProductoNoReconocido.objects.filter(
        uuid_factura=uuid,
        origen='venta',
        procesado=False
    )

print(f"\n✓ PNRs encontrados: {pnrs.count()}")

if pnrs.count() > 0:
    print("\nProductos no reconocidos:")
    for idx, pnr in enumerate(pnrs, 1):
        print(f"  {idx}. {pnr.nombre_detectado}")
        print(f"     - Cantidad: {pnr.cantidad}")
        print(f"     - Precio: ${pnr.precio_unitario or 0:,.2f}")
        print(f"     - Fecha: {pnr.fecha_detectado}")
        print(f"     - UUID: {pnr.uuid_factura}")
    
    # Marcar factura para revisión
    print("\n📝 Marcando factura para revisión manual...")
    factura.requiere_revision_manual = True
    factura.estado_revision = "pendiente"
    factura.save(update_fields=["requiere_revision_manual", "estado_revision"])
    print("✓ Factura actualizada")
    
    print("\n" + "="*80)
    print("✅ CORRECCIÓN COMPLETADA")
    print("="*80)
    print(f"\nAhora puedes ir al admin y ver la factura {factura.folio_factura}")
    print("Aparecerá con estado '⚠️ Pendiente (X PNR)' y podrás asignar los productos.")
else:
    print("\n⚠️ No se encontraron PNRs pendientes para esta factura")
    print("Esto puede significar:")
    print("  1. Los productos SÍ existen en la BD y se registraron correctamente")
    print("  2. Los PNRs se crearon con un UUID diferente")
    print("  3. Los PNRs ya fueron procesados")
    
    # Buscar TODOS los PNRs de esta factura (incluyendo procesados)
    all_pnrs = ProductoNoReconocido.objects.filter(
        uuid_factura=uuid,
        origen='venta'
    )
    print(f"\nPNRs totales (incluyendo procesados): {all_pnrs.count()}")
    for pnr in all_pnrs:
        print(f"  - {pnr.nombre_detectado} (procesado: {pnr.procesado})")

print("\n" + "="*80)
