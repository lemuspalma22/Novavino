import dotenv
dotenv.load_dotenv()
import os
import django
import re

# === Django setup ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

# === Imports específicos para VENTAS ===
from compras.extractors.pdf_reader import extract_text_from_pdf
from ventas.extractors.novavino import extraer_factura_novavino
from ventas.utils.registrar_venta import registrar_venta_automatizada

# (Opcional) utilidades compartidas por si quieres verificar UUID/Total con la misma lógica robusta
from extractors.utils_extractores import extraer_uuid, extraer_total

# === Cambia el PDF a probar ===
pdf_path = "LEPR970522CD0_Factura_987_89035BD9-8F47-4695-B5F9-051860FEC0AC.pdf"

def main():
    # 1) Extraer texto
    texto = extract_text_from_pdf(pdf_path)

    print("📄 Texto extraído del PDF:")
    print("=" * 60)
    print(texto)
    print("=" * 60)

    # 2) Parsear como VENTA
    data = extraer_factura_novavino(texto)

    # 3) Impresiones de validación
    print("\n🧾 Extracción completa de factura de VENTA (Novavino):")
    print(f"FOLIO: {data.get('folio')}")
    # Fecha que detecta el extractor de ventas
    print(f"FECHA_EMISION: {data.get('fecha_emision')}")
    # Cliente detectado
    print(f"CLIENTE: {data.get('cliente')}")
    # UUID opcional (si aparece en el PDF)
    print(f"UUID: {data.get('uuid')}")

    # Verificar total con la misma función robusta:
    try:
        total_calc = extraer_total(texto)
        print(f"TOTAL (validador robusto): {total_calc}")
    except Exception as e:
        print(f"⚠️ No se pudo validar TOTAL con utilitario robusto: {e}")
    print(f"TOTAL (extractor ventas): {data.get('total')}")

    # 4) Productos
    print("PRODUCTOS:")
    productos = data.get("productos", [])
    if not productos:
        print("  (ninguno detectado)")
    else:
        for p in productos:
            print(f" - {{'nombre': '{p.get('nombre')}', 'cantidad': {p.get('cantidad')}, 'precio_unitario': {p.get('precio_unitario')}}}")

    # 5) Guardar en BD
    print("\n💾 Guardando venta en la base de datos...")
    try:
        registrar_venta_automatizada(data)
        print(f"✅ Venta guardada con folio {data.get('folio')}")
    except Exception as e:
        print(f"❌ Error al guardar venta: {e}")

if __name__ == "__main__":
    main()
