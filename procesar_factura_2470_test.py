"""
Script para procesar la factura 2470 que está pendiente en Drive.
Esto verifica que el sistema funciona correctamente.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from compras.utils.drive_processor import DriveInvoiceProcessor

print("\n" + "="*70)
print("PROCESAR FACTURA 2470 (TEST)")
print("="*70)

processor = DriveInvoiceProcessor(validation_mode="lenient")

print("\n[INFO] Procesando todas las facturas pendientes en Drive...")
resultado = processor.process_all_invoices(move_files=True)

print("\n" + "="*70)
print("RESULTADOS")
print("="*70)
print(f"Total archivos: {resultado['total']}")
print(f"Exitosas: {resultado['success']}")
print(f"Duplicadas: {resultado['duplicate']}")
print(f"Errores: {resultado['error']}")

if resultado['details']:
    print("\nDetalles:")
    for detalle in resultado['details']:
        status_icon = {
            'success': '[OK]',
            'duplicate': '[DUPLICADO]',
            'error': '[ERROR]'
        }.get(detalle['status'], '[?]')
        
        print(f"\n  {status_icon} {detalle['file']}")
        if detalle.get('folio'):
            print(f"      Folio: {detalle['folio']}")
        if detalle.get('proveedor'):
            print(f"      Proveedor: {detalle['proveedor']}")
        if detalle.get('error'):
            print(f"      Error: {detalle['error'][:100]}")

print("\n" + "="*70 + "\n")
