from ventas.extractors.novavino import ExtractorNovavino
from ventas.models import Factura
from inventario.models import ProductoNoReconocido
from inventario.utils import encontrar_producto_unico

# Extraer PDF
extractor = ExtractorNovavino()
datos = extractor.extract('LEPR970522CD0_Factura_1127_E9DA14FE-E047-465F-A7B0-314647B8D87C.pdf')

print("PRODUCTOS EN PDF:")
productos = datos.get('productos', [])
for i, p in enumerate(productos, 1):
    nombre = p.get('nombre', '')
    cant = p.get('cantidad', 0)
    precio = p.get('precio_unitario', 0)
    print(f"{i}. {nombre} | Cant: {cant} | Precio: ${precio:,.2f}")
    
    prod_bd, err = encontrar_producto_unico(nombre)
    if err == "not_found":
        print(f"   ⚠️ NO EXISTE EN BD")
    elif err:
        print(f"   ⚠️ {err}")
    else:
        print(f"   ✓ OK")

print(f"\nTotal productos: {len(productos)}")
print(f"UUID: {datos.get('uuid')}")

# Verificar factura
try:
    factura = Factura.objects.get(folio_factura='1127')
    print(f"\nFACTURA EN BD:")
    print(f"  Detalles: {factura.detalles.count()}")
    print(f"  Requiere revisión: {factura.requiere_revision_manual}")
    print(f"  UUID guardado: {factura.uuid_factura}")
except:
    print("\nFactura no encontrada")

# Verificar PNRs
uuid = datos.get('uuid')
pnrs = ProductoNoReconocido.objects.filter(uuid_factura=uuid, origen='venta')
print(f"\nPNRs: {pnrs.count()}")
