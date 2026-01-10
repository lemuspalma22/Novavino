import re

def es_producto_valido(nombre: str) -> bool:
    nombre = nombre.strip()
    if not nombre:
        return False

    if re.fullmatch(r"^[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?$|^\d+(\.\d+)?$", nombre):
        return False

    patrones_prohibidos = [
        r"^IEPS", r"^IVA", r"^pz$", r"^CP:", r"^\d{5}$", r"Comprobante", r"Pago", r"Emisión",
        r"^Fecha", r"^NOMBRE:", r"^RFC", r"^Uso CFDI", r"^Subtotal", r"^Total", r"^Importe",
        r"[A-Z]{5,}[0-9]{2,}"
    ]

    for patron in patrones_prohibidos:
        if re.search(patron, nombre, re.IGNORECASE):
            return False

    return True
