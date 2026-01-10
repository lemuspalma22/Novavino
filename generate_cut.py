import dotenv
dotenv.load_dotenv()
import os
import django
from datetime import datetime
from collections import defaultdict
import csv


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

from compras.models import Compra, CompraProducto

# Pedimos rango de fechas al usuario
print("\n📅 Ingreso del rango de fechas para el corte de compras")
fecha_inicio_input = input("Fecha de inicio (YYYY-MM-DD): ")
fecha_fin_input = input("Fecha de fin (YYYY-MM-DD): ")
fecha_inicio = datetime.strptime(fecha_inicio_input, "%Y-%m-%d")
fecha_fin = datetime.strptime(fecha_fin_input, "%Y-%m-%d")

# 🔎 Buscamos compras
compras = Compra.objects.filter(fecha__range=(fecha_inicio, fecha_fin))

# Inicializamos contadores
total_gastado = 0
productos_personalizados = 0
productos_no_personalizados = 0
gasto_por_proveedor = defaultdict(float)

print("\n📦 Resumen de Compras:")
for compra in compras:
    print(f"\nCompra {compra.folio} ({compra.fecha}): {compra.proveedor.nombre if compra.proveedor else 'Proveedor no asignado'}")
    productos = compra.productos.all()
    for producto_compra in productos:
        subtotal = producto_compra.subtotal()
        total_gastado += float(subtotal)
        proveedor_nombre = compra.proveedor.nombre if compra.proveedor else "Proveedor no asignado"
        gasto_por_proveedor[proveedor_nombre] += float(subtotal)

        if producto_compra.producto.es_personalizado:
            productos_personalizados += producto_compra.cantidad
        else:
            productos_no_personalizados += producto_compra.cantidad

        print(f"  - {producto_compra.cantidad} x {producto_compra.producto.nombre} → ${subtotal:.2f}")

# ✅ Ahora SÍ, después de recorrer todo:
print("\n🔢 Totales:")
print(f"Total gastado: ${total_gastado:.2f}")
print(f"Productos personalizados: {productos_personalizados}")
print(f"Productos no personalizados: {productos_no_personalizados}")

print("\n📊 Total gastado por proveedor:")
for proveedor, total in gasto_por_proveedor.items():
    print(f"- {proveedor}: ${total:.2f}")


# Preguntar si quiere exportar a CSV
exportar_csv = input("\n¿Deseas exportar este corte a CSV? (s/n): ").strip().lower()

if exportar_csv == "s":
    nombre_archivo = f"corte_compras_{fecha_inicio.date()}_a_{fecha_fin.date()}.csv"

    with open(nombre_archivo, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(["Folio", "Fecha", "Proveedor", "Producto", "Cantidad", "Precio Unitario", "Subtotal", "Personalizado"])

        for compra in compras:
            productos = compra.productos.all()
            for producto_compra in productos:
                writer.writerow([
                    compra.folio,
                    compra.fecha,
                    compra.proveedor.nombre if compra.proveedor else "Proveedor no asignado",
                    producto_compra.producto.nombre,
                    producto_compra.cantidad,
                    producto_compra.precio_unitario,
                    producto_compra.subtotal(),
                    "Sí" if producto_compra.producto.es_personalizado else "No"
                ])

    print(f"\n✅ Corte exportado exitosamente como: {nombre_archivo}")
else:
    print("\n🚫 No se exportó a CSV.")