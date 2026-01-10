# ventas/utils/procesar_complemento.py
from decimal import Decimal
from django.db import transaction
from django.core.files import File
from ventas.models import Factura, ComplementoPago, DocumentoRelacionado
from ventas.extractors.complemento_pago import extract_complemento_from_pdf
from ventas.utils.vinculador_complementos import vincular_complemento


class ProcesadorComplemento:
    """
    Procesador completo para complementos de pago:
    1. Extrae datos del PDF
    2. Crea ComplementoPago y DocumentoRelacionado
    3. Vincula automáticamente con PagoFactura existentes
    4. Aplica guardians (facturas inexistentes, duplicados, etc.)
    """
    
    def __init__(self, pdf_path: str, guardar_archivo: bool = True):
        self.pdf_path = pdf_path
        self.guardar_archivo = guardar_archivo
        self.data_extraida = None
        self.complemento = None
        self.errores = []
        self.warnings = []
    
    def procesar(self) -> dict:
        """
        Procesa el PDF y crea el complemento con vinculación automática.
        
        Returns:
            dict con resultado:
            {
                "success": bool,
                "complemento": ComplementoPago | None,
                "vinculacion": dict,
                "errores": list[str],
                "warnings": list[str]
            }
        """
        try:
            # Paso 1: Extraer datos del PDF
            if not self._extraer_datos():
                return self._resultado_error("Error al extraer datos del PDF")
            
            # Paso 2: Aplicar guardians
            if not self._aplicar_guardians():
                return self._resultado_error("Falló validación de guardians")
            
            # Paso 3: Crear complemento y documentos relacionados
            with transaction.atomic():
                if not self._crear_complemento():
                    return self._resultado_error("Error al crear el complemento")
                
                if not self._crear_documentos_relacionados():
                    return self._resultado_error("Error al crear documentos relacionados")
            
            # Paso 4: Vincular automáticamente con pagos existentes
            resultado_vinculacion = vincular_complemento(self.complemento)
            
            return {
                "success": True,
                "complemento": self.complemento,
                "vinculacion": resultado_vinculacion,
                "errores": self.errores,
                "warnings": self.warnings
            }
        
        except Exception as e:
            self.errores.append(f"Error inesperado: {str(e)}")
            return self._resultado_error(str(e))
    
    def _extraer_datos(self) -> bool:
        """Extrae datos del PDF."""
        try:
            self.data_extraida = extract_complemento_from_pdf(self.pdf_path)
            
            # Validar datos mínimos
            if not self.data_extraida.get("folio"):
                self.errores.append("No se pudo extraer el folio del complemento")
                return False
            
            if not self.data_extraida.get("uuid"):
                self.errores.append("No se pudo extraer el UUID del complemento")
                return False
            
            if not self.data_extraida.get("documentos_relacionados"):
                self.errores.append("No se encontraron documentos relacionados en el complemento")
                return False
            
            return True
        
        except Exception as e:
            self.errores.append(f"Error al extraer PDF: {str(e)}")
            return False
    
    def _aplicar_guardians(self) -> bool:
        """Aplica validaciones de guardian."""
        
        # Guardian 1: Verificar que el complemento no exista ya
        if ComplementoPago.objects.filter(uuid_complemento=self.data_extraida["uuid"]).exists():
            self.errores.append(
                f"❌ GUARDIAN: El complemento con UUID {self.data_extraida['uuid']} "
                f"ya existe en el sistema"
            )
            return False
        
        if ComplementoPago.objects.filter(folio_complemento=self.data_extraida["folio"]).exists():
            self.errores.append(
                f"❌ GUARDIAN: Ya existe un complemento con folio {self.data_extraida['folio']}"
            )
            return False
        
        # Guardian 2: Verificar que las facturas relacionadas existan
        for doc in self.data_extraida["documentos_relacionados"]:
            uuid_factura = doc.get("uuid_factura")
            folio_factura = doc.get("folio_factura")
            
            # Buscar por UUID primero
            factura = None
            if uuid_factura:
                factura = Factura.objects.filter(uuid_factura=uuid_factura).first()
            
            # Fallback: buscar por folio
            if not factura and folio_factura:
                factura = Factura.objects.filter(folio_factura=folio_factura).first()
            
            if not factura:
                self.errores.append(
                    f"❌ GUARDIAN: Complemento paga factura inexistente\n"
                    f"   Folio: {folio_factura}\n"
                    f"   UUID: {uuid_factura}\n"
                    f"   → Esta factura NO existe en el sistema"
                )
                return False
            
            # Guardian 3: Validar que la factura sea PPD
            if factura.metodo_pago != 'PPD':
                self.warnings.append(
                    f"⚠️ WARNING: Factura {folio_factura} tiene método de pago "
                    f"'{factura.metodo_pago}', se esperaba 'PPD'"
                )
        
        return True
    
    def _crear_complemento(self) -> bool:
        """Crea el ComplementoPago en la BD."""
        try:
            self.complemento = ComplementoPago.objects.create(
                folio_complemento=self.data_extraida["folio"],
                uuid_complemento=self.data_extraida["uuid"],
                fecha_emision=self.data_extraida["fecha_emision"],
                fecha_pago=self.data_extraida["fecha_pago"],
                monto_total=self.data_extraida["monto"],
                forma_pago_sat=self.data_extraida["forma_pago"] or "99",
                cliente=self.data_extraida["cliente"] or "CLIENTE DESCONOCIDO",
                rfc_cliente=self.data_extraida.get("rfc_cliente")
            )
            
            # Guardar archivo PDF si se solicita
            if self.guardar_archivo:
                with open(self.pdf_path, 'rb') as f:
                    pdf_file = File(f)
                    filename = f"complemento_{self.data_extraida['folio']}.pdf"
                    self.complemento.archivo_pdf.save(filename, pdf_file, save=True)
            
            return True
        
        except Exception as e:
            self.errores.append(f"Error al crear complemento: {str(e)}")
            return False
    
    def _crear_documentos_relacionados(self) -> bool:
        """Crea los DocumentoRelacionado vinculados al complemento."""
        try:
            for doc_data in self.data_extraida["documentos_relacionados"]:
                # Buscar factura
                factura = Factura.objects.filter(
                    uuid_factura=doc_data["uuid_factura"]
                ).first()
                
                if not factura:
                    factura = Factura.objects.filter(
                        folio_factura=doc_data["folio_factura"]
                    ).first()
                
                if not factura:
                    self.errores.append(
                        f"No se encontró factura {doc_data['folio_factura']}"
                    )
                    continue
                
                DocumentoRelacionado.objects.create(
                    complemento=self.complemento,
                    factura=factura,
                    uuid_factura_relacionada=doc_data["uuid_factura"],
                    num_parcialidad=doc_data.get("num_parcialidad", 1),
                    saldo_anterior=doc_data["saldo_anterior"] or Decimal("0.00"),
                    importe_pagado=doc_data["importe_pagado"] or Decimal("0.00"),
                    saldo_insoluto=doc_data["saldo_insoluto"] or Decimal("0.00"),
                    iva_desglosado=doc_data.get("iva"),
                    ieps_desglosado=doc_data.get("ieps")
                )
            
            return True
        
        except Exception as e:
            self.errores.append(f"Error al crear documentos relacionados: {str(e)}")
            return False
    
    def _resultado_error(self, mensaje_principal: str) -> dict:
        """Construye dict de resultado con error."""
        return {
            "success": False,
            "complemento": None,
            "vinculacion": None,
            "errores": [mensaje_principal] + self.errores,
            "warnings": self.warnings
        }


def procesar_complemento_pdf(pdf_path: str, guardar_archivo: bool = True) -> dict:
    """
    Función de conveniencia para procesar un complemento de pago desde PDF.
    
    Args:
        pdf_path: Ruta al archivo PDF del complemento
        guardar_archivo: Si True, guarda el PDF en el modelo
        
    Returns:
        dict con resultado del procesamiento
    
    Example:
        resultado = procesar_complemento_pdf("complemento_1047.pdf")
        if resultado["success"]:
            print(f"Complemento {resultado['complemento'].folio_complemento} creado")
            print(f"Vinculados: {resultado['vinculacion']['vinculados']}")
        else:
            print("Errores:", resultado['errores'])
    """
    procesador = ProcesadorComplemento(pdf_path, guardar_archivo)
    return procesador.procesar()
