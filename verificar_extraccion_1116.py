"""
Verificar qué detectó el extractor para la factura 1116
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from ventas.extractors.novavino import extraer_factura_novavino
from compras.extractors.pdf_reader import extract_text_from_pdf
from inventario.utils import encontrar_producto_unico

pdf_path = "LEPR970522CD0_Factura_1116_9F5DA3A8-E3E2-489E-B5D3-5B1C49437E7F.pdf"

print("=== VERIFICACION EXTRACTOR 1116 ===\n")

texto = extract_text_from_pdf(pdf_path)
datos = extraer_factura_novavino(texto)

print(f"Total productos extraidos: {len(datos.get('productos', []))}\n")

# Contar productos duplicados
productos_contados = {}
for i, prod in enumerate(datos.get('productos', []), 1):
    nombre = prod.get('nombre')
    cantidad = prod.get('cantidad')
    precio = prod.get('precio_unitario')
    
    print(f"{i}. Nombre extraido: '{nombre}'")
    print(f"   Cantidad: {cantidad}")
    print(f"   Precio: ${precio}")
    
    # Resolver a qué producto en BD corresponde
    producto_bd, err = encontrar_producto_unico(nombre)
    if producto_bd:
        print(f"   Resuelve a: '{producto_bd.nombre}' (ID: {producto_bd.id})")
        
        # Contar
        if producto_bd.id not in productos_contados:
            productos_contados[producto_bd.id] = []
        productos_contados[producto_bd.id].append({
            'nombre_extraido': nombre,
            'cantidad': cantidad,
            'precio': precio
        })
    else:
        print(f"   ERROR: {err}")
    print()

# Verificar duplicados
print("\n=== ANALISIS DE DUPLICADOS ===")
tiene_duplicados = False
for producto_id, apariciones in productos_contados.items():
    if len(apariciones) > 1:
        tiene_duplicados = True
        print(f"\n[!] PRODUCTO DUPLICADO - ID {producto_id}:")
        print(f"    Aparece {len(apariciones)} veces:")
        for idx, ap in enumerate(apariciones, 1):
            print(f"    {idx}. '{ap['nombre_extraido']}' - Cant: {ap['cantidad']}, Precio: ${ap['precio']}")

if not tiene_duplicados:
    print("\n[OK] No hay productos duplicados en la extraccion")
else:
    print("\n[PROBLEMA] El extractor esta detectando productos duplicados!")
    print("Esto causaria que se sumen las cantidades en la BD")
