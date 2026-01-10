import dotenv
dotenv.load_dotenv()
import os
import json
import tempfile
import traceback
from typing import Optional, Tuple, Any
from decimal import Decimal
from datetime import date, datetime

import django
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# ============================
# Django setup
# ============================
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

# ============================
# Domain imports
# ============================
from factura_parser import extract_invoice_data  # parser genérico ya existente
from compras.utils.registrar_compra import registrar_compra_automatizada
from compras.models import Compra, Proveedor
from django.db import transaction
from django.db.models import Q

# Validador (opcional, tolerante si existe)
try:
    from compras.utils.validate_invoice import validate_invoice
except Exception:
    validate_invoice = None

# Resolver alias de proveedor (opcional)
try:
    from compras.utils.proveedor_alias import resolve_alias as resolve_proveedor_alias  # type: ignore
except Exception:
    resolve_proveedor_alias = None

# Builder de productos para el registrador (cuando el extractor no trae productos)
from compras.utils.catalogo import ensure_product_list_for_registrar

# Extractor específico de Vieja Bodega (ya lo tienes en /extractors)
try:
    from compras.extractors import extract_vieja_bodega
except Exception:
    extract_vieja_bodega = None

# ============================
# Google Drive folders (IDs)
# ============================
ROOT_FOLDER_ID = os.getenv("COMPRAS_ROOT_ID", "1o9SkoeJ66qoBEbmyzXXhs1I67PQStTWV")            # "Facturas Prveedores"
NUEVAS_FOLDER_ID = os.getenv("COMPRAS_NUEVAS_ID", "1yQ4Jq2nQuJsKxxdoIJ2VLAjszSx19d4U")         # "Compras_Nuevas"
PROCESADAS_FOLDER_ID = os.getenv("COMPRAS_PROCESADAS_ID", "1k_1LT-J4foKRw2-pAYuAWBntmab6Yix7") # "Compras_Procesadas"
ERRORES_FOLDER_ID = os.getenv("COMPRAS_ERRORES_ID", "1YSo5L2VCoswN-vYr1kOCiTVctGp70ZV2")       # "Compras_Errores"

# Validación (por defecto lenient para no romper lo ya probado)
VALIDATION_MODE = os.getenv("VALIDATION_MODE", "lenient").lower()  # strict | lenient | off

# ============================
# Google Drive auth
# ============================
def get_drive() -> GoogleDrive:
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

# ============================
# Helpers
# ============================
def normalize_spaces(text):
    if isinstance(text, str):
        return " ".join(text.replace("\u00A0", " ").split()).strip()
    return text

def _extract_str_from_obj_or_dict(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        for k in ("nombre", "razon_social", "display_name", "rfc", "name"):
            val = v.get(k)
            if isinstance(val, str) and val.strip():
                return val
        return str(v)
    for attr in ("razon_social", "nombre", "display_name", "rfc", "name"):
        if hasattr(v, attr):
            val = getattr(v, attr, None)
            if isinstance(val, str) and val.strip():
                return val
    return str(v)

def normalize_proveedor(v) -> str:
    base = normalize_spaces(_extract_str_from_obj_or_dict(v)) or ""
    resolved = None
    if resolve_proveedor_alias:
        try:
            resolved = resolve_proveedor_alias(base)
            if resolved and not isinstance(resolved, str):
                resolved = _extract_str_from_obj_or_dict(resolved)
        except Exception:
            resolved = None
    return (resolved or base).upper()

def _model_has_field(model, field_name: str) -> bool:
    return any(getattr(f, "name", None) == field_name for f in model._meta.get_fields())

def is_duplicate(data: dict) -> bool:
    """Dedupe por uuid_sat/uuid; fallback por folio+proveedor+fecha."""
    try:
        uuid = (data.get("uuid_sat") or data.get("uuid") or "").strip()
        if uuid:
            if hasattr(Compra, "uuid_sat") and Compra.objects.filter(uuid_sat=uuid).exists():
                return True
            if Compra.objects.filter(uuid=uuid).exists():
                return True
    except Exception:
        pass
    try:
        folio = normalize_spaces(str(data.get("folio") or ""))
        proveedor = normalize_proveedor(data.get("proveedor"))
        fecha = normalize_spaces(str(data.get("fecha_emision") or ""))
        filters = {}
        if folio and _model_has_field(Compra, "folio"):
            filters["folio"] = folio
        if proveedor and _model_has_field(Compra, "proveedor_nombre"):
            filters["proveedor_nombre"] = proveedor
        if fecha and _model_has_field(Compra, "fecha_emision"):
            filters["fecha_emision"] = fecha
        if filters:
            return Compra.objects.filter(**filters).exists()
    except Exception:
        pass
    return False

def move_file(file, folder_id: str):
    if not folder_id:
        return
    file["parents"] = [{"id": folder_id}]
    file.Upload()

def _to_json_safe(obj: Any) -> Any:
    if isinstance(obj, (Decimal, date, datetime)):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_json_safe(x) for x in obj]
    return obj

