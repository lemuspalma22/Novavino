import os
import tempfile
import traceback  
import django

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# === Django setup ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

from compras.extractors.pdf_reader import extract_text_from_pdf  # 👈 IMPORT NECESARIO
from ventas.extractors.novavino import extraer_factura_novavino
from ventas.utils.registrar_venta import registrar_venta_automatizada
from ventas.models import Factura  # para deduplicar por folio

# === Config ===
FOLDER_ID_VENTAS = "1jhsWqGxrVPeokIUCzFjS_Q-0kDE4jI9r"  # <-- tu carpeta de ventas en Drive
PROCESADOS_FOLDER_ID = None  # si quieres moverlos tras procesar, pon el ID

def get_drive():
    gauth = GoogleAuth("settings.yaml")
    gauth.LoadCredentialsFile("token.json")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    else:
        try:
            if gauth.access_token_expired:
                gauth.Refresh()
            else:
                gauth.Authorize()
        except Exception:
            gauth.LocalWebserverAuth()
    gauth.SaveCredentialsFile("token.json")
    return GoogleDrive(gauth)

def already_processed(folio: str) -> bool:
    return Factura.objects.filter(folio_factura=str(folio).strip()).exists()

def process_pdf_file(file, temp_path) -> bool:
    file.GetContentFile(temp_path)
    try:
        # 1) Leer texto del PDF
        texto = extract_text_from_pdf(temp_path)

        # 2) Extraer datos de venta desde el texto
        data = extraer_factura_novavino(texto)

        # 3) Validaciones mínimas
        folio = data.get("folio")
        if not folio:
            raise ValueError("❌ No se encontró el folio en la factura de venta.")
        if already_processed(folio):
            print(f"⏩ Ya existe la venta con folio {folio}. Omitido: {file['title']}")
            return False

        # 4) Guardar en BD
        registrar_venta_automatizada(data)
        print(f"✅ Procesado: {file['title']} (folio {folio})")
        return True

    except Exception as e:
        print(f"❌ Error procesando {file['title']}: {e}")
        traceback.print_exc()
        return False

def move_to_processed_folder(file):
    if PROCESADOS_FOLDER_ID:
        file['parents'] = [{'id': PROCESADOS_FOLDER_ID}]
        file.Upload()

def main():
    drive = get_drive()
    archivos = drive.ListFile({
        'q': f"'{FOLDER_ID_VENTAS}' in parents and mimeType='application/pdf' and trashed=false"
    }).GetList()

    total = len(archivos)
    ok = 0
    skipped = 0

    for archivo in archivos:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            exito = process_pdf_file(archivo, tmp.name)
        if exito:
            ok += 1
            move_to_processed_folder(archivo)
        else:
            skipped += 1

    print("\n📊 Resumen ventas:")
    print(f"📄 PDFs revisados: {total}")
    print(f"🟢 Ventas registradas: {ok}")
    print(f"⏩ Omitidos / con error: {skipped}")

if __name__ == "__main__":
    main()
