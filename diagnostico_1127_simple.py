"""
Script simplificado para diagnosticar factura 1127
Ejecutar con: python manage.py shell < diagnostico_1127_simple.py
"""
from ventas.extractors.novavino import ExtractorNovavino
from ventas.models import Factura
from inventario.models import ProductoNoReconocido
from inventario.utils import encontrar_producto_unico

print("="*80)
print("DIAGNÓSTICO FACTURA 1127")
print("="*80)

# 1. Extraer PDF
print("\n1. EXTRAYENDO PDF...")
pdf_path = "LEPR970522CD0_Factura_1127_E9DA14FE-E047-465F-A7B0-314647B8D87C.pdf"
extractor = ExtractorNovavino()
datos = extractor.extract(pdf_path)

print(f"UUID: {datos.get('uuid')}")
print(f"Folio: {datos.get('folio')}")
print(f"Cliente: {datos.get('cliente')}")

productos = datos.get('productos', [])
print(f"\nProductos en PDF: {len(productos)}")
for idx, p in enumerate(productos, 1):
    nombre = p.get('nombre', '')
    cant = p.get('cantidad', 0)
    precio = p.get('precio_unitario', 0)
    print(f"  {idx}. {nombre} | Cant: {cant} | P/U: ${precio:,.2f}")
    
    # Verificar si existe
    prod_bd, err = encontrar_producto_unico(nombre)
    if err == "not_found":
        print(f"     ⚠️ NO ENCONTRADO EN BD")
    elif err == "ambiguous":
        print(f"     ⚠️ AMBIGUO")
    else:
        print(f"     ✓ OK: {prod_bd.nombre}")

# 2. Verificar factura en BD
print("\n" + "="*80)
print("2. FACTURA EN BD")
print("="*80)
try:
    factura = Factura.objects.get(folio_factura='1127')
    print(f"✓ Encontrada (ID: {factura.id})")
    print(f"  UUID: {factura.uuid_factura}")
    print(f"  Requiere revisión: {factura.requiere_revision_manual}")
    print(f"  Estado: {factura.estado_revision}")
    print(f"\n  Detalles: {factura.detalles.count()}")
    for d in factura.detalles.all():
        print(f"    - {d.producto.nombre} x{d.cantidad}")
except Factura.DoesNotExist:
    print("✗ NO encontrada")
    factura = None

# 3. Verificar PNRs
print("\n" + "="*80)
print("3. PRODUCTOS NO RECONOCIDOS")
print("="*80)
uuid = datos.get('uuid')
pnrs = ProductoNoReconocido.objects.filter(uuid_factura=uuid, origen='venta')
print(f"PNRs con UUID {uuid}: {pnrs.count()}")
for pnr in pnrs:
    print(f"  - {pnr.nombre_detectado} (procesado: {pnr.procesado})")

# 4. Análisis
print("\n" + "="*80)
print("4. ANÁLISIS")
print("="*80)
if factura:
    diff = len(productos) - factura.detalles.count()
    print(f"Productos PDF: {len(productos)}")
    print(f"Detalles BD: {factura.detalles.count()}")
    print(f"PNRs: {pnrs.count()}")
    print(f"Diferencia: {diff}")
    
    if diff > 0:
        print(f"\n⚠️ FALTAN {diff} producto(s)")
        # Identificar cuáles
        nombres_bd = {d.producto.nombre for d in factura.detalles.all()}
        for p in productos:
            nombre = p.get('nombre', '')
            if nombre not in nombres_bd:
                print(f"  FALTA: {nombre}")
                cant = p.get('cantidad', 0)
                if cant <= 0:
                    print(f"    → CAUSA: Cantidad inválida ({cant})")

print("\n" + "="*80)
