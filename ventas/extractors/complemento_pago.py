# ventas/extractors/complemento_pago.py
import re
from decimal import Decimal, InvalidOperation
from compras.extractors.pdf_reader import extract_text_from_pdf


def _to_decimal(s: str) -> Decimal | None:
    """Convierte string a Decimal, manejando formato con comas."""
    try:
        return Decimal(s.replace(",", "").replace("$", "").strip())
    except (InvalidOperation, AttributeError, ValueError):
        return None


def extraer_complemento_pago(texto: str) -> dict:
    """
    Extrae información de un Complemento de Pago (CFDI).
    
    Args:
        texto: Texto extraído del PDF del complemento
        
    Returns:
        dict con estructura:
        {
            "folio": "1047",
            "uuid": "41EC4C96-...",
            "fecha_emision": "2025-11-06",
            "fecha_pago": "2025-11-05",
            "monto": Decimal("2358.00"),
            "forma_pago": "03",
            "cliente": "BAHIA DE CHELEM",
            "rfc_cliente": "BCE231018IC7",
            "documentos_relacionados": [
                {
                    "uuid_factura": "1D625F45-...",
                    "folio_factura": "1032",
                    "num_parcialidad": 1,
                    "saldo_anterior": Decimal("2358.00"),
                    "importe_pagado": Decimal("2358.00"),
                    "saldo_insoluto": Decimal("0.00"),
                    "iva": Decimal("325.24"),
                    "ieps": Decimal("425.83")
                }
            ]
        }
    """
    data = {
        "folio": None,
        "uuid": None,
        "fecha_emision": None,
        "fecha_pago": None,
        "monto": None,
        "forma_pago": None,
        "cliente": None,
        "rfc_cliente": None,
        "documentos_relacionados": []
    }
    
    lines = [ln.strip() for ln in texto.splitlines()]
    
    # === UUID del complemento ===
    m_uuid = re.search(
        r"FOLIO FISCAL.*?\n.*?([A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12})",
        texto,
        re.IGNORECASE | re.DOTALL
    )
    if m_uuid:
        data["uuid"] = m_uuid.group(1)
    
    # === Folio del complemento ===
    m_folio = re.search(r"Complemento de Pagos?\s+(\d+)", texto, re.IGNORECASE)
    if m_folio:
        data["folio"] = m_folio.group(1)
    
    # === Fecha de emisión ===
    m_emision = re.search(
        r"FECHA Y HORA DE EMISI[OÓ]N DE CFDI[:\s]+(\d{4}-\d{2}-\d{2})",
        texto,
        re.IGNORECASE
    )
    if m_emision:
        data["fecha_emision"] = m_emision.group(1)
    
    # === Cliente ===
    for i, ln in enumerate(lines):
        if ln == "CLIENTE":
            if i + 1 < len(lines):
                data["cliente"] = lines[i + 1].strip()
            if i + 2 < len(lines):
                # RFC suele estar en la siguiente línea
                rfc_candidate = lines[i + 2].strip()
                if re.match(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$", rfc_candidate):
                    data["rfc_cliente"] = rfc_candidate
            break
    
    # === Sección PAGO 1 ===
    # Fecha de pago
    m_fecha_pago = re.search(
        r"Fecha de Pago[:\s]+(\d{4}-\d{2}-\d{2})",
        texto,
        re.IGNORECASE
    )
    if m_fecha_pago:
        data["fecha_pago"] = m_fecha_pago.group(1)
    
    # Forma de pago
    m_forma = re.search(
        r"Forma de Pago[:\s]+(\d{2})\s*-",
        texto,
        re.IGNORECASE
    )
    if m_forma:
        data["forma_pago"] = m_forma.group(1)
    
    # Monto del pago
    m_monto = re.search(
        r"Monto[:\s]+\$\s*([0-9,]+\.\d{2})",
        texto,
        re.IGNORECASE
    )
    if m_monto:
        data["monto"] = _to_decimal(m_monto.group(1))
    
    # === DOCUMENTO RELACIONADO ===
    # Buscar sección de documentos relacionados
    doc_section_start = None
    for i, ln in enumerate(lines):
        if "DOCUMENTO RELACIONADO" in ln:
            doc_section_start = i
            break
    
    if doc_section_start is not None:
        doc_data = {
            "uuid_factura": None,
            "folio_factura": None,
            "num_parcialidad": 1,
            "saldo_anterior": None,
            "importe_pagado": None,
            "saldo_insoluto": None,
            "iva": None,
            "ieps": None
        }
        
        # Buscar en las siguientes ~30 líneas
        search_end = min(doc_section_start + 30, len(lines))
        section = "\n".join(lines[doc_section_start:search_end])
        
        # UUID del documento (factura)
        m_uuid_doc = re.search(
            r"Id Documento[:\s]+([A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12})",
            section,
            re.IGNORECASE
        )
        if m_uuid_doc:
            doc_data["uuid_factura"] = m_uuid_doc.group(1)
        
        # Folio de la factura
        m_folio_doc = re.search(r"Folio[:\s]+(\d+)", section, re.IGNORECASE)
        if m_folio_doc:
            doc_data["folio_factura"] = m_folio_doc.group(1)
        
        # Número de parcialidad
        m_parcialidad = re.search(r"Num\.\s*Parcialidad[:\s]+(\d+)", section, re.IGNORECASE)
        if m_parcialidad:
            doc_data["num_parcialidad"] = int(m_parcialidad.group(1))
        
        # Saldo anterior
        m_saldo_ant = re.search(
            r"Imp\.\s*Saldo\s*Ant\.[:\s]+\$\s*([0-9,]+\.\d{2})",
            section,
            re.IGNORECASE
        )
        if m_saldo_ant:
            doc_data["saldo_anterior"] = _to_decimal(m_saldo_ant.group(1))
        
        # Importe pagado
        m_imp_pag = re.search(
            r"Imp\.\s*Pagado[:\s]+\$\s*([0-9,]+\.\d{2})",
            section,
            re.IGNORECASE
        )
        if m_imp_pag:
            doc_data["importe_pagado"] = _to_decimal(m_imp_pag.group(1))
        
        # Saldo insoluto
        m_saldo_ins = re.search(
            r"Imp\.\s*Saldo\s*Insoluto[:\s]+\$\s*([0-9,]+\.\d{2})",
            section,
            re.IGNORECASE
        )
        if m_saldo_ins:
            doc_data["saldo_insoluto"] = _to_decimal(m_saldo_ins.group(1))
        
        # === Impuestos ===
        # IVA
        m_iva = re.search(
            r"002\s*-\s*IVA.*?Importe\s*DR[:\s]+\$\s*([0-9,]+\.\d{2})",
            section,
            re.IGNORECASE | re.DOTALL
        )
        if m_iva:
            doc_data["iva"] = _to_decimal(m_iva.group(1))
        
        # IEPS
        m_ieps = re.search(
            r"003\s*-\s*IEPS.*?Importe\s*DR[:\s]+\$\s*([0-9,]+\.\d{2})",
            section,
            re.IGNORECASE | re.DOTALL
        )
        if m_ieps:
            doc_data["ieps"] = _to_decimal(m_ieps.group(1))
        
        # Solo agregar si encontramos al menos el UUID y folio
        if doc_data["uuid_factura"] and doc_data["folio_factura"]:
            data["documentos_relacionados"].append(doc_data)
    
    return data


def extract_complemento_from_pdf(pdf_path: str) -> dict:
    """
    Extrae datos de complemento de pago desde archivo PDF.
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        dict con datos extraídos
    """
    texto = extract_text_from_pdf(pdf_path)
    return extraer_complemento_pago(texto)