def write_error_sidecar(drive: GoogleDrive, file_title: str, error_text: str, data_snapshot: Optional[dict] = None):
    # .error.txt
    sidecar = drive.CreateFile({
        "title": f"{file_title}.error.txt",
        "parents": [{"id": ERRORES_FOLDER_ID}],
        "mimeType": "text/plain",
    })
    sidecar.SetContentString(str(error_text))
    sidecar.Upload()
    # .data.json
    if data_snapshot is not None:
        try:
            safe = _to_json_safe(data_snapshot)
            sidecar_json = drive.CreateFile({
                "title": f"{file_title}.data.json",
                "parents": [{"id": ERRORES_FOLDER_ID}],
                "mimeType": "application/json",
            })
            sidecar_json.SetContentString(json.dumps(safe, ensure_ascii=False, indent=2))
            sidecar_json.Upload()
        except Exception:
            pass

# ============================
# Proveedor: resolver/crear instancia
# ============================
@transaction.atomic
def resolve_or_create_proveedor_instance(data: dict) -> Proveedor:
    """
    Devuelve/crea Proveedor a partir de data["proveedor"] (str/dict/obj) y data["rfc_emisor"].
    Side effects:
      - data["proveedor"] = instancia Proveedor (FK)
      - data["proveedor_nombre"] = nombre normalizado (str)
    """
    raw = data.get("proveedor")
    nombre_str = normalize_spaces(_extract_str_from_obj_or_dict(raw)) or ""
    nombre_norm = normalize_spaces(_extract_str_from_obj_or_dict(resolve_proveedor_alias(nombre_str) if resolve_proveedor_alias else nombre_str)) or ""
    rfc = (data.get("rfc_emisor") or "").strip().upper()

    prov = None
    if rfc and _model_has_field(Proveedor, "rfc"):
        prov = Proveedor.objects.filter(rfc=rfc).first()

    if prov is None and nombre_norm:
        qs = Proveedor.objects.all()
        cand = None
        if _model_has_field(Proveedor, "razon_social"):
            cand = qs.filter(razon_social__iexact=nombre_norm).first()
        if cand is None and _model_has_field(Proveedor, "nombre"):
            cand = qs.filter(nombre__iexact=nombre_norm).first()
        prov = cand

    if prov is None:
        create_kwargs = {}
        if _model_has_field(Proveedor, "razon_social") and nombre_norm:
            create_kwargs["razon_social"] = nombre_norm
        elif _model_has_field(Proveedor, "nombre") and nombre_norm:
            create_kwargs["nombre"] = nombre_norm
        if _model_has_field(Proveedor, "rfc") and rfc:
            create_kwargs["rfc"] = rfc
        if not create_kwargs:
            if _model_has_field(Proveedor, "nombre"):
                create_kwargs["nombre"] = nombre_norm or "PROVEEDOR DESCONOCIDO"
            elif _model_has_field(Proveedor, "razon_social"):
                create_kwargs["razon_social"] = nombre_norm or "PROVEEDOR DESCONOCIDO"
        prov = Proveedor.objects.create(**create_kwargs)

    data["proveedor"] = prov
    data["proveedor_nombre"] = nombre_norm or nombre_str or rfc or "DESCONOCIDO"
    return prov

# ============================
# Extractores por proveedor
# ============================
def try_vendor_extractors(pdf_path: str):
    """
    DEPRECADO: Esta función intentaba extraer por proveedor específico,
    pero ahora usamos factura_parser.py que ya maneja todos los proveedores.
    Se mantiene por compatibilidad pero siempre retorna None.
    """
    # Ya no intentamos extractores individuales aquí
    # El factura_parser.py maneja todos los proveedores correctamente
    return None

