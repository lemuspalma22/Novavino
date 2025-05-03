import re
from decimal import Decimal
from extractors.utils_extractores import extraer_total, extraer_fecha_emision

def extraer_factura_novavino(texto: str) -> dict:
    import re
    from decimal import Decimal

    data = {
        "folio": None,
        "uuid": None,
        "fecha_emision": None,
        "cliente": None,
        "total": None,
        "productos": []
    }

    lines = texto.splitlines()

    # UUID
    uuid_match = re.search(r"[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}", texto)
    if uuid_match:
        data["uuid"] = uuid_match.group(0)

    # Folio
    folio_match = re.search(r"Factura\s+(\d+)", texto)
    if folio_match:
        data["folio"] = folio_match.group(1)

    # Fecha
    for line in lines:
        if "FECHA Y HORA DE EMISIÓN DE CFDI" in line:
            fecha_line_index = lines.index(line)
            fecha_val = lines[fecha_line_index + 1].strip()
            data["fecha_emision"] = fecha_val
            break

    # Cliente
    for i, line in enumerate(lines):
        if "CLIENTE" in line:
            data["cliente"] = lines[i + 1].strip()
            break

    # Total
    from extractors.utils_extractores import extraer_total
    data["total"] = extraer_total(texto)

    # Productos (nueva lógica: detectar patrón y agrupar por bloques)
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # buscar cantidad
        if re.match(r"^\d+\.\d{2}$", line):
            cantidad = Decimal(line)
            descripcion = lines[i + 2].strip() if i + 2 < len(lines) else ""
            nombre = descripcion
            # buscar precio unitario en línea siguiente
            j = i
            while j < len(lines):
                if "$" in lines[j]:
                    precio_match = re.search(r"\$\s*([\d,]+\.\d{2})", lines[j])
                    if precio_match:
                        precio = Decimal(precio_match.group(1).replace(",", ""))
                        data["productos"].append({
                            "nombre": nombre,
                            "cantidad": cantidad,
                            "precio_unitario": precio
                        })
                        i = j  # avanza hasta el final del bloque
                        break
                j += 1
        i += 1

    return data

