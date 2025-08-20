import os
import tempfile
import django

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

from factura_parser import extract_invoice_data
from compras.utils.registrar_compra import registrar_compra_automatizada

# === CONFIGURACIÓN ===
FOLDER_ID = '1o9SkoeJ66qoBEbmyzXXhs1I67PQStTWV'
PROCESADOS_FOLDER_ID = None  # O usa el ID de tu carpeta 'procesados'

# === AUTENTICACIÓN GOOGLE DRIVE ===
def get_drive():
    gauth = GoogleAuth("settings.yaml")
    gauth.LoadCredentialsFile("token.json")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("token.json")
    return GoogleDrive(gauth)

# === VERIFICAR SI YA FUE PROCESADO ===
from compras.models import Compra

def is_processed(uuid):
    return Compra.objects.filter(uuid=uuid).exists()

# === PROCESAR ARCHIVO PDF ===
def process_pdf_file(file, temp_path):
    file.GetContentFile(temp_path)

    try:
        data = extract_invoice_data(temp_path)

        # Adjuntar UUID del archivo Drive como identificador único
        uuid = file['id']
        data['uuid'] = uuid

        # Validaciones mínimas
        if not data.get("folio"):
            raise ValueError("❌ No se encontró el folio en la factura.")
        if not data.get("fecha_emision"):
            if data.get("fecha"):
                data["fecha_emision"] = data["fecha"]  # 🛠️ Fix temporal automático
            else:
                raise ValueError("❌ No se encontró la fecha_emision ni la fecha en la factura.")

        if is_processed(uuid):
            print(f"⏩ Ya procesado: {file['title']}")
            return False

        # 💾 Guardar compra completa
        registrar_compra_automatizada(data)

        print(f"✅ Procesado: {file['title']}")
        return True

    except Exception as e:
        print(f"❌ Error procesando {file['title']}: {e}")
        return False


# === MOVER A CARPETA PROCESADOS (opcional) ===
def move_to_processed_folder(file):
    file['parents'] = [{'id': PROCESADOS_FOLDER_ID}]
    file.Upload()

# === FLUJO PRINCIPAL ===
def main():
    drive = get_drive()
    archivos = drive.ListFile({
        'q': f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
    }).GetList()

    total = len(archivos)
    procesados = 0
    ignorados = 0

    for archivo in archivos:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            exito = process_pdf_file(archivo, tmp.name)

        if exito:
            procesados += 1
            if PROCESADOS_FOLDER_ID:
                move_to_processed_folder(archivo)
        else:
            ignorados += 1

    print("\n📊 Resumen:")
    print(f"📄 Archivos revisados: {total}")
    print(f"📦 Nuevas compras registradas: {procesados}")
    print(f"⏩ Ya procesadas anteriormente o fallidas: {ignorados}")

if __name__ == "__main__":
    main()