# ============================
# Core processing
# ============================
def process_pdf_file(drive: GoogleDrive, file, mode: str = VALIDATION_MODE) -> Tuple[str, str]:
    """
    Retorna (status, error_text)
      status ∈ {"success", "duplicate", "error"}
    """
    tmp_path = None
    data = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
        file.GetContentFile(tmp_path)

        # 1) Intentar extractor específico por proveedor
        data = try_vendor_extractors(tmp_path)

        # 2) Si no aplica, usar parser genérico
        if not data:
            data = extract_invoice_data(tmp_path) or {}

        # Metadatos útiles
        data["drive_file_id"] = file["id"]
        data["archivo_nombre"] = file["title"]

        # Si el extractor ya puso instancia de Proveedor, respétala
        if isinstance(data.get("proveedor"), Proveedor):
            data["proveedor_nombre"] = (
                data.get("proveedor_nombre")
                or getattr(data["proveedor"], "razon_social", None)
                or getattr(data["proveedor"], "nombre", None)
                or "DESCONOCIDO"
            )
        else:
            # Normaliza proveedor como string (para dedupe/log); la FK se resuelve después
            if data.get("proveedor") is not None:
                data["proveedor"] = normalize_proveedor(data["proveedor"])

        # Fallback de fecha
        if not data.get("fecha_emision") and data.get("fecha"):
            data["fecha_emision"] = data["fecha"]

        # Campo mínimo legacy
        if not data.get("folio"):
            raise ValueError("No se encontró 'folio' en la factura.")

        # ==== INYECCIÓN DEFENSIVA de productos a partir de conceptos ====
        from compras.utils.catalogo import ensure_product_list_for_registrar
        if not data.get("productos") and data.get("conceptos"):
            ensure_product_list_for_registrar(data, proveedor_nombre=data.get("proveedor_nombre", ""))
        if not data.get("productos") or not isinstance(data.get("productos"), list) or not data["productos"]:
            import logging
            logging.warning(f"[NOVAVINO] La factura {data.get('folio')}/{data.get('archivo_nombre')} NO tiene detalles/productos extraídos. Revisar extractor y PDF.")
        # ==== FIN INYECCIÓN ====

        # Validación (si existe módulo)
        if validate_invoice and mode != "off":
            try:
                validate_invoice(data, rfc_esperado=None, mode=mode)
            except TypeError:
                validate_invoice(data, rfc_esperado=None)

        # Dedupe
        if is_duplicate(data):
            print(f"Duplicada/Omitida: {file['title']}")
            return "duplicate", ""

        # Proveedor FK (si vino texto); si vino instancia, solo asegura proveedor_nombre
        if not isinstance(data.get("proveedor"), Proveedor):
            resolve_or_create_proveedor_instance(data)
        else:
            data["proveedor_nombre"] = (
                data.get("proveedor_nombre")
                or getattr(data["proveedor"], "razon_social", None)
                or getattr(data["proveedor"], "nombre", None)
                or "DESCONOCIDO"
            )

        # Productos:
        # - Si el extractor ya los trajo, NO tocar.
        # - Si vienen vacíos, construir lista para el registrador (y fallback POR CLASIFICAR si está activo).
        if not data.get("productos"):
            prov_nombre = (
                getattr(data.get("proveedor"), "razon_social", None)
                or getattr(data.get("proveedor"), "nombre", None)
                or data.get("proveedor_nombre")
                or ""
            )
            ensure_product_list_for_registrar(data, proveedor_nombre=prov_nombre)

        # Persistir (ideal: registrar_compra_automatizada devuelva la instancia)
        compra = registrar_compra_automatizada(data)

        print(f"Procesado: {file['title']}")
        return "success", ""

    except Exception as e:
        err_txt = f"{type(e).__name__}: {e}\n\nTRACE:\n{traceback.format_exc()}"
        print(f"Error procesando {file.get('title')}: {e}")
        try:
            write_error_sidecar(drive, file.get("title", "archivo_sin_nombre"), err_txt, data_snapshot=data)
        except Exception:
            pass
        return "error", err_txt
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

def list_pdfs_in_folder(drive: GoogleDrive, folder_id: str):
    return drive.ListFile({
        "q": f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    }).GetList()

def main():
    drive = get_drive()
    use_multi = bool(NUEVAS_FOLDER_ID)

    if use_multi:
        archivos = list_pdfs_in_folder(drive, NUEVAS_FOLDER_ID)
    else:
        archivos = list_pdfs_in_folder(drive, ROOT_FOLDER_ID)

    total = len(archivos)
    ok = skipped = failed = 0

    for archivo in archivos:
        status, _ = process_pdf_file(drive, archivo, mode=VALIDATION_MODE)

        if status == "success":
            ok += 1
            if use_multi:
                move_file(archivo, PROCESADAS_FOLDER_ID)
        elif status == "duplicate":
            skipped += 1
            if use_multi:
                move_file(archivo, PROCESADAS_FOLDER_ID)
        else:
            failed += 1
            if use_multi:
                move_file(archivo, ERRORES_FOLDER_ID)

    # ASCII puro (Windows-safe)
    print("\nResumen Compras:")
    print(f"PDFs revisados: {total}")
    print(f"Compras registradas: {ok}")
    print(f"Omitidos / duplicados: {skipped}")
    print(f"Errores: {failed}")
    print(f"VALIDATION_MODE={VALIDATION_MODE} | Multi-folder={'ON' if use_multi else 'OFF'}")

if __name__ == "__main__":
    main()
