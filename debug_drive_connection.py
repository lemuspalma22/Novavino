"""
Script para diagnosticar problemas con el procesamiento de facturas desde Drive.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

print("\n" + "="*70)
print("DIAGNOSTICO: PROCESAMIENTO DE FACTURAS DESDE DRIVE")
print("="*70)

# Test 1: Verificar imports
print("\n[1/6] Verificando imports...")
try:
    from compras.utils.drive_processor import DriveInvoiceProcessor
    print("  [OK] Modulo drive_processor importado")
except Exception as e:
    print(f"  [ERROR] No se pudo importar: {e}")
    exit(1)

# Test 2: Verificar configuración de carpetas
print("\n[2/6] Verificando configuracion de carpetas...")
import dotenv
dotenv.load_dotenv()

ROOT_FOLDER_ID = os.getenv("COMPRAS_ROOT_ID", "1o9SkoeJ66qoBEbmyzXXhs1I67PQStTWV")
NUEVAS_FOLDER_ID = os.getenv("COMPRAS_NUEVAS_ID", "1yQ4Jq2nQuJsKxxdoIJ2VLAjszSx19d4U")
PROCESADAS_FOLDER_ID = os.getenv("COMPRAS_PROCESADAS_ID", "1k_1LT-J4foKRw2-pAYuAWBntmab6Yix7")
ERRORES_FOLDER_ID = os.getenv("COMPRAS_ERRORES_ID", "1YSo5L2VCoswN-vYr1kOCiTVctGp70ZV2")

print(f"  Carpeta ROOT: {ROOT_FOLDER_ID[:20]}...")
print(f"  Carpeta NUEVAS: {NUEVAS_FOLDER_ID[:20]}...")
print(f"  Carpeta PROCESADAS: {PROCESADAS_FOLDER_ID[:20]}...")
print(f"  Carpeta ERRORES: {ERRORES_FOLDER_ID[:20]}...")

# Test 3: Intentar conectar con Google Drive
print("\n[3/6] Intentando conectar con Google Drive...")
try:
    processor = DriveInvoiceProcessor()
    drive = processor.get_drive()
    print("  [OK] Conexion exitosa con Google Drive")
except Exception as e:
    print(f"  [ERROR] No se pudo conectar: {e}")
    print("\n  SOLUCION:")
    print("  1. Verifica que existan los archivos:")
    print("     - settings.yaml")
    print("     - token.json (se crea automaticamente)")
    print("  2. Si no existe token.json, ejecuta:")
    print("     python process_drive_invoices.py")
    print("  3. Autoriza el acceso en la ventana que se abre")
    exit(1)

# Test 4: Listar archivos en carpeta NUEVAS
print("\n[4/6] Listando archivos en carpeta 'Compras_Nuevas'...")
try:
    archivos = processor.list_pdfs_in_folder(NUEVAS_FOLDER_ID)
    print(f"  [INFO] Se encontraron {len(archivos)} archivo(s) PDF")
    
    if len(archivos) == 0:
        print("\n  [ADVERTENCIA] No hay archivos en la carpeta!")
        print("  VERIFICAR:")
        print("  1. Los archivos estan en la carpeta correcta?")
        print("  2. Son archivos PDF?")
        print("  3. No estan en la papelera?")
    else:
        print("\n  Archivos encontrados:")
        for i, archivo in enumerate(archivos[:10], 1):
            print(f"    {i}. {archivo['title']}")
        if len(archivos) > 10:
            print(f"    ... y {len(archivos) - 10} mas")
    
    # Buscar específicamente factura 2070
    factura_2070 = None
    for archivo in archivos:
        if "2070" in archivo['title']:
            factura_2070 = archivo
            print(f"\n  [ENCONTRADO] Factura 2070: {archivo['title']}")
            break
    
    if not factura_2070:
        print("\n  [ADVERTENCIA] No se encontro archivo con '2070' en el nombre")
        print("  Verifica el nombre exacto del archivo en Drive")
        
except Exception as e:
    print(f"  [ERROR] No se pudo listar archivos: {e}")
    import traceback
    print(traceback.format_exc())
    exit(1)

# Test 5: Verificar si factura 2070 existe en BD
print("\n[5/6] Verificando si factura 2070 existe en BD...")
from compras.models import Compra
try:
    compra = Compra.objects.filter(folio="2070").first()
    if compra:
        print(f"  [ADVERTENCIA] Factura 2070 YA existe en BD!")
        print(f"    ID: {compra.id}")
        print(f"    Folio: {compra.folio}")
        print(f"    Proveedor: {compra.proveedor}")
        print(f"    UUID: {compra.uuid}")
        print("\n  La factura NO se procesara (se detectara como duplicada)")
        print("\n  SOLUCION:")
        print("  1. Borrar completamente la factura del admin")
        print("  2. Verificar que no exista en la BD")
        print("  3. Intentar de nuevo")
    else:
        print("  [OK] Factura 2070 NO existe en BD (se puede procesar)")
except Exception as e:
    print(f"  [ERROR] Error al verificar BD: {e}")

# Test 6: Simular procesamiento (sin mover archivos)
print("\n[6/6] Simulando procesamiento (sin mover archivos)...")
if len(archivos) > 0:
    print("  [INFO] Procesando primer archivo de prueba...")
    try:
        archivo = archivos[0]
        print(f"  Archivo: {archivo['title']}")
        
        # Procesar SIN mover
        resultado = processor.process_pdf_file(archivo)
        
        print(f"\n  Resultado:")
        print(f"    Status: {resultado['status']}")
        print(f"    Folio: {resultado.get('folio', 'N/A')}")
        print(f"    Proveedor: {resultado.get('proveedor', 'N/A')}")
        
        if resultado['status'] == 'error':
            print(f"    Error: {resultado.get('error_text', 'N/A')}")
        elif resultado['status'] == 'duplicate':
            print(f"    [INFO] Factura duplicada (ya existe en BD)")
        else:
            print(f"    [OK] Factura procesada exitosamente")
            
    except Exception as e:
        print(f"  [ERROR] Error al procesar: {e}")
        import traceback
        print(traceback.format_exc())
else:
    print("  [SKIP] No hay archivos para probar")

print("\n" + "="*70)
print("DIAGNOSTICO COMPLETADO")
print("="*70 + "\n")
