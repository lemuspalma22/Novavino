"""
Módulo para procesar facturas desde Google Drive.
Refactorización del script process_drive_invoices.py para uso desde Django Admin.
"""
import os
import json
import tempfile
import traceback
from typing import Optional, Tuple, Any, Dict, List
from decimal import Decimal
from datetime import date, datetime

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from factura_parser import extract_invoice_data
from compras.utils.registrar_compra import registrar_compra_automatizada
from compras.models import Compra, Proveedor
from django.db import transaction

# Validador (opcional)
try:
    from compras.utils.validate_invoice import validate_invoice
except Exception:
    validate_invoice = None

# Resolver alias de proveedor (opcional)
try:
    from compras.utils.proveedor_alias import resolve_alias as resolve_proveedor_alias
except Exception:
    resolve_proveedor_alias = None

# Builder de productos
from compras.utils.catalogo import ensure_product_list_for_registrar


class DriveInvoiceProcessor:
    """Procesador de facturas desde Google Drive."""
    
    def __init__(
        self,
        root_folder_id: str = None,
        nuevas_folder_id: str = None,
        procesadas_folder_id: str = None,
        errores_folder_id: str = None,
        validation_mode: str = "lenient"
    ):
        """
        Args:
            root_folder_id: ID de carpeta raíz "Facturas Proveedores"
            nuevas_folder_id: ID de carpeta "Compras_Nuevas"
            procesadas_folder_id: ID de carpeta "Compras_Procesadas"
            errores_folder_id: ID de carpeta "Compras_Errores"
            validation_mode: "strict", "lenient" o "off"
        """
        self.root_folder_id = root_folder_id or os.getenv("COMPRAS_ROOT_ID", "1o9SkoeJ66qoBEbmyzXXhs1I67PQStTWV")
        self.nuevas_folder_id = nuevas_folder_id or os.getenv("COMPRAS_NUEVAS_ID", "1yQ4Jq2nQuJsKxxdoIJ2VLAjszSx19d4U")
        self.procesadas_folder_id = procesadas_folder_id or os.getenv("COMPRAS_PROCESADAS_ID", "1k_1LT-J4foKRw2-pAYuAWBntmab6Yix7")
        self.errores_folder_id = errores_folder_id or os.getenv("COMPRAS_ERRORES_ID", "1YSo5L2VCoswN-vYr1kOCiTVctGp70ZV2")
        self.validation_mode = validation_mode
        self.drive = None
        
    def get_drive(self) -> GoogleDrive:
        """Obtiene instancia autenticada de Google Drive."""
        if self.drive:
            return self.drive
            
        gauth = GoogleAuth("settings.yaml")
        gauth.LoadCredentialsFile("token.json")
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
        gauth.SaveCredentialsFile("token.json")
        self.drive = GoogleDrive(gauth)
        return self.drive
    
    def normalize_spaces(self, text):
        """Normaliza espacios en texto."""
        if isinstance(text, str):
            return " ".join(text.replace("\u00A0", " ").split()).strip()
        return text
    
    def _extract_str_from_obj_or_dict(self, v) -> str:
        """Extrae string de objeto o diccionario."""
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
    
    def normalize_proveedor(self, v) -> str:
        """Normaliza nombre de proveedor."""
        base = self.normalize_spaces(self._extract_str_from_obj_or_dict(v)) or ""
        resolved = None
        if resolve_proveedor_alias:
            try:
                resolved = resolve_proveedor_alias(base)
                if resolved and not isinstance(resolved, str):
                    resolved = self._extract_str_from_obj_or_dict(resolved)
            except Exception:
                resolved = None
        return (resolved or base).upper()
    
    def _model_has_field(self, model, field_name: str) -> bool:
        """Verifica si un modelo tiene un campo."""
        return any(getattr(f, "name", None) == field_name for f in model._meta.get_fields())
    
    def is_duplicate(self, data: dict) -> bool:
        """Verifica si una factura ya existe en la BD."""
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
            folio = self.normalize_spaces(str(data.get("folio") or ""))
            proveedor = self.normalize_proveedor(data.get("proveedor"))
            fecha = self.normalize_spaces(str(data.get("fecha_emision") or ""))
            filters = {}
            if folio and self._model_has_field(Compra, "folio"):
                filters["folio"] = folio
            if proveedor and self._model_has_field(Compra, "proveedor_nombre"):
                filters["proveedor_nombre"] = proveedor
            if fecha and self._model_has_field(Compra, "fecha_emision"):
                filters["fecha_emision"] = fecha
            if filters:
                return Compra.objects.filter(**filters).exists()
        except Exception:
            pass
        return False
    
    def move_file(self, file, folder_id: str):
        """Mueve un archivo a otra carpeta de Drive."""
        if not folder_id:
            return
        file["parents"] = [{"id": folder_id}]
        file.Upload()
    
    def _to_json_safe(self, obj: Any) -> Any:
        """Convierte objetos a formato JSON-safe."""
        if isinstance(obj, (Decimal, date, datetime)):
            return str(obj)
        if isinstance(obj, dict):
            return {k: self._to_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [self._to_json_safe(x) for x in obj]
        return obj
    
    def write_error_sidecar(self, file_title: str, error_text: str, data_snapshot: Optional[dict] = None):
        """Escribe archivo de error en carpeta de errores."""
        drive = self.get_drive()
        # .error.txt
        sidecar = drive.CreateFile({
            "title": f"{file_title}.error.txt",
            "parents": [{"id": self.errores_folder_id}],
            "mimeType": "text/plain",
        })
        sidecar.SetContentString(str(error_text))
        sidecar.Upload()
        # .data.json
        if data_snapshot is not None:
            try:
                safe = self._to_json_safe(data_snapshot)
                sidecar_json = drive.CreateFile({
                    "title": f"{file_title}.data.json",
                    "parents": [{"id": self.errores_folder_id}],
                    "mimeType": "application/json",
                })
                sidecar_json.SetContentString(json.dumps(safe, ensure_ascii=False, indent=2))
                sidecar_json.Upload()
            except Exception:
                pass
    
    @transaction.atomic
    def resolve_or_create_proveedor_instance(self, data: dict) -> Proveedor:
        """
        Devuelve/crea Proveedor a partir de data["proveedor"] y data["rfc_emisor"].
        Side effects:
          - data["proveedor"] = instancia Proveedor (FK)
          - data["proveedor_nombre"] = nombre normalizado (str)
        """
        raw = data.get("proveedor")
        nombre_str = self.normalize_spaces(self._extract_str_from_obj_or_dict(raw)) or ""
        nombre_norm = self.normalize_spaces(self._extract_str_from_obj_or_dict(
            resolve_proveedor_alias(nombre_str) if resolve_proveedor_alias else nombre_str
        )) or ""
        rfc = (data.get("rfc_emisor") or "").strip().upper()

        prov = None
        if rfc and self._model_has_field(Proveedor, "rfc"):
            prov = Proveedor.objects.filter(rfc=rfc).first()

        if prov is None and nombre_norm:
            qs = Proveedor.objects.all()
            cand = None
            if self._model_has_field(Proveedor, "razon_social"):
                cand = qs.filter(razon_social__iexact=nombre_norm).first()
            if cand is None and self._model_has_field(Proveedor, "nombre"):
                cand = qs.filter(nombre__iexact=nombre_norm).first()
            prov = cand

        if prov is None:
            create_kwargs = {}
            if self._model_has_field(Proveedor, "razon_social") and nombre_norm:
                create_kwargs["razon_social"] = nombre_norm
            elif self._model_has_field(Proveedor, "nombre") and nombre_norm:
                create_kwargs["nombre"] = nombre_norm
            if self._model_has_field(Proveedor, "rfc") and rfc:
                create_kwargs["rfc"] = rfc
            if not create_kwargs:
                if self._model_has_field(Proveedor, "nombre"):
                    create_kwargs["nombre"] = nombre_norm or "PROVEEDOR DESCONOCIDO"
                elif self._model_has_field(Proveedor, "razon_social"):
                    create_kwargs["razon_social"] = nombre_norm or "PROVEEDOR DESCONOCIDO"
            prov = Proveedor.objects.create(**create_kwargs)

        data["proveedor"] = prov
        data["proveedor_nombre"] = nombre_norm or nombre_str or rfc or "DESCONOCIDO"
        return prov
    
    def process_pdf_file(self, file) -> Dict[str, Any]:
        """
        Procesa un archivo PDF de factura.
        
        Returns:
            Dict con:
                - status: "success", "duplicate" o "error"
                - error_text: texto del error si status == "error"
                - file_title: nombre del archivo
                - folio: folio de la factura (si se extrajo)
                - proveedor: nombre del proveedor (si se extrajo)
        """
        tmp_path = None
        data = None
        result = {
            "status": "error",
            "error_text": "",
            "file_title": file.get("title", "Sin nombre"),
            "folio": None,
            "proveedor": None
        }
        
        try:
            # Descargar archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp_path = tmp.name
            file.GetContentFile(tmp_path)

            # Extraer datos
            data = extract_invoice_data(tmp_path) or {}

            # Metadatos
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
                # Normaliza proveedor como string
                if data.get("proveedor") is not None:
                    data["proveedor"] = self.normalize_proveedor(data["proveedor"])

            # Fallback de fecha
            if not data.get("fecha_emision") and data.get("fecha"):
                data["fecha_emision"] = data["fecha"]

            # Campo mínimo
            if not data.get("folio"):
                raise ValueError("No se encontró 'folio' en la factura.")

            # Guardar para resultado
            result["folio"] = data.get("folio")
            result["proveedor"] = data.get("proveedor_nombre") or str(data.get("proveedor", ""))

            # Inyección de productos
            if not data.get("productos") and data.get("conceptos"):
                ensure_product_list_for_registrar(data, proveedor_nombre=data.get("proveedor_nombre", ""))

            # Validación
            if validate_invoice and self.validation_mode != "off":
                try:
                    validate_invoice(data, rfc_esperado=None, mode=self.validation_mode)
                except TypeError:
                    validate_invoice(data, rfc_esperado=None)

            # Dedupe
            if self.is_duplicate(data):
                result["status"] = "duplicate"
                return result

            # Proveedor FK
            if not isinstance(data.get("proveedor"), Proveedor):
                self.resolve_or_create_proveedor_instance(data)
            else:
                data["proveedor_nombre"] = (
                    data.get("proveedor_nombre")
                    or getattr(data["proveedor"], "razon_social", None)
                    or getattr(data["proveedor"], "nombre", None)
                    or "DESCONOCIDO"
                )

            # Productos
            if not data.get("productos"):
                prov_nombre = (
                    getattr(data.get("proveedor"), "razon_social", None)
                    or getattr(data.get("proveedor"), "nombre", None)
                    or data.get("proveedor_nombre")
                    or ""
                )
                ensure_product_list_for_registrar(data, proveedor_nombre=prov_nombre)

            # Registrar en BD
            compra = registrar_compra_automatizada(data)
            result["status"] = "success"
            return result

        except Exception as e:
            err_txt = f"{type(e).__name__}: {e}\n\nTRACE:\n{traceback.format_exc()}"
            result["error_text"] = str(e)
            try:
                self.write_error_sidecar(file.get("title", "archivo_sin_nombre"), err_txt, data_snapshot=data)
            except Exception:
                pass
            return result
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
    
    def list_pdfs_in_folder(self, folder_id: str) -> List:
        """Lista PDFs en una carpeta de Drive."""
        drive = self.get_drive()
        return drive.ListFile({
            "q": f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        }).GetList()
    
    def process_all_invoices(self, move_files: bool = True) -> Dict[str, Any]:
        """
        Procesa todas las facturas pendientes.
        
        Args:
            move_files: Si True, mueve archivos según resultado
            
        Returns:
            Dict con resumen de procesamiento:
                - total: total de archivos
                - success: archivos procesados exitosamente
                - duplicate: archivos duplicados
                - error: archivos con errores
                - details: lista de detalles por archivo
        """
        drive = self.get_drive()
        use_multi = bool(self.nuevas_folder_id)
        
        # Log de configuración para debugging
        print(f"[DRIVE] Configuración:")
        print(f"  - move_files: {move_files}")
        print(f"  - use_multi: {use_multi}")
        print(f"  - nuevas_folder_id: {self.nuevas_folder_id[:20] if self.nuevas_folder_id else 'None'}...")
        print(f"  - procesadas_folder_id: {self.procesadas_folder_id[:20] if self.procesadas_folder_id else 'None'}...")
        
        if use_multi:
            archivos = self.list_pdfs_in_folder(self.nuevas_folder_id)
        else:
            archivos = self.list_pdfs_in_folder(self.root_folder_id)
        
        total = len(archivos)
        success_count = 0
        duplicate_count = 0
        error_count = 0
        details = []
        
        print(f"[DRIVE] Encontrados {total} archivo(s) para procesar")
        
        for archivo in archivos:
            result = self.process_pdf_file(archivo)
            
            detail = {
                "file": result["file_title"],
                "status": result["status"],
                "folio": result.get("folio"),
                "proveedor": result.get("proveedor"),
                "error": result.get("error_text", "")
            }
            details.append(detail)
            
            if result["status"] == "success":
                success_count += 1
                if move_files and use_multi:
                    try:
                        print(f"[DRIVE] Moviendo {archivo['title']} a Procesadas...")
                        self.move_file(archivo, self.procesadas_folder_id)
                        print(f"[DRIVE] ✓ Movido exitosamente")
                    except Exception as e:
                        print(f"[DRIVE] ✗ Error al mover: {e}")
                        import traceback
                        traceback.print_exc()
            elif result["status"] == "duplicate":
                duplicate_count += 1
                if move_files and use_multi:
                    try:
                        print(f"[DRIVE] Moviendo {archivo['title']} (duplicado) a Procesadas...")
                        self.move_file(archivo, self.procesadas_folder_id)
                        print(f"[DRIVE] ✓ Movido exitosamente")
                    except Exception as e:
                        print(f"[DRIVE] ✗ Error al mover: {e}")
                        import traceback
                        traceback.print_exc()
            else:
                error_count += 1
                if move_files and use_multi:
                    try:
                        print(f"[DRIVE] Moviendo {archivo['title']} a Errores...")
                        self.move_file(archivo, self.errores_folder_id)
                        print(f"[DRIVE] ✓ Movido exitosamente")
                    except Exception as e:
                        print(f"[DRIVE] ✗ Error al mover: {e}")
                        import traceback
                        traceback.print_exc()
        
        return {
            "total": total,
            "success": success_count,
            "duplicate": duplicate_count,
            "error": error_count,
            "details": details,
            "validation_mode": self.validation_mode,
            "multi_folder": use_multi
        }


# Función de conveniencia para compatibilidad con script existente
def process_drive_invoices(validation_mode: str = "lenient") -> Dict[str, Any]:
    """
    Función helper para procesar facturas desde Google Drive.
    
    Args:
        validation_mode: "strict", "lenient" o "off"
        
    Returns:
        Dict con resumen de procesamiento
    """
    processor = DriveInvoiceProcessor(validation_mode=validation_mode)
    return processor.process_all_invoices(move_files=True)
