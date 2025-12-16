"""
Procesador de facturas de ventas desde Google Drive.
Similar a compras/utils/drive_processor.py pero para ventas.
"""
import os
import tempfile
import traceback
from typing import Optional, Dict, List
from decimal import Decimal
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.auth import RefreshError
from django.utils import timezone

from compras.extractors.pdf_reader import extract_text_from_pdf
from ventas.extractors.novavino import extraer_factura_novavino
from ventas.utils.registrar_venta import registrar_venta_automatizada


class DriveVentasProcessor:
    """
    Procesa facturas de ventas desde Google Drive.
    """
    
    def __init__(self):
        """Inicializa el procesador con las configuraciones de las carpetas."""
        self.root_folder_id = os.getenv("VENTAS_ROOT_ID", "")
        self.nuevas_folder_id = os.getenv("VENTAS_NUEVAS_ID", "")
        self.procesadas_folder_id = os.getenv("VENTAS_PROCESADAS_ID", "")
        self.errores_folder_id = os.getenv("VENTAS_ERRORES_ID", "")
        
        # Verificar configuración
        if not all([self.nuevas_folder_id, self.procesadas_folder_id, self.errores_folder_id]):
            raise ValueError(
                "Faltan variables de entorno para Google Drive. "
                "Asegúrate de tener: VENTAS_NUEVAS_ID, VENTAS_PROCESADAS_ID, VENTAS_ERRORES_ID"
            )
    
    def get_drive(self):
        """Obtiene una instancia autenticada de Google Drive."""
        gauth = GoogleAuth("settings.yaml")
        
        try:
            gauth.LoadCredentialsFile("token.json")
        except Exception:
            pass
        
        try:
            if gauth.credentials is None:
                gauth.LocalWebserverAuth()
            else:
                try:
                    if gauth.access_token_expired:
                        gauth.Refresh()
                    else:
                        gauth.Authorize()
                except RefreshError:
                    try:
                        os.remove("token.json")
                    except Exception:
                        pass
                    gauth.LocalWebserverAuth()
        except Exception:
            gauth.CommandLineAuth()
        
        gauth.SaveCredentialsFile("token.json")
        return GoogleDrive(gauth)
    
    def list_pdfs_in_folder(self, folder_id: str) -> List:
        """Lista todos los PDFs en una carpeta de Drive."""
        drive = self.get_drive()
        query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        return drive.ListFile({'q': query}).GetList()
    
    def move_file(self, file, target_folder_id: str):
        """Mueve un archivo a otra carpeta en Drive."""
        file['parents'] = [{'id': target_folder_id}]
        file.Upload()
    
    def process_pdf_file(self, archivo, move_files=True) -> Dict:
        """
        Procesa un único PDF de factura de venta.
        
        Returns:
            dict con: status ('success', 'duplicate', 'error'), file, folio, error
        """
        filename = archivo.get('title', 'sin_nombre.pdf')
        
        try:
            # Descargar PDF temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp_path = tmp.name
                archivo.GetContentFile(tmp_path)
            
            try:
                # 1) Extraer texto
                texto = extract_text_from_pdf(tmp_path)
                
                # 2) Extraer datos con extractor de Novavino
                data = extraer_factura_novavino(texto)
                
                folio = (data.get("folio") or "").strip()
                if not folio:
                    raise ValueError("No se encontró el folio en la factura de venta.")
                
                # 3) Registrar venta (con reemplazo si ya existe)
                resultado = registrar_venta_automatizada(data, replace_if_exists=True)
                
                print(f"[VENTAS] ✓ Procesado: {filename} (folio {folio})")
                
                return {
                    "status": "success",
                    "file": filename,
                    "folio": folio,
                    "error": None
                }
                
            finally:
                # Limpiar archivo temporal
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        
        except Exception as e:
            error_msg = str(e)
            print(f"[VENTAS] ✗ Error procesando {filename}: {error_msg}")
            traceback.print_exc()
            
            return {
                "status": "error",
                "file": filename,
                "folio": None,
                "error": error_msg
            }
    
    def process_all_invoices(self, move_files=True) -> Dict:
        """
        Procesa todas las facturas de venta pendientes desde Google Drive.
        
        Args:
            move_files: Si True, mueve archivos a carpetas correspondientes
        
        Returns:
            dict con totales y detalles del procesamiento
        """
        drive = self.get_drive()
        
        # Log de configuración
        print(f"[VENTAS] Configuración:")
        print(f"  - move_files: {move_files}")
        print(f"  - nuevas_folder_id: {self.nuevas_folder_id[:20]}...")
        print(f"  - procesadas_folder_id: {self.procesadas_folder_id[:20]}...")
        
        # Listar PDFs en carpeta de nuevas
        archivos = self.list_pdfs_in_folder(self.nuevas_folder_id)
        
        total = len(archivos)
        success_count = 0
        error_count = 0
        details = []
        
        print(f"[VENTAS] Encontrados {total} archivo(s) para procesar")
        
        for archivo in archivos:
            result = self.process_pdf_file(archivo, move_files=move_files)
            details.append(result)
            
            if result["status"] == "success":
                success_count += 1
                if move_files:
                    try:
                        print(f"[VENTAS] Moviendo {archivo['title']} a Procesadas...")
                        self.move_file(archivo, self.procesadas_folder_id)
                        print(f"[VENTAS] ✓ Movido exitosamente")
                    except Exception as e:
                        print(f"[VENTAS] ✗ Error al mover: {e}")
                        traceback.print_exc()
            else:
                error_count += 1
                if move_files:
                    try:
                        print(f"[VENTAS] Moviendo {archivo['title']} a Errores...")
                        self.move_file(archivo, self.errores_folder_id)
                        print(f"[VENTAS] ✓ Movido exitosamente")
                    except Exception as e:
                        print(f"[VENTAS] ✗ Error al mover: {e}")
                        traceback.print_exc()
        
        return {
            "total": total,
            "success": success_count,
            "error": error_count,
            "details": details
        }
