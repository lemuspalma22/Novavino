import dotenv
dotenv.load_dotenv()
import os
import tempfile
import traceback  
import django
import time
from typing import Optional, Dict
from decimal import Decimal, InvalidOperation
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from django.utils import timezone
from pydrive2.auth import RefreshError


# === Django setup ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

from compras.extractors.pdf_reader import extract_text_from_pdf  # 👈 IMPORT NECESARIO
from ventas.extractors.novavino import extraer_factura_novavino
from ventas.utils.registrar_venta import registrar_venta_automatizada
from ventas.models import Factura  # para deduplicar por folio

# === Config ===
FOLDER_ID_VENTAS = "1jhsWqGxrVPeokIUCzFjS_Q-0kDE4jI9r"  # <-- tu carpeta de ventas en Drive (Facturas Ventas por Procesar (Nuevas))
PROCESADOS_FOLDER_ID = "19sDwsEL5xE4k-RQPQ18B-LEMwEv6tP1v"  # si quieres moverlos tras procesar, pon el ID
ERRORES_FOLDER_ID = "1f91IEc8lCW9nZA32qHW1c2L9FpAzWnqA"          # ❌ opcional: carpeta destino en caso de error
RENAME_ON_MOVE = True 

def get_drive():
    gauth = GoogleAuth("settings.yaml")

    # Cargar credenciales previas si existen
    try:
        gauth.LoadCredentialsFile("token.json")
    except Exception:
        pass

    try:
        if gauth.credentials is None:
            # No hay token -> flujo local con navegador
            gauth.LocalWebserverAuth()
        else:
            try:
                # Hay token -> intenta refrescar
                if gauth.access_token_expired:
                    gauth.Refresh()
                else:
                    gauth.Authorize()
            except RefreshError:
                # Token inválido/revocado -> borra y reautentica
                try:
                    os.remove("token.json")
                except Exception:
                    pass
                gauth.LocalWebserverAuth()
    except Exception:
        # Fallback “sin navegador” (por si hay algún bloqueo del puerto localhost)
        gauth.CommandLineAuth()

    # Guarda credenciales buenas
    gauth.SaveCredentialsFile("token.json")
    return GoogleDrive(gauth)

def _move_with_retries(file, target_folder_id: str, new_title: Optional[str] = None,
                       props: Optional[Dict[str, str]] = None, max_retries: int = 3, sleep_base: float = 0.8):
    """
    Mueve un archivo a otra carpeta de Drive reemplazando padres.
    - Cambia el nombre si new_title no es None.
    - Agrega propiedades personalizadas si props no es None.
    - Reintenta en errores transitorios.
    """
    if not target_folder_id:
        return False

    for attempt in range(1, max_retries + 1):
        try:
            # Reemplaza TODOS los padres por el destino
            file['parents'] = [{'id': target_folder_id}]
            if new_title:
                file['title'] = new_title  # PyDrive2 usa 'title' como nombre
            if props:
                existing = file.get('properties') or {}
                existing.update({str(k): str(v) for k, v in props.items()})
                file['properties'] = existing
            file.Upload()  # aplica cambios
            return True
        except Exception as e:
            if attempt == max_retries:
                print(f"⚠️  No pude mover '{file.get('title')}' tras {attempt} intentos: {e}")
                return False
            time.sleep(sleep_base * attempt)  # backoff lineal simple
    return False

def move_to_processed_folder(file, folio: str, fecha_str: str = "") -> bool:
    """
    Mueve a la carpeta de PROCESADOS. Renombra a 'FOLIO_YYYYMMDD_nombre.pdf' si RENAME_ON_MOVE=True.
    """
    if not PROCESADOS_FOLDER_ID:
        return False
    base_title = file.get('title') or 'documento.pdf'
    new_title = None
    if RENAME_ON_MOVE:
        safe_fecha = fecha_str.replace("/", "-").replace(" ", "_") if fecha_str else ""
        prefix = f"{folio}_{safe_fecha}_".strip("_")
        new_title = f"{prefix}{base_title}"
    props = {"processed": "true", "folio": folio}
    return _move_with_retries(file, PROCESADOS_FOLDER_ID, new_title=new_title, props=props)

def move_to_error_folder(file, reason: str, folio: str = "") -> bool:
    """
    Mueve a carpeta de ERRORES con propiedad 'error_reason'.
    """
    if not ERRORES_FOLDER_ID:
        return False
    props = {"error_reason": reason}
    if folio:
        props["folio"] = folio
    return _move_with_retries(file, ERRORES_FOLDER_ID, new_title=None, props=props)

def process_pdf_file(file, temp_path) -> bool:
    file.GetContentFile(temp_path)
    try:
        # 1) Leer texto del PDF
        texto = extract_text_from_pdf(temp_path)

        # 2) Extraer datos
        data = extraer_factura_novavino(texto)

        folio = (data.get("folio") or "").strip()
        if not folio:
            raise ValueError("❌ No se encontró el folio en la factura de venta.")

        # (opcional) fecha para renombrado
        fecha_emision = (data.get("fecha_emision") or data.get("fecha") or "") or str(timezone.now().date())

        # 3) Registrar venta con idempotencia por REEMPLAZO
        registrar_venta_automatizada(data, replace_if_exists=True)

        print(f"✅ Procesado: {file['title']} (folio {folio})")

        # 4) Mover a PROCESADOS (si configuraste el ID)
        moved = move_to_processed_folder(file, folio, fecha_str=str(fecha_emision))
        if moved:
            print(f"📦 Movido a PROCESADOS: {file.get('title')}")
        else:
            if PROCESADOS_FOLDER_ID:
                print("⚠️  No se pudo mover a PROCESADOS (revisar permisos/ID).")

        return True

    except Exception as e:
        reason = str(e)
        print(f"❌ Error procesando {file['title']}: {reason}")
        traceback.print_exc()

        # 5) Mover a ERRORES (si configuraste el ID)
        try:
            folio = (data.get("folio") or "").strip() if 'data' in locals() and isinstance(data, dict) else ""
        except Exception:
            folio = ""
        moved_err = move_to_error_folder(file, reason=reason[:200], folio=folio)
        if moved_err:
            print(f"🧩 Movido a ERRORES: {file.get('title')}")
        else:
            if ERRORES_FOLDER_ID:
                print("⚠️  No se pudo mover a ERRORES (revisar permisos/ID).")

        return False

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
        else:
            skipped += 1

    print("\n📊 Resumen ventas:")
    print(f"📄 PDFs revisados: {total}")
    print(f"🟢 Ventas registradas: {ok}")
    print(f"⏩ Omitidos / con error: {skipped}")


if __name__ == "__main__":
    main()
