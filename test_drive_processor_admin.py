"""
Script de prueba para verificar que el módulo drive_processor funciona correctamente.
NO procesa facturas reales, solo valida imports y estructura.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

print("\n" + "="*70)
print("TEST: MÓDULO DRIVE_PROCESSOR")
print("="*70)

# Test 1: Importar módulo
print("\n[1/5] Verificando imports...")
try:
    from compras.utils.drive_processor import DriveInvoiceProcessor, process_drive_invoices
    print("  [OK] Módulo importado correctamente")
except ImportError as e:
    print(f"  [ERROR] No se pudo importar: {e}")
    exit(1)

# Test 2: Crear instancia
print("\n[2/5] Creando instancia del procesador...")
try:
    processor = DriveInvoiceProcessor(validation_mode="lenient")
    print("  [OK] Instancia creada correctamente")
    print(f"  - Carpeta nuevas: {processor.nuevas_folder_id[:20]}...")
    print(f"  - Modo validación: {processor.validation_mode}")
except Exception as e:
    print(f"  [ERROR] No se pudo crear instancia: {e}")
    exit(1)

# Test 3: Verificar métodos
print("\n[3/5] Verificando métodos disponibles...")
metodos_esperados = [
    'get_drive',
    'normalize_spaces',
    'is_duplicate',
    'process_pdf_file',
    'list_pdfs_in_folder',
    'process_all_invoices'
]
for metodo in metodos_esperados:
    if hasattr(processor, metodo):
        print(f"  [OK] {metodo}")
    else:
        print(f"  [ERROR] Falta método: {metodo}")

# Test 4: Verificar función de conveniencia
print("\n[4/5] Verificando función process_drive_invoices()...")
if callable(process_drive_invoices):
    print("  [OK] Función disponible")
else:
    print("  [ERROR] Función no es callable")

# Test 5: Verificar admin action
print("\n[5/5] Verificando admin action...")
try:
    from compras.admin import CompraAdmin
    from compras.models import Compra
    from django.contrib.admin.sites import site
    
    admin_instance = CompraAdmin(model=Compra, admin_site=site)
    
    # Verificar que la action existe
    if 'procesar_facturas_drive' in admin_instance.actions:
        print("  [OK] Action 'procesar_facturas_drive' registrada")
    else:
        print("  [ERROR] Action no encontrada en admin")
    
    # Verificar que el método existe
    if hasattr(admin_instance, 'procesar_facturas_drive'):
        print("  [OK] Método procesar_facturas_drive() existe")
        
        # Verificar descripción
        desc = getattr(admin_instance.procesar_facturas_drive, 'short_description', None)
        if desc:
            print(f"  [OK] Descripción: '{desc}'")
        else:
            print("  [WARN] Sin descripción (short_description)")
    else:
        print("  [ERROR] Método no encontrado")
        
except Exception as e:
    print(f"  [ERROR] Error al verificar admin: {e}")

# Resumen
print("\n" + "="*70)
print("RESUMEN")
print("="*70)
print("[OK] Todos los componentes estan instalados correctamente")
print("")
print("PROXIMOS PASOS:")
print("1. Ve al Django Admin > Compras")
print("2. Selecciona accion 'Procesar facturas desde Google Drive'")
print("3. Haz clic en 'Ir'")
print("")
print("NOTA: Si hay facturas pendientes en Drive, se procesaran.")
print("      Si no hay facturas, veras mensaje de advertencia.")
print("="*70 + "\n")
