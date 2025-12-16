"""
Script para reorganizar las carpetas de Facturas de Ventas en Google Drive.
Crea una carpeta padre "Facturas_Ventas" y mueve las 3 subcarpetas dentro.
"""
import os
import dotenv
dotenv.load_dotenv()
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# IDs actuales de las carpetas
FOLDER_ID_VENTAS_NUEVAS = "1jhsWqGxrVPeokIUCzFjS_Q-0kDE4jI9r"  # Facturas Ventas por Procesar (Nuevas)
PROCESADOS_FOLDER_ID = "19sDwsEL5xE4k-RQPQ18B-LEMwEv6tP1v"  # Procesadas
ERRORES_FOLDER_ID = "1f91IEc8lCW9nZA32qHW1c2L9FpAzWnqA"  # Errores

def get_drive():
    gauth = GoogleAuth("settings.yaml")
    try:
        gauth.LoadCredentialsFile("token.json")
    except Exception:
        pass
    
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    else:
        if gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
    
    gauth.SaveCredentialsFile("token.json")
    return GoogleDrive(gauth)

def get_folder_info(drive, folder_id):
    """Obtiene información de una carpeta."""
    try:
        folder = drive.CreateFile({'id': folder_id})
        folder.FetchMetadata()
        return {
            'id': folder['id'],
            'title': folder['title'],
            'parents': folder.get('parents', [])
        }
    except Exception as e:
        print(f"Error obteniendo info de {folder_id}: {e}")
        return None

def create_parent_folder(drive, parent_name="Facturas_Ventas"):
    """Crea la carpeta padre en la raíz de Drive."""
    folder_metadata = {
        'title': parent_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']

def move_folder(drive, folder_id, new_parent_id):
    """Mueve una carpeta a un nuevo padre."""
    try:
        folder = drive.CreateFile({'id': folder_id})
        folder.FetchMetadata()
        
        # Cambiar el padre
        folder['parents'] = [{'id': new_parent_id}]
        folder.Upload()
        return True
    except Exception as e:
        print(f"Error moviendo carpeta {folder_id}: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("REORGANIZACION DE CARPETAS DE VENTAS EN GOOGLE DRIVE")
    print("="*80)
    
    drive = get_drive()
    
    # 1. Verificar que las carpetas existen
    print("\n[1/4] Verificando carpetas existentes...")
    print("-"*80)
    
    nuevas_info = get_folder_info(drive, FOLDER_ID_VENTAS_NUEVAS)
    procesadas_info = get_folder_info(drive, PROCESADOS_FOLDER_ID)
    errores_info = get_folder_info(drive, ERRORES_FOLDER_ID)
    
    if not all([nuevas_info, procesadas_info, errores_info]):
        print("\n[ERROR] No se pudieron encontrar todas las carpetas.")
        print("Verifica los IDs en el script.")
        return
    
    print(f"  [OK] Nuevas: {nuevas_info['title']}")
    print(f"  [OK] Procesadas: {procesadas_info['title']}")
    print(f"  [OK] Errores: {errores_info['title']}")
    
    # 2. Crear carpeta padre
    print("\n[2/4] Creando carpeta padre 'Facturas_Ventas'...")
    print("-"*80)
    
    parent_folder_id = create_parent_folder(drive, "Facturas_Ventas")
    print(f"  [OK] Carpeta creada con ID: {parent_folder_id}")
    
    # 3. Mover las 3 subcarpetas
    print("\n[3/4] Moviendo subcarpetas...")
    print("-"*80)
    
    carpetas = [
        (FOLDER_ID_VENTAS_NUEVAS, "Nuevas"),
        (PROCESADOS_FOLDER_ID, "Procesadas"),
        (ERRORES_FOLDER_ID, "Errores")
    ]
    
    for folder_id, nombre in carpetas:
        print(f"  Moviendo {nombre}...", end=" ")
        if move_folder(drive, folder_id, parent_folder_id):
            print("[OK]")
        else:
            print("[ERROR]")
    
    # 4. Mostrar nuevas configuraciones
    print("\n[4/4] Nuevas configuraciones para el código:")
    print("-"*80)
    print("""
# Actualizar estas variables en el código:

# Carpeta padre (raíz de ventas)
VENTAS_ROOT_ID = "{root_id}"

# Subcarpetas (IDs no cambian, solo el padre)
VENTAS_NUEVAS_ID = "{nuevas_id}"
VENTAS_PROCESADAS_ID = "{procesadas_id}"
VENTAS_ERRORES_ID = "{errores_id}"
""".format(
        root_id=parent_folder_id,
        nuevas_id=FOLDER_ID_VENTAS_NUEVAS,
        procesadas_id=PROCESADOS_FOLDER_ID,
        errores_id=ERRORES_FOLDER_ID
    ))
    
    print("\n" + "="*80)
    print("COMPLETADO")
    print("="*80)
    print("""
Siguiente paso:
1. Ve a Google Drive y verifica que la estructura sea correcta:
   - Facturas_Ventas/
     - Facturas Ventas por Procesar (Nuevas)/
     - Procesadas/
     - Errores/

2. Copia los IDs de arriba y actualiza las variables de entorno (.env):
   VENTAS_ROOT_ID=...
   VENTAS_NUEVAS_ID=...
   VENTAS_PROCESADAS_ID=...
   VENTAS_ERRORES_ID=...

3. Continúa con la implementación del botón en admin.
""")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
