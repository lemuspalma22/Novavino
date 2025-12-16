"""Reprocesar factura 2445 completamente"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.models import Compra, CompraProducto
from compras.extractors.pdf_reader import extract_text_from_pdf
from extractors.secretos_delavid import ExtractorSecretosDeLaVid
from compras.utils.registrar_compra import registrar_compra_automatizada

print("\n" + "="*70)
print("REPROCESAR FACTURA 2445")
print("="*70)

pdf_path = "SVI180726AHAFS2445.pdf"

# Paso 1: Eliminar factura existente
print("\n[1/4] Eliminando factura existente...")
compras_existentes = Compra.objects.filter(folio="2445")
if compras_existentes.exists():
    # Eliminar productos asociados
    for compra in compras_existentes:
        CompraProducto.objects.filter(compra=compra).delete()
    compras_existentes.delete()
    print("      [OK] Factura eliminada")
else:
    print("      [INFO] No habia factura existente")

# Paso 2: Extraer datos del PDF
print("\n[2/4] Extrayendo datos del PDF...")
text = extract_text_from_pdf(pdf_path)
extractor = ExtractorSecretosDeLaVid(text, pdf_path)
datos = extractor.parse()

print(f"      Folio: {datos.get('folio')}")
print(f"      UUID: {datos.get('uuid')}")
print(f"      Total: ${datos.get('total'):,.2f}")
print(f"      Productos: {len(datos.get('productos', []))}")

# Mostrar productos detectados
productos = datos.get('productos', [])
print("\n      Productos detectados:")
for i, prod in enumerate(productos, 1):
    nombre = prod.get('nombre_detectado', 'SIN NOMBRE')[:50]
    cantidad = prod.get('cantidad', 0)
    precio = prod.get('precio_unitario', 0)
    print(f"        {i}. {nombre} | {cantidad} x ${precio:,.2f}")

# Paso 3: Registrar en BD
print("\n[3/4] Registrando en base de datos...")
try:
    compra = registrar_compra_automatizada(datos)
    print(f"      [OK] Compra registrada: ID={compra.id}")
    print(f"      Requiere revision: {compra.requiere_revision_manual}")
except Exception as e:
    print(f"      [ERROR] {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Paso 4: Verificar resultado
print("\n[4/4] Verificando resultado...")
compra_nueva = Compra.objects.get(folio="2445")
productos_guardados = CompraProducto.objects.filter(compra=compra_nueva)

print(f"      Productos guardados: {productos_guardados.count()}")

suma_pdf = 0
suma_bd = 0

for cp in productos_guardados:
    cantidad = cp.cantidad or 0
    precio_pdf = cp.precio_unitario or 0
    precio_bd = cp.producto.precio_compra if cp.producto else 0
    
    suma_pdf += cantidad * precio_pdf
    suma_bd += cantidad * precio_bd
    
    nombre = cp.producto.nombre if cp.producto else "NO ASIGNADO"
    print(f"        - {nombre[:40]:40} | {cantidad} x ${precio_pdf:,.2f}")

print(f"\n      Suma PDF: ${suma_pdf:,.2f}")
print(f"      Suma BD:  ${suma_bd:,.2f}")
print(f"      Total:    ${compra_nueva.total:,.2f}")

diferencia = abs(compra_nueva.total - suma_bd)
diferencia_pct = (diferencia / compra_nueva.total * 100) if compra_nueva.total else 0

print(f"      Diferencia: ${diferencia:,.2f} ({diferencia_pct:.2f}%)")

print("\n" + "="*70)
print("RESULTADO:")
print("-"*70)

if productos_guardados.count() == 4:
    print("[OK] Se guardaron 4 productos (correcto)")
elif productos_guardados.count() == 3:
    print("[ERROR] Solo se guardaron 3 productos (falta TRES RIBERAS)")
    print("\nInvestigando por que falta...")
    
    # Verificar si alguno tiene nombre que incluya TRES RIBERAS
    for cp in productos_guardados:
        if cp.producto and "TRES" in cp.producto.nombre.upper():
            print(f"  [INFO] Encontrado producto con TRES: {cp.producto.nombre}")
    
    print("\n  [DIAGNOSTICO] El extractor SI detecto 4 productos")
    print("                Pero solo se guardaron 3 en BD")
    print("                Problema: en el proceso de asignacion de productos")
else:
    print(f"[ERROR] Se guardaron {productos_guardados.count()} productos (inesperado)")

if diferencia_pct < 1:
    print("[OK] Diferencia < 1%")
else:
    print(f"[ALERTA] Diferencia {diferencia_pct:.2f}%")

print("="*70 + "\n")
