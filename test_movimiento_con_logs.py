"""
Script para probar el movimiento de archivos con logs detallados.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.utils.drive_processor import DriveInvoiceProcessor

print("\n" + "="*70)
print("TEST: MOVIMIENTO DE ARCHIVOS CON LOGS")
print("="*70)

# Primero, borrar factura 2470 si existe
from compras.models import Compra
compra_existente = Compra.objects.filter(folio="2470").first()
if compra_existente:
    print(f"\n[INFO] Borrando factura 2470 existente (ID: {compra_existente.id})...")
    compra_existente.delete()
    print("  [OK] Factura borrada")
else:
    print("\n[INFO] Factura 2470 no existe en BD (OK)")

# Procesar
print("\n[INFO] Procesando facturas desde Drive...")
print("-"*70)

processor = DriveInvoiceProcessor(validation_mode="lenient")
resultado = processor.process_all_invoices(move_files=True)

print("-"*70)
print("\n[RESULTADO]")
print(f"Total: {resultado['total']}")
print(f"Exitosas: {resultado['success']}")
print(f"Duplicadas: {resultado['duplicate']}")
print(f"Errores: {resultado['error']}")

if resultado['details']:
    print("\nDetalles:")
    for detalle in resultado['details']:
        print(f"  - {detalle['file']}: {detalle['status']}")

print("\n" + "="*70)
print("AHORA VERIFICA EN DRIVE:")
print("="*70)
print("1. Ve a la carpeta 'Compras_Nuevas' en Drive")
print("2. La factura 2470 deberia haber desaparecido")
print("3. Ve a la carpeta 'Compras_Procesadas'")
print("4. La factura 2470 deberia estar ahi")
print("\nSi NO se movio, revisa los logs de arriba para ver el error")
print("="*70 + "\n")
