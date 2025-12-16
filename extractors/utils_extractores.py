import re
from datetime import datetime


def extraer_folio(texto):
    lines = texto.splitlines()
    for i, line in enumerate(lines):
        if re.search(r"Folio\s*:", line, re.IGNORECASE):
            # print(f"\n[DEBUG] Linea con 'Folio:': {repr(line)}")
            for offset in range(1, 4):
                if i - offset >= 0:
                    anterior = lines[i - offset].strip()
                    # print(f"[DEBUG] Linea anterior ({offset}): {repr(anterior)}")
                    cleaned = re.sub(r"[^\d]", "", anterior)
                    # print(f"[DEBUG] Limpiado: {repr(cleaned)}")
                    if cleaned.isdigit():
                        # print(f"[OK] Detectado como folio: {cleaned}")
                        return cleaned
            raise ValueError("Se encontro 'Folio:' pero no habia numero valido en las lineas anteriores.")
    raise ValueError("No se encontro 'Folio:' en el texto OCR.")



def extraer_uuid(texto):
    """
    Busca el primer UUID con el formato estándar (36 caracteres) en el texto.
    """
    match = re.search(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", texto)
    if not match:
        raise ValueError("No se encontro un UUID valido en el texto OCR.")
    return match.group(0)


def extraer_fecha_emision(texto):
    """
    Busca una fecha con formato ISO 8601, como 2025-01-15T09:28:22
    """
    match = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", texto)
    if not match:
        raise ValueError("No se encontro la fecha de emision en el texto OCR.")
    return datetime.fromisoformat(match.group(1))


def extraer_total(texto: str) -> float:
    """
    Extrae el TOTAL de una factura desde el texto OCR.
    
    Lógica:
    - Caso 1: Buscar línea que diga exactamente 'Total' y tomar el monto mayor en las siguientes líneas.
    - Caso 2: Buscar línea que diga 'Total:' en formato clave-valor (Total: $X,XXX.XX).
    - Caso 3: Fallback por 'Bueno por: $X,XXX.XX' para facturas tipo pagaré.
    """
    lines = texto.splitlines()

    # Caso 1: Línea que diga solo "Total" y revisar siguientes líneas
    for i, line in enumerate(lines):
        if re.fullmatch(r"\bTotal\b", line.strip(), re.IGNORECASE):
            max_total = None
            for j in range(1, 10):  # buscar hasta 10 líneas después
                if i + j < len(lines):
                    candidate = lines[i + j].strip()
                    matches = re.findall(r"\$?\s*([\d,]+\.\d{2})", candidate)
                    for match in matches:
                        value = float(match.replace(",", ""))
                        if max_total is None or value > max_total:
                            max_total = value
            if max_total is not None:
                return max_total

    # Caso 2: Total en la misma línea tipo "Total: $1234.56"

def extraer_total(texto: str) -> float:
    """
    Extrae el TOTAL (no el subtotal) de una factura.
    - Busca todas las ocurrencias válidas de la palabra TOTAL (excluyendo SUBTOTAL).
    - Explora hasta 8 líneas posteriores por cada ocurrencia.
    - Devuelve el monto más alto entre todos los candidatos encontrados.
    """
    lines = texto.splitlines()
    total_candidates = []

    # Paso 1: Buscar todas las líneas con "TOTAL" pero no "SUBTOTAL"
    for i, line in enumerate(lines):
        if re.search(r"\bTOTAL\b", line, re.IGNORECASE) and not re.search(r"SUBTOTAL", line, re.IGNORECASE):
            for j in range(1, 9):
                if i + j < len(lines):
                    candidate = lines[i + j].strip()
                    match = re.search(r"\$?\s*([\d,]+\.\d{2})", candidate)
                    if match:
                        value = float(match.group(1).replace(",", ""))
                        total_candidates.append(value)

    if total_candidates:
        return max(total_candidates)

    # Paso 2: Fallback directo
    match = re.search(r"(?<!SUB)TOTAL\s*:\s*\$?\s*([\d,]+\.\d{2})", texto, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))

    # Paso 3: Fallback por "IMPORTE EN LETRA"
    match = re.search(r"IMPORTE EN LETRA.*?\n.*?\n.*?([\d,]+\.\d{2})", texto, re.IGNORECASE | re.DOTALL)
    if match:
        return float(match.group(1).replace(",", ""))

    # Paso 4: Fallback total — mayor número del texto
    all_matches = re.findall(r"\$?\s*([\d,]+\.\d{2})", texto)
    if all_matches:
        values = [float(x.replace(",", "")) for x in all_matches]
        return max(values)

    raise ValueError("No se encontro el total en el texto OCR.")




