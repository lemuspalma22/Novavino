import dotenv
dotenv.load_dotenv()
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

from compras.extractors.pdf_reader import (
    extract_invoice_data,
    extract_product_list,
    extract_text_from_pdf,
)
from inventario.utils import encontrar_producto
from inventario.models import ProductoNoReconocido  # 👈 nuevo import
from compras.models import Compra, CompraProducto
from datetime import datetime


#pdf_path = "LEPR970522CD0_Factura_798_558F6BFB-661A-4B26-A34E-C6FA56CBD907.pdf"
#pdf_path =  "LEPR970522CD0_Factura_760_85F6D90B-87F0-4BA9-A57F-EB3636304D74.pdf"
#pdf_path =  "LEPR970522CD0_Factura_780_A46C65AE-2E0D-4799-96E0-B97E7FEF77DC.pdf"
pdf_path =  "LEPR970522CD0_Factura_751_58BE9C98-9966-4ABA-B233-9ABC1D4378EE.pdf"
# Obtener texto completo

text = extract_text_from_pdf(pdf_path)

# Extraer metadatos de la factura
print("🧾 Datos de la factura:")
datos = extract_invoice_data(pdf_path)
for k, v in datos.items():
    print(f"{k}: {v}")

# Extraer productos y cantidades
print("\n📦 Productos detectados:")
productos = extract_product_list(text)
for producto in productos:
    print(f"- {producto['cantidad']} x {producto['nombre_detectado']}")

# Mapeo con productos existentes o alias
print("\n🔍 Productos encontrados en base de datos:")
for producto in productos:
    resultado = encontrar_producto(producto["nombre_detectado"])
    if resultado:
        print(f"✔ {producto['cantidad']} x {resultado.nombre}")
    else:
        print(f"⚠ Producto no encontrado: {producto['nombre_detectado']}")

        # Registrar producto no reconocido (si no existe ya)
        ya_existe = ProductoNoReconocido.objects.filter(
            nombre_detectado=producto["nombre_detectado"]
        ).exists()

        if not ya_existe:
            ProductoNoReconocido.objects.create(
                nombre_detectado=producto["nombre_detectado"],
                uuid_factura=datos.get("uuid"),
                procesado=False
            )

print("\n💾 Guardando productos en base de datos...")

# Buscar o crear la compra correspondiente usando el UUID
uuid = datos.get("uuid")
compra, creada = Compra.objects.get_or_create(
    uuid=uuid,
    defaults={
        "folio": datos.get("factura"),
        "fecha": datetime.fromisoformat(datos["fecha_emision"]) if datos.get("fecha_emision") else None,
        "total": float(datos.get("total").replace(",", "")) if datos.get("total") else 0,
        "proveedor": None,  # Lo llenas a mano en admin si no lo detectamos
        "pagado": False
    }
)

if not creada:
    print(f"📄 Compra ya existente: {compra.folio} (UUID: {compra.uuid})")
else:
    print(f"📄 Nueva compra registrada: {compra.folio} (UUID: {compra.uuid})")

# Determinar proveedor desde los productos detectados
proveedores_detectados = set()

for p in productos:
    producto = encontrar_producto(p["nombre_detectado"])
    if producto:
        proveedores_detectados.add(producto.proveedor)

# Si todos los productos son del mismo proveedor, lo asignamos a la compra
if len(proveedores_detectados) == 1:
    proveedor_unico = proveedores_detectados.pop()
    compra.proveedor = proveedor_unico
    compra.save()
    print(f"🏷️ Proveedor asignado automáticamente: {proveedor_unico.nombre}")
elif len(proveedores_detectados) > 1:
    print("⚠️ Productos de múltiples proveedores detectados. La compra no se asignó automáticamente.")
else:
    print("⚠️ No se pudo determinar ningún proveedor desde los productos.")


# Insertar productos de la factura como CompraProducto
for p in productos:
    producto = encontrar_producto(p["nombre_detectado"])
    if producto:
        # Verificar si ya existe el producto en la compra
        existe = CompraProducto.objects.filter(
            compra=compra,
            producto=producto,
            detectado_como=p["nombre_detectado"]
        ).exists()

        if not existe:
            CompraProducto.objects.create(
                compra=compra,
                producto=producto,
                cantidad=int(p["cantidad"]),
                precio_unitario=producto.precio_compra,
                detectado_como=p["nombre_detectado"]
            )
            print(f"✔ Guardado: {p['cantidad']} x {producto.nombre}")
        else:
            print(f"🔁 Ya existía: {producto.nombre}, no se duplicó")
