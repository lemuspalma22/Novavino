"""
Script para verificar si los archivos se están moviendo correctamente.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

import dotenv
dotenv.load_dotenv()

from compras.utils.drive_processor import DriveInvoiceProcessor

print("\n" + "="*70)
print("VERIFICAR MOVIMIENTO DE ARCHIVOS EN DRIVE")
print("="*70)

processor = DriveInvoiceProcessor()

NUEVAS_FOLDER_ID = os.getenv("COMPRAS_NUEVAS_ID", "1yQ4Jq2nQuJsKxxdoIJ2VLAjszSx19d4U")
PROCESADAS_FOLDER_ID = os.getenv("COMPRAS_PROCESADAS_ID", "1k_1LT-J4foKRw2-pAYuAWBntmab6Yix7")
ERRORES_FOLDER_ID = os.getenv("COMPRAS_ERRORES_ID", "1YSo5L2VCoswN-vYr1kOCiTVctGp70ZV2")

print(f"\nCarpeta NUEVAS: {NUEVAS_FOLDER_ID}")
print(f"Carpeta PROCESADAS: {PROCESADAS_FOLDER_ID}")
print(f"Carpeta ERRORES: {ERRORES_FOLDER_ID}")

# Listar archivos en NUEVAS
print("\n[1/2] Listando archivos en 'Compras_Nuevas'...")
archivos_nuevas = processor.list_pdfs_in_folder(NUEVAS_FOLDER_ID)
print(f"  Archivos encontrados: {len(archivos_nuevas)}")
for archivo in archivos_nuevas:
    print(f"    - {archivo['title']}")

if len(archivos_nuevas) > 0:
    print("\n  [ENCONTRADO] Hay archivos en 'Compras_Nuevas'")
    print("  ESTO SIGNIFICA: El archivo NO se movio despues del procesamiento")
else:
    print("\n  [OK] Carpeta 'Compras_Nuevas' esta vacia")
    print("  ESTO SIGNIFICA: Los archivos se movieron correctamente")

# Listar archivos en PROCESADAS
print("\n[2/2] Listando archivos en 'Compras_Procesadas'...")
archivos_procesadas = processor.list_pdfs_in_folder(PROCESADAS_FOLDER_ID)
print(f"  Archivos encontrados: {len(archivos_procesadas)}")
if len(archivos_procesadas) > 0:
    print("  Ultimos 5 archivos:")
    for archivo in archivos_procesadas[-5:]:
        print(f"    - {archivo['title']}")

# Verificar específicamente factura 2470
print("\n[DIAGNOSTICO] Buscando factura 2470...")
factura_en_nuevas = any("2470" in a['title'] for a in archivos_nuevas)
factura_en_procesadas = any("2470" in a['title'] for a in archivos_procesadas)

if factura_en_nuevas:
    print("  [PROBLEMA] Factura 2470 SIGUE en 'Compras_Nuevas'")
    print("  El archivo NO se movio despues del procesamiento")
elif factura_en_procesadas:
    print("  [OK] Factura 2470 ESTA en 'Compras_Procesadas'")
    print("  El archivo se movio correctamente")
else:
    print("  [?] Factura 2470 NO encontrada en ninguna carpeta")

print("\n" + "="*70)
print("DIAGNOSTICO")
print("="*70)

if factura_en_nuevas:
    print("\n[PROBLEMA DETECTADO]")
    print("El archivo 2470 no se movio a 'Compras_Procesadas'")
    print("\nPOSIBLES CAUSAS:")
    print("1. El parametro move_files=True no esta funcionando")
    print("2. Falta permisos en Drive")
    print("3. Error silencioso en move_file()")
    print("\nSOLUCION:")
    print("Voy a revisar el codigo del procesador...")
else:
    print("\n[OK] Todo funciona correctamente")

print("\n" + "="*70 + "\n")
