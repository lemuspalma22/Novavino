import fitz  # PyMuPDF
import re

def extract_text_from_pdf(pdf_path):
    """Extrae el texto completo del PDF."""
    with fitz.open(pdf_path) as doc:
        return "\n".join([page.get_text("text") for page in doc])


def extract_invoice_data(pdf_path):
    """Extrae datos clave de una factura en PDF."""
    text = extract_text_from_pdf(pdf_path)

    # Expresiones regulares para extraer datos clave
    factura = re.search(r"Factura (\d+)", text)
    uuid = re.search(r"FOLIO FISCAL \(UUID\)\s+([A-F0-9\-]+)", text)
    fecha_emision = re.search(r"FECHA Y HORA DE EMISIÓN DE CFDI\s+([\d\-T:]+)", text)
    cliente = re.search(r"CLIENTE\s+([A-Z\s]+)\n([A-Z0-9]+)", text)
    subtotal = re.search(r"SUBTOTAL\s+\$ ([\d,]+\.\d+)", text)
    total = re.search(r"TOTAL\s+\$ ([\d,]+\.\d+)", text)
    
    data = {
        "factura": factura.group(1) if factura else None,
        "uuid": uuid.group(1) if uuid else None,
        "fecha_emision": fecha_emision.group(1) if fecha_emision else None,
        "cliente": cliente.group(1) if cliente else None,
        "rfc_cliente": cliente.group(2) if cliente else None,
        "subtotal": subtotal.group(1) if subtotal else None,
        "total": total.group(1) if total else None,
    }

    return data


def extract_product_list(text):
    """
    Extrae productos desde el bloque entre 'CONCEPTOS' y 'IMPORTE CON LETRA'.
    Detecta líneas con cantidad, unidad, y nombre del producto real.
    """
    productos = []

    # Cortar solo el bloque de productos
    if "CONCEPTOS" in text and "IMPORTE CON LETRA" in text:
        texto_conceptos = text.split("CONCEPTOS")[1].split("IMPORTE CON LETRA")[0]
    else:
        texto_conceptos = text  # fallback si no están los marcadores

    lines = texto_conceptos.strip().split("\n")

    for i in range(len(lines) - 2):
        linea_cantidad = lines[i].strip()
        linea_unidad = lines[i + 1].strip()
        linea_descripcion = lines[i + 2].strip()

        if re.match(r"^\d+(\.\d+)?$", linea_cantidad):
            try:
                cantidad = float(linea_cantidad)
                if linea_descripcion and not any(x in linea_descripcion.lower() for x in ["clave", "impuesto", "traslado", "serv", "objeto"]):
                    productos.append({
                        "cantidad": cantidad,
                        "nombre_detectado": linea_descripcion
                    })
            except ValueError:
                continue

    return productos


