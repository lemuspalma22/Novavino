"""Verificar qué versión del extractor está cargada en Django"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

import inspect
from extractors.secretos_delavid import ExtractorSecretosDeLaVid

print("\n" + "="*70)
print("VERIFICACION: VERSION DEL EXTRACTOR CARGADO")
print("="*70)

# Obtener el código fuente del método parse
source = inspect.getsource(ExtractorSecretosDeLaVid.parse)

print("\nBuscando mejoras aplicadas...")
print("-"*70)

# Verificar si tiene el código mejorado
if "partes_descripcion" in source:
    print("[OK] Extractor MEJORADO cargado")
    print("     Detectado: 'partes_descripcion' (codigo nuevo)")
else:
    print("[ERROR] Extractor VIEJO cargado")
    print("        Django esta usando codigo en cache")

if "# Buscar la línea con la clave y tomar las siguientes líneas (puede ser multilínea)" in source:
    print("[OK] Comentario de multilinea encontrado")
else:
    print("[ALERTA] Comentario no encontrado - podria ser version vieja")

# Verificar las regex de limpieza
if r'[A-Z]{2,}\d{1,2}\.\d{2}$' in source:
    print("[OK] Regex de limpieza mejorada encontrada")
else:
    print("[ALERTA] Regex de limpieza no encontrada")

print("\n" + "="*70)
print("DIAGNOSTICO:")
print("-"*70)

if "partes_descripcion" in source:
    print("\n[INFO] El codigo mejorado SI esta cargado en Django")
    print("\nPosibles causas del problema:")
    print("  1. Necesitas REFRESCAR la pagina del admin (Ctrl+Shift+R)")
    print("  2. Hay datos en cache del navegador")
    print("  3. Algo mas esta fallando en el procesamiento")
    print("\nAccion sugerida:")
    print("  - Cierra completamente el navegador")
    print("  - Vuelve a abrir y procesar la factura")
else:
    print("\n[PROBLEMA] Django esta usando el codigo VIEJO")
    print("\nAccion REQUERIDA:")
    print("  - REINICIAR el servidor de desarrollo de Django")
    print("  - Presiona Ctrl+C en la terminal donde corre 'runserver'")
    print("  - Vuelve a ejecutar: python manage.py runserver")
    print("  - Luego vuelve a procesar la factura")

print("="*70 + "\n")

# Mostrar fragmento relevante del código
print("\nFRAGMENTO DEL CODIGO ACTUAL (lineas 117-145):")
print("="*70)

lines = source.split('\n')
for i, line in enumerate(lines[15:45], start=15):  # Aproximadamente donde está la mejora
    print(f"{i:3}: {line}")

print("="*70 + "\n")
